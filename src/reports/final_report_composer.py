"""Final Report Composer.

Assembles the final markdown report by filling blueprint sections with
evidence from agent outputs and the existing site-selection result.
Section order and depth follow the approved blueprint exactly.
"""
from __future__ import annotations

from typing import Any

from ..preferences.schemas import AgentOutput, ReportBlueprint, UserPreferences

_DEPTH_INTRO = {
    "short":    "Brief overview.",
    "medium":   "Balanced analysis.",
    "detailed": "Comprehensive evidence-based analysis.",
}

# Maps section name keywords → which agent outputs are relevant
_SECTION_AGENT_ROUTING: dict[str, list[str]] = {
    "executive":       [],
    "summary":         [],
    "recommendation":  ["EnergyAgent", "LatencyAgent", "LandPlanningAgent"],
    "site":            ["EnergyAgent", "LatencyAgent", "LandPlanningAgent"],
    "budget":          [],
    "financial":       [],
    "risk":            ["ResilienceAgent", "WaterAgent", "LandPlanningAgent"],
    "uncertainty":     ["ResilienceAgent", "WaterAgent", "ClimateCoolingAgent"],
    "energy":          ["EnergyAgent"],
    "carbon":          ["EnergyAgent", "ClimateCoolingAgent"],
    "water":           ["WaterAgent"],
    "climate":         ["ClimateCoolingAgent"],
    "cooling":         ["ClimateCoolingAgent"],
    "latency":         ["LatencyAgent"],
    "resilience":      ["ResilienceAgent"],
    "land":            ["LandPlanningAgent"],
    "planning":        ["LandPlanningAgent"],
    "data quality":    [],
    "caveat":          [],
    "policy":          [],
}


def _agents_for_section(section_name: str, outputs: list[AgentOutput]) -> list[AgentOutput]:
    """Return agent outputs relevant to a section, first by section_targets then by name heuristic."""
    targeted = [o for o in outputs if section_name in o.section_targets]
    if targeted:
        return targeted

    lower = section_name.lower()
    heuristic: list[AgentOutput] = []
    for keyword, agents in _SECTION_AGENT_ROUTING.items():
        if keyword in lower:
            heuristic += [o for o in outputs if o.agent_name in agents and o not in heuristic]
    return heuristic or outputs


def _money(value: float | None) -> str:
    if value is None:
        return "unspecified"
    if abs(value) >= 1e9:
        return f"GBP {value / 1e9:.2f}bn"
    if abs(value) >= 1e6:
        return f"GBP {value / 1e6:.1f}m"
    return f"GBP {value:,.0f}"


def _render_executive_summary(site_result: dict[str, Any], preferences: UserPreferences) -> str:
    recs = site_result.get("recommendations", [])
    budget = site_result.get("budget_plan", {})
    top = recs[0] if recs else {}

    lines = [
        f"**Feasible:** {site_result.get('feasibility', 'unknown')}",
        f"**Top recommendation:** {top.get('location', 'N/A')} "
        f"(score: {top.get('score_breakdown', {}).get('production', 'N/A')}/10, "
        f"priority: {top.get('priority_flag', 'N/A')})",
        f"**Estimated total capex:** {_money(budget.get('estimated_total_capex_gbp'))}",
        f"**Annual opex:** {_money(budget.get('estimated_annual_opex_gbp'))}",
        f"**Centres recommended:** {budget.get('recommended_centre_count', 'N/A')}",
    ]
    critics = site_result.get("critic_results", [])
    failed = [c["name"] for c in critics if not c.get("passed", True)]
    if failed:
        lines.append(f"**Critic flags:** {', '.join(failed)}")

    return "\n".join(f"- {l}" for l in lines)


def _render_site_recommendations(site_result: dict[str, Any], depth: str) -> str:
    recs = site_result.get("recommendations", [])
    if not recs:
        return "_No feasible site recommendation was generated for the specified constraints._"

    lines: list[str] = []
    for i, rec in enumerate(recs, 1):
        scores = rec.get("score_breakdown", {})
        lines.append(
            f"### {i}. {rec.get('location', 'Unknown')}  "
            f"*({rec.get('priority_flag', '')})*"
        )
        lines.append(
            f"Overall score: **{scores.get('production', scores.get('base', '?'))}/10** | "
            f"Feasible: {rec.get('feasibility', '?')} | "
            f"Capex: {_money(rec.get('estimated_capex_gbp'))}"
        )
        if depth in ("medium", "detailed"):
            lines.append("")
            score_items = " | ".join(
                f"{k}: {v:.1f}" for k, v in scores.items() if k not in ("production", "base")
            )
            lines.append(f"Scores: {score_items}")
            lines.append(f"{rec.get('text_summary', '')}")
        if depth == "detailed" and rec.get("explanation"):
            lines.append("")
            lines.append(rec["explanation"])
        if rec.get("policy_points"):
            lines.append(f"Policy: {'; '.join(rec['policy_points'][:3])}")
        lines.append("")
    return "\n".join(lines)


