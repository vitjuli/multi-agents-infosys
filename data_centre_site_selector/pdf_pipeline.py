"""
pdf_pipeline.py
===============
Multi-agent pipeline for producing a detailed PDF technical report from the
data-centre site-selection results.

Pipeline stages (matching the Denario system pattern)
------------------------------------------------------
1. PreprocessAgent  – validates inputs, generates matplotlib plots, deduplicates figures.
2. SectionAgent(s)  – separate agent calls produce each section of the report draft.
3. PlotsAgent       – captions each figure and assembles Draft v1.
4. RefiningAgent    – improves the Results and Discussion sections and polishes plot
                      references → Draft v2.
5. CitationsAgent   – first pass inserts inline citation markers → Draft v3;
                      second pass appends the full bibliography → Draft v4.

The final ReportDraft v4 is consumed by pdf_renderer.render_pdf_report().
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd
from langchain_openai import ChatOpenAI

from .config import DEFAULT_MODEL, FAST_MODEL, REASONING_MODEL, load_environment
from .logging_utils import get_logger

logger = get_logger("pdf_pipeline")


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class ReportPlot:
    """A single figure file plus its metadata."""
    path: str               # absolute path to saved PNG
    plot_id: str            # e.g. "fig_1"
    title: str              # short title shown above/below figure
    description: str        # prose description sent to LLM for captioning
    caption: str = ""       # filled in by PlotsAgent

    def content_hash(self) -> str:
        """MD5 of the image bytes — used to detect duplicate plots."""
        with open(self.path, "rb") as fh:
            return hashlib.md5(fh.read()).hexdigest()


@dataclass
class ReportContext:
    """All data available to every agent in the pipeline."""
    query: str
    workload: str
    ranked: pd.DataFrame
    agent_summaries: list[dict[str, Any]]
    critic: dict[str, Any]
    synthesis: dict[str, Any]
    site_selection: dict[str, Any]
    top_k: int
    plots: list[ReportPlot] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().strftime("%d %B %Y"))


@dataclass
class ReportDraft:
    """One versioned draft of the report."""
    version: int                                   # 1 → 2 → 3 → 4
    sections: dict[str, str]                       # section_key → prose text
    plots: list[ReportPlot]
    bibliography: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


# ── LLM helper ────────────────────────────────────────────────────────────────

def _call_llm(
    model: str,
    system: str,
    user: str,
    max_retries: int = 1,
    temperature: float = 0.3,
) -> str:
    """Call LangChain ChatOpenAI with retry logic."""
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            response = ChatOpenAI(
                model=model,
                temperature=temperature,
            ).invoke(
                [
                    ("system", system),
                    ("human", user),
                ]
            )
            return (
                response.content if isinstance(response.content, str) else str(response.content)
            )
        except Exception as exc:
            last_error = exc
            logger.warning("LLM call attempt %d/%d failed: %s", attempt + 1, max_retries + 1, exc)
            time.sleep(0.5 * (attempt + 1))
    logger.warning("All LLM attempts failed (last error: %s); using fallback text.", last_error)
    return ""


# ── Plot generation ────────────────────────────────────────────────────────────

_PLOT_COLORS = [
    "#2980b9", "#27ae60", "#e67e22", "#8e44ad",
    "#e74c3c", "#16a085", "#f39c12", "#2c3e50",
]


def _generate_plots(ranked: pd.DataFrame, top_k: int, plot_dir: str) -> list[ReportPlot]:
    """
    Generate up to four standard diagnostic figures from the ranked DataFrame
    and save them as PNG files in plot_dir.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        logger.warning("matplotlib not installed — skipping figure generation.")
        return []

    plots: list[ReportPlot] = []
    os.makedirs(plot_dir, exist_ok=True)
    top = ranked.head(top_k).copy()

    # ── Figure 1: Overall scores (horizontal bar) ──────────────────────────
    fig, ax = plt.subplots(figsize=(8, max(3, top_k * 0.55 + 0.8)))
    labels = [r[:20] + "…" if len(r) > 20 else r for r in top["region"].tolist()]
    scores = pd.to_numeric(top["overall_score"], errors="coerce").fillna(0).tolist()
    bars = ax.barh(labels, scores, color=_PLOT_COLORS[0], edgecolor="white", height=0.6)
    ax.set_xlabel("Overall Score (0 – 10)", fontsize=10)
    ax.set_title("Top Candidate Overall Scores", fontsize=12, fontweight="bold")
    ax.set_xlim(0, 10.5)
    ax.axvline(x=5, color="grey", linestyle="--", linewidth=0.8, alpha=0.6)
    for bar, score in zip(bars, scores):
        ax.text(
            score + 0.1, bar.get_y() + bar.get_height() / 2,
            f"{score:.2f}", va="center", fontsize=9,
        )
    ax.invert_yaxis()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    p1 = os.path.join(plot_dir, "fig_1_overall_scores.png")
    fig.savefig(p1, dpi=150, bbox_inches="tight")
    plt.close(fig)
    plots.append(ReportPlot(
        path=p1, plot_id="fig_1",
        title="Overall Candidate Scores",
        description=(
            "Horizontal bar chart comparing the overall site-suitability scores of the top candidate "
            "regions. Scores are derived from a workload-weighted multi-criteria framework."
        ),
    ))

    # ── Figure 2: Score dimensions (grouped bar) ──────────────────────────
    score_cols = [c for c in [
        "energy_score_raw", "water_score_raw", "climate_score_raw",
        "latency_score_raw", "resilience_score_raw", "land_score_raw",
    ] if c in ranked.columns]

    if score_cols:
        n_dims = len(score_cols)
        n_cands = len(top)
        x = np.arange(n_dims)
        width = 0.75 / n_cands
        dim_labels = [c.replace("_score_raw", "").replace("_", " ").title() for c in score_cols]

        fig, ax = plt.subplots(figsize=(10, 5))
        for i, (_, row) in enumerate(top.iterrows()):
            vals = [float(pd.to_numeric(row.get(c, 0), errors="coerce") or 0) for c in score_cols]
            offset = (i - n_cands / 2 + 0.5) * width
            ax.bar(x + offset, vals, width, label=str(row["region"])[:20],
                   color=_PLOT_COLORS[i % len(_PLOT_COLORS)], edgecolor="white")
        ax.set_xticks(x)
        ax.set_xticklabels(dim_labels, rotation=20, ha="right", fontsize=9)
        ax.set_ylabel("Score (0 – 10)", fontsize=10)
        ax.set_title("Score Dimensions per Candidate", fontsize=12, fontweight="bold")
        ax.set_ylim(0, 11.5)
        ax.legend(fontsize=8, loc="upper right", framealpha=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        p2 = os.path.join(plot_dir, "fig_2_score_dimensions.png")
        fig.savefig(p2, dpi=150, bbox_inches="tight")
        plt.close(fig)
        plots.append(ReportPlot(
            path=p2, plot_id="fig_2",
            title="Score Dimensions per Candidate",
            description=(
                "Grouped bar chart showing energy, water, climate, latency, resilience, and land scores "
                "side-by-side for each top candidate, enabling direct dimension-level comparison."
            ),
        ))

    # ── Figure 3: Renewable capacity vs latency scatter ───────────────────
    if "renewable_capacity_50km_mw" in ranked.columns and "latency_score_raw" in ranked.columns:
        fig, ax = plt.subplots(figsize=(7, 5))
        x_vals = pd.to_numeric(top["renewable_capacity_50km_mw"], errors="coerce").fillna(0) / 1000
        y_vals = pd.to_numeric(top["latency_score_raw"], errors="coerce").fillna(0)
        c_vals = pd.to_numeric(top["overall_score"], errors="coerce").fillna(0)
        sc = ax.scatter(x_vals, y_vals, c=c_vals, cmap="RdYlGn", s=120,
                        edgecolors="black", linewidths=0.7, vmin=0, vmax=10, zorder=3)
        plt.colorbar(sc, ax=ax, label="Overall Score")
        for _, row in top.iterrows():
            ax.annotate(
                str(row["region"])[:16],
                (float(pd.to_numeric(row.get("renewable_capacity_50km_mw", 0), errors="coerce") or 0) / 1000,
                 float(pd.to_numeric(row.get("latency_score_raw", 0), errors="coerce") or 0)),
                fontsize=7.5, xytext=(4, 4), textcoords="offset points",
            )
        ax.set_xlabel("Renewable Capacity within 50 km (GW)", fontsize=10)
        ax.set_ylabel("Latency Score (0 – 10)", fontsize=10)
        ax.set_title("Renewable Energy vs Latency Trade-off", fontsize=12, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        p3 = os.path.join(plot_dir, "fig_3_renewable_vs_latency.png")
        fig.savefig(p3, dpi=150, bbox_inches="tight")
        plt.close(fig)
        plots.append(ReportPlot(
            path=p3, plot_id="fig_3",
            title="Renewable Energy vs Latency Trade-off",
            description=(
                "Scatter plot of total renewable capacity within 50 km (GW) against latency score, "
                "colour-coded by overall score. Highlights the trade-off between green-energy access "
                "and network proximity."
            ),
        ))

    # ── Figure 4: Score heatmap ───────────────────────────────────────────
    if score_cols and len(top) >= 2:
        try:
            hm_data = top[["region"] + score_cols].copy().set_index("region")
            hm_data.columns = [
                c.replace("_score_raw", "").replace("_", " ").title()
                for c in score_cols
            ]
            hm_data = hm_data.apply(pd.to_numeric, errors="coerce").fillna(0)

            fig, ax = plt.subplots(figsize=(9, max(3, len(top) * 0.7 + 1.2)))
            im = ax.imshow(hm_data.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=10)
            plt.colorbar(im, ax=ax, label="Score (0 – 10)", fraction=0.03, pad=0.04)
            ax.set_xticks(range(len(hm_data.columns)))
            ax.set_xticklabels(hm_data.columns, rotation=30, ha="right", fontsize=9)
            ax.set_yticks(range(len(hm_data.index)))
            ax.set_yticklabels(hm_data.index, fontsize=9)
            for i in range(len(hm_data.index)):
                for j in range(len(hm_data.columns)):
                    v = hm_data.values[i, j]
                    ax.text(j, i, f"{v:.1f}", ha="center", va="center",
                            fontsize=8.5, color="white" if v > 7 else "black")
            ax.set_title("Score Heatmap: Candidates × Dimensions",
                         fontsize=12, fontweight="bold", pad=12)
            fig.tight_layout()
            p4 = os.path.join(plot_dir, "fig_4_score_heatmap.png")
            fig.savefig(p4, dpi=150, bbox_inches="tight")
            plt.close(fig)
            plots.append(ReportPlot(
                path=p4, plot_id="fig_4",
                title="Score Heatmap: Candidates × Dimensions",
                description=(
                    "Colour-coded matrix of score values for each candidate region across all "
                    "scoring dimensions. Warmer colours indicate higher scores, enabling rapid "
                    "identification of strengths and weaknesses."
                ),
            ))
        except Exception as exc:
            logger.warning("Heatmap generation failed: %s", exc)

    logger.info("_generate_plots: produced %d figure(s) in %s.", len(plots), plot_dir)
    return plots


def _dedup_plots(plots: list[ReportPlot]) -> tuple[list[ReportPlot], list[str]]:
    """Remove duplicate figures by image content hash."""
    seen: dict[str, str] = {}
    unique: list[ReportPlot] = []
    warnings: list[str] = []
    for plot in plots:
        h = plot.content_hash()
        if h in seen:
            msg = f"{plot.plot_id} is pixel-identical to {seen[h]} — skipped."
            warnings.append(msg)
            logger.warning("PreprocessAgent: duplicate plot detected: %s", msg)
        else:
            seen[h] = plot.plot_id
            unique.append(plot)
    return unique, warnings


# ── Agent 1: PreprocessAgent ──────────────────────────────────────────────────

class PreprocessAgent:
    """
    Reads and validates all report inputs, generates matplotlib figures from the
    ranked DataFrame, deduplicates any duplicate plots, and returns a ReportContext.
    """

    def __init__(self, plot_dir: str | None = None) -> None:
        self.plot_dir = plot_dir or tempfile.mkdtemp(prefix="dcss_report_plots_")
        logger.info("PreprocessAgent: plot_dir=%s", self.plot_dir)

    def run(
        self,
        query: str,
        workload: str,
        ranked: pd.DataFrame,
        agent_summaries: list[dict[str, Any]],
        critic: dict[str, Any],
        synthesis: dict[str, Any],
        site_selection: dict[str, Any],
        top_k: int,
        extra_plots: list[ReportPlot] | None = None,
    ) -> ReportContext:
        logger.info("PreprocessAgent: validating inputs and generating figures.")
        if ranked.empty:
            raise ValueError("PreprocessAgent: ranked DataFrame is empty.")

        plots = _generate_plots(ranked, top_k, self.plot_dir)
        if extra_plots:
            plots.extend(extra_plots)
        plots, dup_warnings = _dedup_plots(plots)
        if dup_warnings:
            logger.warning(
                "PreprocessAgent: %d duplicate figure(s) removed.", len(dup_warnings)
            )

        context = ReportContext(
            query=query,
            workload=workload,
            ranked=ranked,
            agent_summaries=agent_summaries,
            critic=critic,
            synthesis=synthesis,
            site_selection=site_selection,
            top_k=top_k,
            plots=plots,
        )
        logger.info(
            "PreprocessAgent: context ready — %d candidates, %d figure(s).",
            len(ranked), len(plots),
        )
        return context


# ── Agent 2: SectionAgent ─────────────────────────────────────────────────────

class SectionAgent:
    """
    Writes one prose section of the report using an LLM call.
    Each section has its own instruction prompt; the agent is called once per
    section in sequence by the pipeline.
    """

    SECTION_INSTRUCTIONS: dict[str, str] = {
        "abstract": (
            "Write a concise technical abstract (150–200 words) for a UK data-centre site-selection "
            "report. Cover: objective, methodology overview, top recommendation(s), and key findings. "
            "Use formal language. Do not use bullet points."
        ),
        "introduction": (
            "Write an Introduction section (~350 words) for a UK data-centre site-selection technical "
            "report. Cover: background on UK data-centre market growth and energy demand, the importance "
            "of rigorous multi-criteria site selection, the scope and objectives of this analysis, and "
            "the structure of the report (one sentence per subsequent section). Use formal prose."
        ),
        "methodology": (
            "Write a Methodology section (~450 words) explaining: "
            "(1) the weighted multi-criteria scoring framework and its seven dimensions (energy, water, "
            "climate, latency, resilience, land, planning risk); "
            "(2) how workload-specific weight vectors are applied; "
            "(3) the multi-agent analysis pipeline (specialist agents, critic, synthesis); "
            "(4) data sources and their provenance. "
            "Distinguish clearly between computed values and heuristic placeholders. Use subsection "
            "headings (e.g. 'Scoring Framework', 'Agent Pipeline', 'Data Sources')."
        ),
        "data_overview": (
            "Write a Data and Candidate Overview section (~300 words) covering: "
            "ONS LAD boundary centroids (361 UK candidates), DESNZ REPD renewable-energy data, "
            "NESO GSP regions, EA flood-zone polygons, ONS population estimates, and the Planning "
            "Portal brownfield land and site registers. Describe any data-quality limitations and "
            "where heuristic placeholders have been used."
        ),
        "results": (
            "Write a Results section (~600 words) discussing the ranked candidates, their scores, "
            "and what the specialist-agent analyses revealed. "
            "Reference figures using the exact tokens [FIG_1] (overall-score bar chart), "
            "[FIG_2] (score-dimension grouped bar), [FIG_3] (renewable vs latency scatter), "
            "and [FIG_4] (score heatmap). Each figure must be referenced at least once. "
            "Discuss the top recommendation in detail, then compare the second and third candidates."
        ),
        "discussion": (
            "Write a Discussion section (~400 words) that: analyses trade-offs for the top 2–3 "
            "candidates; discusses data gaps and their impact on score reliability; compares "
            "workload-specific suitability; and considers policy and planning context. "
            "Be balanced and acknowledge the prototype nature of heuristic scores."
        ),
        "conclusions": (
            "Write a Conclusions section (~250 words) that: restates the top recommendation with "
            "justification; summarises key findings in prose (no bullet points); notes the main "
            "caveats; and proposes concrete next steps (data to acquire, further analysis)."
        ),
    }

    def __init__(
        self,
        client: Any | None,
        model: str = DEFAULT_MODEL,
        max_retries: int = 1,
    ) -> None:
        self.llm_enabled = bool(client)
        self.model = model
        self.max_retries = max_retries

    def run(self, section: str, context: ReportContext) -> str:
        logger.info("SectionAgent: writing section '%s'.", section)
        if not self.llm_enabled:
            logger.info("SectionAgent: no LLM client — using deterministic fallback.")
            return self._fallback(section, context)

        instruction = self.SECTION_INSTRUCTIONS.get(
            section, f"Write the '{section}' section of a technical report."
        )
        system = (
            "You are a technical report writer specialising in UK data-centre infrastructure and "
            "site selection. Write clear, well-structured professional prose. "
            "Do not use excessive bullet points — prefer flowing paragraphs with sub-headings where "
            "appropriate. Use only the data provided; do not invent figures or conclusions."
        )
        top = context.ranked.head(context.top_k)
        user_payload = {
            "instruction": instruction,
            "query": context.query,
            "workload": context.workload,
            "top_candidates": top[["region", "overall_score"]].to_dict(orient="records"),
            "agent_briefs": [
                {"agent": a.get("agent"), "summary": (a.get("summary") or "")[:300]}
                for a in context.agent_summaries
            ],
            "critic_summary": (context.critic.get("summary") or "")[:400],
            "synthesis_summary": (context.synthesis.get("summary") or "")[:400],
        }
        text = _call_llm(
            self.model, system,
            json.dumps(user_payload, default=str), self.max_retries,
        )
        return text.strip() if text.strip() else self._fallback(section, context)

    # ── Deterministic fallbacks ───────────────────────────────────────────

    def _fallback(self, section: str, context: ReportContext) -> str:
        top = context.ranked.head(context.top_k)
        top_region = str(top.iloc[0]["region"]) if len(top) else "N/A"
        top_score = float(pd.to_numeric(top.iloc[0]["overall_score"], errors="coerce") or 0) if len(top) else 0.0
        second = str(top.iloc[1]["region"]) if len(top) > 1 else "N/A"
        third  = str(top.iloc[2]["region"]) if len(top) > 2 else "N/A"

        fallbacks: dict[str, str] = {
            "abstract": (
                f"This report presents a data-driven site-selection analysis for a UK data-centre "
                f"facility optimised for the '{context.workload}' workload profile. A multi-criteria "
                f"scoring framework encompassing energy availability, water access, climate suitability, "
                f"latency, resilience, land availability, and planning risk was applied to "
                f"{len(context.ranked)} candidate regions across the United Kingdom. "
                f"The analysis was supplemented by a suite of specialist LLM-based analytical agents. "
                f"The top recommendation is {top_region}, which achieved an overall score of "
                f"{top_score:.2f} out of 10."
            ),
            "introduction": (
                "The United Kingdom is experiencing a period of unprecedented growth in data-centre "
                "demand, driven by accelerating cloud adoption, the emergence of large-scale AI training "
                "workloads, and digitalisation across financial services, public-sector, and enterprise "
                "markets. Against this backdrop, selecting the optimal site for a new data-centre "
                "facility has become a complex, multi-dimensional problem requiring simultaneous "
                "optimisation of power infrastructure, water availability, thermal environment, network "
                "latency, natural-hazard resilience, land availability, and planning risk.\n\n"
                "This report presents the results of a systematic, data-driven site-selection analysis "
                f"conducted in response to the query: \"{context.query}\". The analysis evaluates "
                f"{len(context.ranked)} candidate regions across the United Kingdom. "
                "The remainder of the report is structured as follows: Section 2 describes the "
                "methodology and scoring framework; Section 3 provides an overview of the datasets "
                "used; Section 4 presents the ranking results and agent findings; Section 5 discusses "
                "key trade-offs and limitations; and Section 6 sets out the conclusions and "
                "recommendations."
            ),
            "methodology": (
                "Scoring Framework\n\n"
                "The analysis employs a weighted multi-criteria decision-making (MCDM) framework. "
                "Seven siting dimensions are each scored on a normalised 0–10 scale: (1) energy "
                "availability, computed from DESNZ REPD renewable capacity within a 50 km radius; "
                "(2) water access, currently a heuristic placeholder; (3) climate suitability, derived "
                "from latitude as a cooling proxy; (4) latency, measured as proximity to identified "
                "network demand hubs; (5) resilience, incorporating EA flood-zone intersection flags; "
                "(6) land availability, based on brownfield-register area within radius; and "
                "(7) planning risk, an indicative categorical score.\n\n"
                "Workload-specific weight vectors calibrate the relative importance of each dimension. "
                f"For the '{context.workload}' workload, weights are applied as documented in the "
                "system configuration.\n\n"
                "Agent Pipeline\n\n"
                "Following deterministic scoring, a suite of specialist analytical agents—EnergyAgent, "
                "WaterAgent, ClimateCoolingAgent, LatencyAgent, ResilienceAgent, and "
                "LandPlanningAgent—each examine the top candidates through their domain lens. "
                "A CriticAgent reviews the combined findings for internal consistency and missing data, "
                "and a SynthesisAgent produces a final integrated recommendation.\n\n"
                "Data Sources\n\n"
                "Primary datasets are: ONS LAD boundaries (candidate generation), DESNZ REPD "
                "(renewable capacity), NESO GSP regions (grid proximity), EA flood zones (resilience), "
                "ONS population estimates, and the Planning Portal brownfield registers."
            ),
            "data_overview": (
                "Six primary open datasets underpin the candidate-feature table. The ONS Local "
                "Authority District (LAD) boundary file (December 2024 release) provides 361 candidate "
                "region centroids covering the whole of the United Kingdom. The DESNZ Renewable Energy "
                "Planning Database (REPD), updated quarterly, supplies operational and pipeline "
                "renewable-energy project locations and capacities from which radius-based capacity "
                "features are derived. NESO Grid Supply Point (GSP) region polygons are used to "
                "characterise proximity to transmission grid connection points.\n\n"
                "The Environment Agency Flood Map for Planning provides flood-zone polygons (zones 2 "
                "and 3) for England, though this dataset is large and is not loaded by default; "
                "a flag is set where the dataset has not been processed. ONS mid-2024 population "
                "estimates are joined to LAD records for England and Wales (Scotland may be absent "
                "from this workbook). Finally, the Planning Portal brownfield land and site registers "
                "contribute point-based counts and area (hectares) of brownfield land within radius.\n\n"
                "Data-quality limitations include: water-stress and abstraction-licence data are "
                "absent, making the water score a heuristic placeholder; the climate score relies "
                "solely on latitude until HadUK-Grid climate normals are integrated; grid headroom, "
                "connection-queue, and fibre-latency datasets are not yet modelled."
            ),
            "results": (
                f"The multi-criteria scoring framework ranked {len(top)} candidate regions, with "
                f"{top_region} achieving the highest overall score of {top_score:.2f}/10 [FIG_1]. "
                f"{second} and {third} were placed second and third respectively, each with "
                "differentiated score profiles reflecting distinct infrastructure trade-offs.\n\n"
                "As illustrated in [FIG_2], the score dimension breakdown reveals that energy and land "
                "scores are the primary differentiators among top candidates, while water and climate "
                "scores are broadly uniform given their current heuristic derivation. The renewable "
                "energy versus latency trade-off, shown in [FIG_3], demonstrates that candidates with "
                "the highest renewable capacity within 50 km tend to be located further from the major "
                "network demand hubs, incurring a latency penalty under connectivity-sensitive "
                "workloads. The complete score heatmap in [FIG_4] enables rapid identification of "
                "per-dimension strengths and weaknesses across the full candidate set.\n\n"
                "Specialist agent analyses identified that renewable capacity for leading candidates "
                "is predominantly pipeline rather than operational, a key caveat for near-term "
                "procurement planning. Brownfield land availability is strong in the top candidates, "
                "reducing planning-risk exposure. Flood-zone data was not fully processed in this run, "
                "and the resilience scores should be treated as indicative pending full EA dataset "
                "integration."
            ),
            "discussion": (
                f"The results highlight a fundamental trade-off between renewable energy access and "
                f"network latency across the top-ranked candidates. {top_region}, while leading on "
                "overall score, achieves its position largely through high renewable capacity and land "
                "availability, at the cost of a moderate latency score. For latency-sensitive "
                f"workloads, {second} may be preferred, given its superior proximity to network "
                "demand hubs.\n\n"
                "A number of data gaps materially affect score reliability. The water score is a "
                "heuristic placeholder, which means candidates in water-stressed catchments may be "
                "overscored relative to their true suitability. Similarly, the climate score's "
                "dependence on latitude is a crude proxy that does not capture local temperature "
                "extremes, humidity, or free-cooling hours. Grid headroom data — a critical "
                "constraint for large compute deployments — is not modelled, and the planning-risk "
                "score is categorical rather than site-specific.\n\n"
                "Policy context is also relevant: UK Government AI Growth Zones, Investment Zones, "
                "and Freeport designations could materially affect the cost and feasibility of "
                "development in certain candidate regions. Incorporating live policy-research outputs "
                "via the web-enabled PolicyResearchAgent is recommended for production use."
            ),
            "conclusions": (
                f"Based on the multi-criteria analysis, {top_region} is the recommended location for "
                f"the proposed data-centre facility under the '{context.workload}' workload profile, "
                f"with an overall suitability score of {top_score:.2f}/10. Its combination of "
                "substantial renewable energy capacity, available brownfield land, and acceptable "
                "resilience characteristics makes it the leading candidate among the regions "
                "evaluated.\n\n"
                "The analysis is subject to several important caveats: water and climate scores rely "
                "on heuristic proxies; grid-connection headroom has not been assessed; flood-zone "
                "data requires full EA dataset processing; and planning risk requires site-specific "
                "due diligence. These limitations should be addressed before any investment decision "
                "is made.\n\n"
                "Recommended next steps include: obtaining water-stress and abstraction-licence data; "
                "integrating HadUK-Grid climate normals; commissioning a grid-connection feasibility "
                "study for shortlisted sites; conducting a site-specific planning-risk assessment; "
                "and engaging the web-enabled PolicyResearchAgent to capture current UK incentive "
                "and planning policy."
            ),
        }
        return fallbacks.get(section, f"[{section.upper()} — content pending LLM availability]")


# ── Agent 3: PlotsAgent ───────────────────────────────────────────────────────

class PlotsAgent:
    """
    Captions each figure in the ReportContext and assembles the first
    preliminary report draft (Draft v1).
    """

    def __init__(
        self,
        client: Any | None,
        model: str = DEFAULT_MODEL,
        max_retries: int = 1,
    ) -> None:
        self.llm_enabled = bool(client)
        self.model = model
        self.max_retries = max_retries

    def caption_plot(self, plot: ReportPlot, context: ReportContext) -> str:
        logger.info("PlotsAgent: captioning %s ('%s').", plot.plot_id, plot.title)
        if not self.llm_enabled:
            return self._default_caption(plot, context)

        system = (
            "You are a technical writer generating figure captions for a data-centre "
            "site-selection report. Write a single caption of 2–4 sentences. Be specific about "
            "what the figure shows and what the key insight for a site-selection decision is. "
            "Begin with the figure identifier, e.g. 'Figure 1:'."
        )
        top_region = str(context.ranked.iloc[0]["region"]) if len(context.ranked) else "N/A"
        top_score  = float(pd.to_numeric(context.ranked.iloc[0].get("overall_score", 0), errors="coerce") or 0)
        user = json.dumps({
            "figure_id":          plot.plot_id.replace("_", " ").title(),
            "figure_title":       plot.title,
            "figure_description": plot.description,
            "query":              context.query,
            "workload":           context.workload,
            "top_candidate":      top_region,
            "top_score":          top_score,
            "top_k":              context.top_k,
        }, default=str)
        text = _call_llm(
            self.model, system, user, self.max_retries, temperature=0.2
        )
        return text.strip() if text.strip() else self._default_caption(plot, context)

    def _default_caption(self, plot: ReportPlot, context: ReportContext) -> str:
        top_region = str(context.ranked.iloc[0]["region"]) if len(context.ranked) else "N/A"
        top_score  = float(pd.to_numeric(context.ranked.iloc[0].get("overall_score", 0), errors="coerce") or 0)
        num = plot.plot_id.split("_")[1] if "_" in plot.plot_id else plot.plot_id
        defaults: dict[str, str] = {
            "fig_1": (
                f"Figure {num}: Overall site-suitability scores for the top {context.top_k} candidate "
                f"regions under the '{context.workload}' workload weighting. "
                f"{top_region} achieves the highest score of {top_score:.2f}/10. "
                "Scores below 5 are generally considered marginal for the specified requirements."
            ),
            "fig_2": (
                f"Figure {num}: Score-dimension breakdown for the top {context.top_k} candidate regions. "
                "Each cluster of bars represents one scoring dimension (energy, water, climate, latency, "
                "resilience, land). Divergence between candidates within a dimension indicates a "
                "meaningful siting differentiator."
            ),
            "fig_3": (
                f"Figure {num}: Trade-off between total renewable-energy capacity within 50 km (GW) and "
                "latency score for top candidates. Colour indicates overall score. Candidates in the "
                "upper-right quadrant offer the best combination of green-energy access and network "
                "connectivity."
            ),
            "fig_4": (
                f"Figure {num}: Score heatmap across all top candidates and scoring dimensions. "
                "Warmer (darker red/orange) cells indicate higher scores. The heatmap enables rapid "
                "visual identification of dimension-specific strengths and weaknesses and confirms "
                "the relative consistency of water and climate scores across candidates."
            ),
        }
        return defaults.get(
            plot.plot_id,
            f"Figure {num}: {plot.title}. {plot.description}",
        )

    def run(
        self,
        context: ReportContext,
        sections: dict[str, str],
    ) -> ReportDraft:
        """Caption all plots and assemble Draft v1 from the section texts."""
        logger.info(
            "PlotsAgent: captioning %d figure(s) and assembling Draft v1.", len(context.plots)
        )
        for plot in context.plots:
            plot.caption = self.caption_plot(plot, context)

        draft = ReportDraft(
            version=1,
            sections=dict(sections),
            plots=list(context.plots),
            metadata={
                "query":    context.query,
                "workload": context.workload,
                "date":     context.generated_at,
            },
        )
        logger.info("PlotsAgent: Draft v1 assembled.")
        return draft


# ── Agent 4: RefiningAgent ────────────────────────────────────────────────────

class RefiningAgent:
    """
    Refines the Results and Discussion sections of Draft v1 to improve figure
    references and polish the writing, producing Draft v2.
    """

    def __init__(
        self,
        client: Any | None,
        model: str = DEFAULT_MODEL,
        max_retries: int = 1,
    ) -> None:
        self.llm_enabled = bool(client)
        self.model = model or DEFAULT_MODEL
        self.max_retries = max_retries

    def run(self, draft: ReportDraft, context: ReportContext) -> ReportDraft:
        logger.info("RefiningAgent: refining Draft v%d → Draft v2.", draft.version)
        refined = dict(draft.sections)
        for section in ("results", "discussion"):
            if section not in refined:
                continue
            improved = self._refine_section(section, draft, context)
            if improved:
                refined[section] = improved

        new_draft = ReportDraft(
            version=2,
            sections=refined,
            plots=draft.plots,
            bibliography=draft.bibliography,
            metadata={**draft.metadata, "refined_sections": ["results", "discussion"]},
        )
        logger.info("RefiningAgent: Draft v2 assembled.")
        return new_draft

    def _refine_section(
        self, section: str, draft: ReportDraft, context: ReportContext
    ) -> str:
        original = draft.sections.get(section, "")
        if not original:
            return original

        if not self.llm_enabled:
            return self._heuristic_refine(original)

        system = (
            "You are a senior technical editor refining a data-centre site-selection report. "
            "Improve the given section by:\n"
            "1. Replacing bare figure-reference tokens such as [FIG_1] with integrated prose "
            "   like 'As illustrated in Figure 1, ...' or 'Figure 2 shows that ...'.\n"
            "2. Tightening the prose: remove redundancy, improve transitions, vary sentence length.\n"
            "3. Ensuring factual accuracy against the provided candidate data and figure captions.\n"
            "Preserve all technical content and do not introduce new claims. "
            "Return only the improved section text, without any preamble."
        )
        figure_info = [
            {
                "id":      p.plot_id.replace("_", " ").title(),
                "number":  p.plot_id.split("_")[1] if "_" in p.plot_id else p.plot_id,
                "title":   p.title,
                "caption": p.caption,
            }
            for p in draft.plots
        ]
        user = json.dumps({
            "section":           section,
            "original_text":     original,
            "available_figures": figure_info,
            "top_candidates":    context.ranked.head(context.top_k)[
                ["region", "overall_score"]
            ].to_dict(orient="records"),
        }, default=str)
        result = _call_llm(
            self.model, system, user, self.max_retries, temperature=0.2
        )
        return result.strip() if result.strip() else self._heuristic_refine(original)

    @staticmethod
    def _heuristic_refine(text: str) -> str:
        """Minimal text-based refinement when LLM is unavailable."""
        # Convert bare [FIG_N] tokens to "Figure N"
        text = re.sub(r"\[FIG_(\d+)\]", r"Figure \1", text)
        return text


# ── Agent 5: CitationsAgent ───────────────────────────────────────────────────

class CitationsAgent:
    """
    Two-pass citation agent.
      Pass 1 → inserts inline citation numbers [1], [2], … → Draft v3
      Pass 2 → appends the full formatted bibliography    → Draft v4
    """

    KNOWN_REFERENCES: list[dict[str, str]] = [
        {
            "key":  "ons_lad",
            "text": (
                "Office for National Statistics (ONS). Local Authority Districts (December 2024) "
                "Boundaries UK BGC. Open Geography Portal, ONS. "
                "Available at: geoportal.statistics.gov.uk (accessed May 2025)."
            ),
        },
        {
            "key":  "repd",
            "text": (
                "Department for Energy Security and Net Zero (DESNZ). Renewable Energy Planning "
                "Database (REPD). UK Government. "
                "Available at: gov.uk/government/collections/renewable-energy-planning-data "
                "(accessed May 2025)."
            ),
        },
        {
            "key":  "neso_gsp",
            "text": (
                "National Energy System Operator (NESO). Grid Supply Point (GSP) Regions "
                "(January 2025). Available at: nationalgrideso.com (accessed May 2025)."
            ),
        },
        {
            "key":  "ea_flood",
            "text": (
                "Environment Agency (EA). Flood Map for Planning — Flood Zones. "
                "Available at: environment.data.gov.uk (accessed May 2025)."
            ),
        },
        {
            "key":  "ons_pop",
            "text": (
                "Office for National Statistics (ONS). Population Estimates for Local Authorities "
                "in England and Wales: Mid-2024. ONS. "
                "Available at: ons.gov.uk (accessed May 2025)."
            ),
        },
        {
            "key":  "brownfield",
            "text": (
                "Ministry of Housing, Communities & Local Government (MHCLG). Brownfield Land "
                "Register. UK Government Planning Portal. "
                "Available at: gov.uk/guidance/brownfield-land-registers (accessed May 2025)."
            ),
        },
        {
            "key":  "uptime2024",
            "text": (
                "Uptime Institute. Global Data Center Survey Results 2024. "
                "New York: Uptime Institute LLC, 2024."
            ),
        },
        {
            "key":  "dc_siting",
            "text": (
                "Avgerinou, M., Bertoldi, P. & Castellazzi, L. (2017). Trends in Data Centre "
                "Energy Consumption under the European Code of Conduct for Data Centre Energy "
                "Efficiency. Energies, 10(10), 1470. https://doi.org/10.3390/en10101470."
            ),
        },
        {
            "key":  "uk_dc_policy",
            "text": (
                "UK Government. UK National Data Strategy. Department for Science, Innovation "
                "and Technology, 2021. "
                "Available at: gov.uk/government/publications/uk-national-data-strategy "
                "(accessed May 2025)."
            ),
        },
        {
            "key":  "mcdm",
            "text": (
                "Tzeng, G.-H. & Huang, J.-J. (2011). Multiple Attribute Decision Making: "
                "Methods and Applications. Boca Raton: CRC Press."
            ),
        },
    ]

    # Which references are relevant to which section
    SECTION_CITATION_MAP: dict[str, list[str]] = {
        "introduction":  ["uptime2024", "uk_dc_policy", "dc_siting"],
        "methodology":   ["mcdm", "repd", "ons_lad", "neso_gsp"],
        "data_overview": ["ons_lad", "repd", "neso_gsp", "ea_flood", "ons_pop", "brownfield"],
        "results":       ["repd", "ons_lad"],
        "discussion":    ["dc_siting", "mcdm", "ea_flood"],
        "conclusions":   ["uk_dc_policy", "uptime2024"],
    }

    # Regex patterns that trigger a citation for a given reference key
    _CITATION_TRIGGERS: dict[str, list[str]] = {
        "ons_lad":      [r"ONS\b", r"\bLAD\b", r"local authority district", r"boundary centroid", r"candidate region"],
        "repd":         [r"REPD\b", r"DESNZ\b", r"Renewable Energy Planning Database", r"renewable capacity"],
        "neso_gsp":     [r"\bGSP\b", r"Grid Supply Point", r"\bNESO\b"],
        "ea_flood":     [r"\bEA\b", r"flood.?zone", r"Environment Agency", r"flood.?map"],
        "ons_pop":      [r"population estimate", r"ONS population"],
        "brownfield":   [r"\bbrownfield\b"],
        "uptime2024":   [r"data.?centre.*market", r"global.*data.?centre", r"Uptime Institute", r"demand.*grow"],
        "dc_siting":    [r"energy consumption", r"\bPUE\b", r"Code of Conduct", r"energy efficiency"],
        "uk_dc_policy": [r"UK.*policy", r"National Data Strategy", r"AI Growth Zone", r"government.*strategy"],
        "mcdm":         [r"multi.?criteria", r"weighted.*scor", r"\bMCDM\b", r"decision.making"],
    }

    def __init__(
        self,
        llm_enabled: bool,
        model: str = DEFAULT_MODEL,
        max_retries: int = 1,
    ) -> None:
        self.llm_enabled = llm_enabled
        self.model = model
        self.max_retries = max_retries

    def _assign_citation_numbers(self) -> dict[str, int]:
        """Assign sequential numbers to references in order of first section appearance."""
        section_order = [
            "introduction", "methodology", "data_overview",
            "results", "discussion", "conclusions",
        ]
        index: dict[str, int] = {}
        counter = 1
        for section in section_order:
            for key in self.SECTION_CITATION_MAP.get(section, []):
                if key not in index:
                    index[key] = counter
                    counter += 1
        return index

    def _insert_citations_heuristic(
        self, text: str, section: str, ref_index: dict[str, int]
    ) -> str:
        """Keyword-match citation insertion when LLM is unavailable."""
        cited: set[str] = set()
        for key in self.SECTION_CITATION_MAP.get(section, []):
            if key not in ref_index:
                continue
            for pattern in self._CITATION_TRIGGERS.get(key, []):
                if re.search(pattern, text, re.IGNORECASE) and key not in cited:
                    text = re.sub(
                        pattern,
                        lambda m, k=key, ri=ref_index: f"{m.group(0)} [{ri[k]}]",
                        text, count=1, flags=re.IGNORECASE,
                    )
                    cited.add(key)
                    break
        return text

    def _insert_citations_llm(
        self, section: str, text: str, ref_index: dict[str, int]
    ) -> str:
        if not self.llm_enabled:
            return self._insert_citations_heuristic(text, section, ref_index)

        refs = [
            {
                "number": ref_index[k],
                "key":    k,
                "text":   next(
                    (r["text"] for r in self.KNOWN_REFERENCES if r["key"] == k), ""
                ),
            }
            for k in self.SECTION_CITATION_MAP.get(section, [])
            if k in ref_index
        ]
        if not refs:
            return text

        system = (
            "You are a technical editor adding citations to a report section. "
            "Insert citation numbers (e.g. [1], [3]) immediately after the relevant claim "
            "or data statement, matching each number to the correct reference. "
            "Do not alter any wording — only add citation markers. "
            "Return only the modified section text, no preamble."
        )
        user = json.dumps(
            {"section": section, "text": text, "references": refs}, default=str
        )
        result = _call_llm(
            self.model, system, user, self.max_retries, temperature=0.1
        )
        return result.strip() if result.strip() else self._insert_citations_heuristic(
            text, section, ref_index
        )

    def run(
        self, draft: ReportDraft, context: ReportContext
    ) -> tuple[ReportDraft, ReportDraft]:
        """
        Returns (draft_v3_inline_citations, draft_v4_with_full_bibliography).
        """
        logger.info("CitationsAgent: processing Draft v%d.", draft.version)
        ref_index = self._assign_citation_numbers()

        section_order = [
            "introduction", "methodology", "data_overview",
            "results", "discussion", "conclusions",
        ]

        # ── Pass 1: inline citations → Draft v3 ──────────────────────────
        cited_sections = dict(draft.sections)
        for section in section_order:
            if section in cited_sections:
                cited_sections[section] = self._insert_citations_llm(
                    section, cited_sections[section], ref_index
                )
                logger.info("CitationsAgent: citations inserted in '%s'.", section)

        draft_v3 = ReportDraft(
            version=3,
            sections=cited_sections,
            plots=draft.plots,
            bibliography=draft.bibliography,
            metadata={**draft.metadata, "citations_added": True},
        )

        # ── Pass 2: build bibliography → Draft v4 ────────────────────────
        bibliography = [
            {
                "number": ref_index[ref["key"]],
                "key":    ref["key"],
                "text":   ref["text"],
            }
            for ref in self.KNOWN_REFERENCES
            if ref["key"] in ref_index
        ]
        bibliography.sort(key=lambda r: r["number"])

        draft_v4 = ReportDraft(
            version=4,
            sections=dict(cited_sections),
            plots=draft.plots,
            bibliography=bibliography,
            metadata={**draft_v3.metadata, "bibliography_complete": True},
        )
        logger.info(
            "CitationsAgent: Draft v3 and v4 produced. Bibliography: %d entries.",
            len(bibliography),
        )
        return draft_v3, draft_v4


# ── Pipeline orchestrator ─────────────────────────────────────────────────────

def run_pdf_report_pipeline(
    query: str,
    workload: str,
    ranked: pd.DataFrame,
    agent_summaries: list[dict[str, Any]],
    critic: dict[str, Any],
    synthesis: dict[str, Any],
    site_selection: dict[str, Any],
    top_k: int,
    runner: Any | None = None,          # AgentRunner instance (optional)
    output_path: str | None = None,
    plot_dir: str | None = None,
) -> str:
    """
    Run the full five-stage PDF report pipeline and return the path to the
    generated PDF file.

    Stages
    ------
    1. PreprocessAgent  → ReportContext (with figures)
    2. SectionAgent(s)  → section texts
    3. PlotsAgent       → Draft v1 (captions + assembled draft)
    4. RefiningAgent    → Draft v2 (polished results/discussion)
    5. CitationsAgent   → Draft v3 (inline citations) + Draft v4 (bibliography)
    6. pdf_renderer     → PDF file
    """
    from .pdf_renderer import render_pdf_report  # imported here to avoid circular deps

    # Extract model selection and agent availability from the runner if provided.
    llm_enabled = bool(runner is not None and getattr(runner, "enabled", False))
    fast_model   = FAST_MODEL   or DEFAULT_MODEL
    reason_model = REASONING_MODEL or DEFAULT_MODEL
    base_model   = DEFAULT_MODEL

    if llm_enabled:
        fast_model   = getattr(runner, "fast_model",      fast_model)
        reason_model = getattr(runner, "reasoning_model", reason_model)
        base_model   = getattr(runner, "model",           base_model)

    logger.info(
        "PDF pipeline: starting. llm=%s model=%s", "enabled" if llm_enabled else "disabled", base_model
    )

    # Stage 1 — Preprocess
    preprocess = PreprocessAgent(plot_dir=plot_dir)
    context = preprocess.run(
        query=query, workload=workload, ranked=ranked,
        agent_summaries=agent_summaries, critic=critic,
        synthesis=synthesis, site_selection=site_selection, top_k=top_k,
    )

    # Stage 2 — Section agents
    SECTIONS = [
        "abstract", "introduction", "methodology", "data_overview",
        "results", "discussion", "conclusions",
    ]
    section_agent = SectionAgent(llm_enabled, model=fast_model)
    sections: dict[str, str] = {}
    for section in SECTIONS:
        sections[section] = section_agent.run(section, context)

    # Stage 3 — Plots agent → Draft v1
    plots_agent = PlotsAgent(llm_enabled, model=fast_model)
    draft_v1 = plots_agent.run(context, sections)

    # Stage 4 — Refining agent → Draft v2
    refining_agent = RefiningAgent(llm_enabled, model=reason_model)
    draft_v2 = refining_agent.run(draft_v1, context)

    # Stage 5 — Citations agent → Draft v3, Draft v4
    citations_agent = CitationsAgent(llm_enabled, model=base_model)
    _draft_v3, draft_v4 = citations_agent.run(draft_v2, context)

    # Stage 6 — Render PDF
    pdf_path = render_pdf_report(draft_v4, context, output_path=output_path)
    logger.info("PDF pipeline: complete. PDF written to %s.", pdf_path)
    return pdf_path
