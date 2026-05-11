from __future__ import annotations

from typing import Any

import pandas as pd

from .schemas import SiteSelectionResult
from .scoring import workload_summary


DISCLAIMER = (
    "This is a hackathon prototype using public datasets and heuristic scoring. "
    "It is not an investment-grade site-selection tool. Some scores, especially water and climate, "
    "are placeholders until appropriate datasets are added."
)


DISPLAY_COLS = [
    "region",
    "overall_score",
    "energy_score_raw",
    "water_score_raw",
    "climate_score_raw",
    "latency_score_raw",
    "resilience_score_raw",
    "land_score_raw",
    "planning_risk_score_raw",
    "renewable_capacity_50km_mw",
    "brownfield_hectares_50km",
]


def table_markdown(df: pd.DataFrame, top_k: int | None = None) -> str:
    view = df[DISPLAY_COLS].head(top_k).copy() if top_k else df[DISPLAY_COLS].copy()
    for col in view.columns:
        if col != "region":
            view[col] = pd.to_numeric(view[col], errors="coerce").round(2)
    return view.to_markdown(index=False)


def normalise_bullets(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, dict):
        return [f"{key}: {item}" for key, item in value.items()]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def agent_block(agent: dict[str, Any]) -> str:
    key_points = normalise_bullets(agent.get("key_points"))[:5]
    risk_items = normalise_bullets(agent.get("risks"))[:5]
    points = "\n".join(f"- {p}" for p in key_points) or "- None provided"
    risks = "\n".join(f"- {r}" for r in risk_items) or "- None provided"
    return (
        f"### {agent.get('agent', 'Agent')}\n\n"
        f"{agent.get('summary', '')}\n\n"
        f"Key points:\n{points}\n\n"
        f"Risks:\n{risks}\n\n"
        f"Confidence: {agent.get('confidence', 'unknown')}\n"
    )


def dataset_availability(features: pd.DataFrame) -> str:
    notes = features["data_quality_notes"].dropna().iloc[0] if "data_quality_notes" in features and len(features) else ""
    lines = [
        "- ONS LAD boundaries: used if geospatial dependencies are installed; otherwise LAD hints are retained.",
        "- DESNZ REPD renewables: used for radius capacity features when coordinates are detected.",
        "- NESO GSP regions: used if geospatial dependencies are installed.",
        "- EA flood zones: cached in feature table only when explicitly built with flood processing.",
        "- ONS population: joined where LAD code/name matches the England/Wales workbook.",
        "- Brownfield land/site: point-based radius counts and hectares are computed where point WKT is present.",
    ]
    if notes:
        lines.append(f"- Diagnostics: {notes}")
    return "\n".join(lines)


def build_markdown_report(
    query: str,
    workload: str,
    ranked: pd.DataFrame,
    agent_summaries: list[dict[str, Any]],
    critic: dict[str, Any],
    synthesis: dict[str, Any],
    top_k: int,
) -> str:
    top = ranked.iloc[0]
    uncertainties = [
        "Water score is heuristic until water-stress, abstraction, and cooling-water datasets are added.",
        "Climate score uses latitude as a crude cooling proxy until HadUK-Grid or similar climate data is available.",
        "Flood-zone processing may be skipped unless the large EA file is explicitly processed and cached.",
        "Existing data-centre capacity and grid headroom/connection queue data are placeholders or missing.",
    ]
    next_sources = [
        "Water stress and abstraction licence datasets.",
        "HadUK-Grid climate normals and heatwave projections.",
        "DNO/TO grid capacity, connection queue, substation headroom, and constraint datasets.",
        "Commercial fibre/backbone latency and peering data.",
        "UK-wide population and business demand data, especially for Scottish candidates.",
    ]
    return "\n\n".join(
        [
            "# Data Centre Site Selection Report",
            f"## Query\n{query}",
            f"## Workload Profile\n`{workload}` weights: {workload_summary(workload)}",
            f"## Dataset Availability\n{dataset_availability(ranked)}",
            f"## Ranked Candidates\n{table_markdown(ranked, top_k)}",
            f"## Top Recommendation\n{top['region']} with overall score {top['overall_score']:.2f}/10.",
            "## Agent Assessments\n" + "\n".join(agent_block(a) for a in agent_summaries),
            "## Critic Review\n" + agent_block(critic),
            "## Uncertainties\n" + "\n".join(f"- {u}" for u in uncertainties),
            "## Next Data Sources to Add\n" + "\n".join(f"- {s}" for s in next_sources),
            "## Prototype Disclaimer\n" + DISCLAIMER,
            "## Final Recommendation\n" + synthesis.get("summary", ""),
        ]
    )


def terminal_report(
    query: str,
    workload: str,
    ranked: pd.DataFrame,
    agent_summaries: list[dict[str, Any]],
    critic: dict[str, Any],
    synthesis: dict[str, Any],
    top_k: int,
) -> str:
    top = ranked.iloc[0]
    agent_lines = "\n".join(f"- {a.get('agent')}: {a.get('summary')}" for a in agent_summaries)
    return f"""Query: {query}
Workload type: {workload}

Dataset availability summary:
{dataset_availability(ranked)}

Top recommendation:
{top['region']} ({top['overall_score']:.2f}/10)

Ranked candidate table:
{table_markdown(ranked, top_k)}

Per-agent summaries:
{agent_lines}

Critic comments:
{critic.get('summary', '')}

Final recommendation:
{synthesis.get('summary', '')}

Main uncertainties:
- Water and climate scores are placeholders.
- Flood features may be missing unless the large flood dataset has been preprocessed.
- Grid headroom, fibre latency, existing data-centre capacity, and water licensing are not yet modelled.

Suggested next datasets to add:
- Water stress/abstraction data.
- HadUK-Grid climate data.
- Grid headroom and connection queue data.
- Fibre latency and peering data.

Prototype disclaimer:
{DISCLAIMER}
"""


