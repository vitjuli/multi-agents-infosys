from __future__ import annotations

from typing import Any

import pandas as pd

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