def _render_budget(site_result: dict[str, Any], depth: str) -> str:
    budget = site_result.get("budget_plan", {})
    lines = [
        f"- Compute requested: **{budget.get('requested_compute_mw', '?')} MW**",
        f"- Recommended centres: **{budget.get('recommended_centre_count', '?')}**",
        f"- Estimated total capex: **{_money(budget.get('estimated_total_capex_gbp'))}**",
        f"- Estimated annual opex: **{_money(budget.get('estimated_annual_opex_gbp'))}**",
        f"- Budget feasible: **{budget.get('budget_feasible', '?')}**",
    ]
    if depth == "detailed":
        for item in site_result.get("budget_plan", {}).get("allocation", []):
            lines.append(
                f"  - {item.get('region', '?')}: {item.get('compute_mw', '?')} MW, "
                f"capex {_money(item.get('estimated_capex_gbp'))}"
            )
        summary = budget.get("cost_materials_summary", {})
        if summary.get("assumptions"):
            lines.append("\nAssumptions:")
            for a in summary["assumptions"]:
                lines.append(f"- {a}")
    return "\n".join(lines)


def _render_agent_section(relevant_outputs: list[AgentOutput], depth: str) -> str:
    if not relevant_outputs:
        return "_No agent analysis available for this section._"

    lines: list[str] = []
    for output in relevant_outputs:
        lines.append(f"**{output.agent_name}**: {output.recommendation_impact}")
        if depth in ("medium", "detailed") and output.claims:
            for claim in output.claims[:5]:
                lines.append(f"- {claim.get('text', '')}")
        if depth == "detailed" and output.risks:
            lines.append("")
            lines.append("Risks:")
            for risk in output.risks[:4]:
                lines.append(f"- {risk}")
        lines.append("")
    return "\n".join(lines)


def _render_risk_section(
    relevant_outputs: list[AgentOutput],
    site_result: dict[str, Any],
    depth: str,
) -> str:
    lines: list[str] = []

    # Critic results from deterministic critics
    for critic in site_result.get("critic_results", []):
        if not critic.get("passed", True):
            lines.append(f"**{critic['name']}** (FAILED):")
            for finding in critic.get("findings", []):
                lines.append(f"- {finding}")
            lines.append("")

    # Agent risks and uncertainties
    all_risks: list[str] = []
    all_gaps: list[str] = []
    for output in relevant_outputs:
        all_risks.extend(output.risks)
        all_gaps.extend(output.data_gaps)
        all_gaps.extend(output.uncertainties)

    if all_risks:
        lines.append("**Agent-identified risks:**")
        for risk in all_risks[:8]:
            lines.append(f"- {risk}")
        lines.append("")

    if depth in ("medium", "detailed") and all_gaps:
        lines.append("**Data gaps and uncertainties:**")
        for gap in all_gaps[:6]:
            lines.append(f"- {gap}")

    return "\n".join(lines) if lines else "_No critical risks flagged._"


def _render_data_quality(site_result: dict[str, Any], all_outputs: list[AgentOutput]) -> str:
    fixed_caveats = [
        "Water score is a population-pressure heuristic — real water-stress data not yet integrated.",
        "Climate score uses latitude as a crude cooling proxy — HadUK-Grid data not yet loaded.",
        "Flood-zone data is optional and may be absent unless explicitly processed.",
        "Grid headroom, fibre latency, and existing DC capacity are not modelled.",
    ]
    lines = [f"- {c}" for c in fixed_caveats]
    for output in all_outputs:
        for gap in output.data_gaps[:2]:
            line = f"- {output.agent_name}: {gap}"
            if line not in lines:
                lines.append(line)
    return "\n".join(lines)


def compose_final_report(
    user_query: str,
    blueprint: ReportBlueprint,
    agent_outputs: list[AgentOutput],
    preferences: UserPreferences,
    site_result: dict[str, Any],
) -> str:
    """Compose the final markdown report according to the approved blueprint.

    Sections appear in blueprint order. Each section's depth controls verbosity.
    Agent outputs are routed to sections by name heuristics and section_targets.
    """
    parts: list[str] = [
        f"# {blueprint.title}",
        f"*{blueprint.goal}*\n",
        f"**Audience:** {preferences.audience} | "
        f"**Style:** {preferences.preferred_style} | "
        f"**Depth:** {preferences.report_depth}",
    ]

    for section in blueprint.sections:
        parts.append(f"\n## {section.name}")
        lower = section.name.lower()

        if any(k in lower for k in ("executive", "overview")):
            parts.append(_render_executive_summary(site_result, preferences))

        elif any(k in lower for k in ("recommendation", "site", "candidate", "location", "ranked")):
            parts.append(_render_site_recommendations(site_result, section.depth))

        elif any(k in lower for k in ("budget", "financial", "cost")):
            parts.append(_render_budget(site_result, section.depth))

        elif any(k in lower for k in ("risk", "uncertainty", "resilience")):
            relevant = _agents_for_section(section.name, agent_outputs)
            parts.append(_render_risk_section(relevant, site_result, section.depth))

        elif any(k in lower for k in ("data quality", "caveat", "limitation", "disclaimer")):
            parts.append(_render_data_quality(site_result, agent_outputs))

        else:
            # Generic section: route to relevant agents
            relevant = _agents_for_section(section.name, agent_outputs)
            parts.append(_render_agent_section(relevant, section.depth))

        if section.required_evidence:
            evidence_str = ", ".join(section.required_evidence)
            parts.append(f"\n*Evidence used: {evidence_str}*")

    parts.append("\n---")
    parts.append(
        f"*Report generated by Preference-Guided Blueprint System | "
        f"Agents run: {', '.join(blueprint.agents_to_run)} | "
        f"Skipped: {', '.join(blueprint.agents_to_skip) or 'none'}*"
    )
    parts.append(
        "*This is a hackathon prototype. Scores are heuristic. "
        "Water and climate scores are placeholders.*"
    )

    return "\n\n".join(parts)