def money(value: float | None) -> str:
    if value is None:
        return "unspecified"
    if abs(value) >= 1_000_000_000:
        return f"GBP {value / 1_000_000_000:.2f}bn"
    if abs(value) >= 1_000_000:
        return f"GBP {value / 1_000_000:.1f}m"
    return f"GBP {value:,.0f}"


def production_markdown_report(result: SiteSelectionResult) -> str:
    data = result.to_dict()
    constraints = data["constraints"]
    rec_lines = []
    for rec in data["recommendations"]:
        rec_lines.append(
            "\n".join(
                [
                    f"### {rec['location']}",
                    f"- Coordinates: {rec['latitude']}, {rec['longitude']}; altitude {rec['altitude_m']} m",
                    f"- Priority: {rec['priority_flag']}; feasible: {rec['feasibility']}",
                    f"- Compute allocation: {rec['compute_mw']} MW",
                    f"- Estimated capex: {money(rec['estimated_capex_gbp'])}; annual opex: {money(rec['estimated_annual_opex_gbp'])}",
                    f"- Summary: {rec['text_summary']}",
                    f"- Problem: {rec['problem_summary'] or 'None'}",
                    "- Policy points:\n" + "\n".join(f"  - {point}" for point in rec["policy_points"]),
                    f"- Explanation: {rec['explanation']}",
                ]
            )
        )
    stages = []
    for stage in data["nested_search"]:
        regions = ", ".join(item["region"] for item in stage["top_regions"][:5])
        stages.append(f"- {stage['label']}: {stage['candidate_count']} candidates. Top regions: {regions or 'none'}.")
    critics = "\n".join(
        f"- {critic['name']}: {'passed' if critic['passed'] else 'needs review'}; {'; '.join(critic['findings'])}"
        for critic in data["critic_results"]
    )
    policy_research = data.get("policy_research")
    policy_research_block = "Not requested."
    if policy_research:
        sources = "\n".join(f"- {source}" for source in normalise_bullets(policy_research.get("sources")))
        policy_research_block = "\n".join(
            [
                policy_research.get("summary", ""),
                "Key points:",
                "\n".join(f"- {point}" for point in normalise_bullets(policy_research.get("key_points"))),
                "Sources:",
                sources or "- None returned",
            ]
        )
    budget = data["budget_plan"]
    return "\n\n".join(
        [
            "# Production Data-Centre Site Selection Report",
            f"## Input Interpretation\nPrompt: {constraints['prompt']}\n\nWorkload: `{constraints['workload']}`\n\nCompute: {budget['requested_compute_mw']} MW\n\nRegion: {constraints['region_text']}\n\nBudget: {money(constraints['budget_gbp'])}",
            "## Suggested Constraints\n" + "\n".join(f"- {item}" for item in constraints["suggested_constraints"]),
            "## Nested Search\n" + "\n".join(stages),
            "## Budget And Materials\n"
            + f"Recommended centres: {budget['recommended_centre_count']}\n\n"
            + f"Estimated total capex: {money(budget['estimated_total_capex_gbp'])}\n\n"
            + f"Estimated annual opex: {money(budget['estimated_annual_opex_gbp'])}\n\n"
            + "\n".join(f"- {key}: {value}" for key, value in budget["cost_materials_summary"].items() if key != "assumptions")
            + "\n\nAssumptions:\n"
            + "\n".join(f"- {item}" for item in budget["cost_materials_summary"]["assumptions"]),
            "## Centre Recommendations\n" + ("\n\n".join(rec_lines) if rec_lines else "No feasible recommendation generated."),
            "## Critic Review\n" + critics,
            "## Web Policy Research\n" + policy_research_block,
            "## Explanation\n" + data["explanation"],
            "## Feedback Request\n" + data["feedback_prompt"],
            "## Important Caveats\n" + DISCLAIMER,
        ]
    )


def production_terminal_report(result: SiteSelectionResult) -> str:
    data = result.to_dict()
    lines = [
        f"Feasible: {data['feasibility']}",
        f"Needs human input: {data['needs_human_input']}",
        f"Input scope: {data['constraints']['region_text']} | workload: {data['constraints']['workload']} | compute: {data['budget_plan']['requested_compute_mw']} MW",
        f"Budget: {money(data['constraints']['budget_gbp'])} | estimated capex: {money(data['budget_plan']['estimated_total_capex_gbp'])}",
        "",
        "Recommended centres:",
    ]
    if not data["recommendations"]:
        lines.append("- None")
    for rec in data["recommendations"]:
        lines.append(
            f"- {rec['location']} ({rec['latitude']}, {rec['longitude']}, {rec['altitude_m']} m): "
            f"{rec['priority_flag']}, feasible={rec['feasibility']}, capex={money(rec['estimated_capex_gbp'])}"
        )
        lines.append(f"  {rec['text_summary']}")
        if rec["problem_summary"]:
            lines.append(f"  Problem: {rec['problem_summary']}")
    lines.extend(["", "Explanation:", data["explanation"], "", "Feedback:", data["feedback_prompt"]])
    return "\n".join(lines)
