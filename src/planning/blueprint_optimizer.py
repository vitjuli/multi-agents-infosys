"""Blueprint Optimiser.

Uses policy weights and user preferences to design the optimal report
structure, then asks an LLM to instantiate it as a concrete ReportBlueprint.
"""
from __future__ import annotations

import json

from ..llm_client import structured_chat
from ..llm_schemas import ReportBlueprintPayload
from ..preferences.schemas import AgentTask, ReportBlueprint, ReportSection, UserPreferences

# Canonical list of available existing agents
AVAILABLE_AGENTS = [
    "EnergyAgent",
    "WaterAgent",
    "ClimateCoolingAgent",
    "LatencyAgent",
    "ResilienceAgent",
    "LandPlanningAgent",
]

# Maps user-friendly priority names → agents most relevant to them
_PRIORITY_AGENT_MAP: dict[str, list[str]] = {
    "energy":      ["EnergyAgent"],
    "low-carbon":  ["EnergyAgent", "ClimateCoolingAgent"],
    "latency":     ["LatencyAgent"],
    "resilience":  ["ResilienceAgent"],
    "land":        ["LandPlanningAgent"],
    "budget":      [],  # budget comes from planner, not specialist agents
    "policy":      [],  # handled by PolicyResearchAgent (web-enabled, optional)
    "uncertainty": ["ResilienceAgent", "LandPlanningAgent"],
    "water":       ["WaterAgent"],
}

# Default fallback blueprint — used when LLM is unavailable
def _default_blueprint(
    user_query: str,
    preferences: UserPreferences,
    agents_to_run: list[str],
    agents_to_skip: list[str],
) -> ReportBlueprint:
    sections: list[ReportSection] = []

    if preferences.preferred_style == "executive" or preferences.report_depth == "short":
        sections.append(ReportSection(
            name="Executive Summary",
            purpose="Concise decision-ready overview",
            depth="short",
            required_evidence=["top recommendation", "feasibility", "top risk"],
        ))

    sections.append(ReportSection(
        name="Top Site Recommendations",
        purpose="Ranked candidate locations with scores",
        depth=preferences.report_depth,
        required_evidence=["site name", "overall score", "capex estimate"],
    ))

    if "budget" in preferences.primary_priorities:
        sections.append(ReportSection(
            name="Budget Analysis",
            purpose="Financial feasibility and cost drivers",
            depth=preferences.report_depth,
            required_evidence=["capex", "opex", "budget feasibility"],
        ))

    if preferences.risk_tolerance == "low" or "Top risks" in preferences.must_include:
        sections.append(ReportSection(
            name="Risk and Uncertainty",
            purpose="Critical risks, data gaps, and decision impact",
            depth="detailed" if preferences.risk_tolerance == "low" else "medium",
            required_evidence=["risk severity", "data gaps", "mitigation"],
        ))

    for priority in preferences.primary_priorities:
        if priority in ("energy", "low-carbon") and "EnergyAgent" in agents_to_run:
            sections.append(ReportSection(
                name="Energy and Carbon Analysis",
                purpose="Renewable capacity, grid access, and CO2 proxy",
                depth=preferences.report_depth,
                required_evidence=["renewable capacity MW", "operational vs pipeline", "GSP access"],
            ))
            break

    sections.append(ReportSection(
        name="Data Quality and Caveats",
        purpose="Transparency on placeholder scores and missing datasets",
        depth="short",
        required_evidence=["placeholder scores", "missing datasets", "confidence"],
    ))

    agent_tasks: list[AgentTask] = []
    for agent in agents_to_run:
        task_map = {
            "EnergyAgent": AgentTask(
                agent="EnergyAgent",
                goal="Analyse renewable capacity and grid connectivity for top candidates",
                required_outputs=["renewable capacity", "operational vs pipeline split", "GSP availability", "energy risks"],
                section_targets=["Energy and Carbon Analysis", "Top Site Recommendations"],
            ),
            "WaterAgent": AgentTask(
                agent="WaterAgent",
                goal="Assess water stress and cooling constraints",
                required_outputs=["water stress score", "cooling constraints", "uncertainty note"],
                section_targets=["Risk and Uncertainty"],
            ),
            "ClimateCoolingAgent": AgentTask(
                agent="ClimateCoolingAgent",
                goal="Assess climate suitability for cooling efficiency",
                required_outputs=["cooling proxy score", "climate risks", "data gap note"],
                section_targets=["Energy and Carbon Analysis"],
            ),
            "LatencyAgent": AgentTask(
                agent="LatencyAgent",
                goal="Evaluate proximity to demand hubs and latency trade-offs",
                required_outputs=["distance to hubs km", "latency score", "workload suitability"],
                section_targets=["Top Site Recommendations"],
            ),
            "ResilienceAgent": AgentTask(
                agent="ResilienceAgent",
                goal="Identify flood risk, resilience constraints, and missing data",
                required_outputs=["flood zone flags", "resilience score", "data gaps"],
                section_targets=["Risk and Uncertainty"],
            ),
            "LandPlanningAgent": AgentTask(
                agent="LandPlanningAgent",
                goal="Assess brownfield land availability and planning risk",
                required_outputs=["brownfield hectares", "planning risk score", "land constraints"],
                section_targets=["Risk and Uncertainty", "Top Site Recommendations"],
            ),
        }
        if agent in task_map:
            agent_tasks.append(task_map[agent])

    return ReportBlueprint(
        title=f"UK Data Centre Site Feasibility Report",
        goal=f"Evaluate candidate UK locations for data centre deployment based on: {user_query[:120]}",
        sections=sections,
        agents_to_run=agents_to_run,
        agents_to_skip=agents_to_skip,
        agent_tasks=agent_tasks,
    )


def _select_agents(preferences: UserPreferences) -> tuple[list[str], list[str]]:
    """Choose which agents to run based on priorities and policy weights."""
    selected: set[str] = set()

    # Always include agents for stated priorities
    for priority in preferences.primary_priorities:
        for agent in _PRIORITY_AGENT_MAP.get(priority, []):
            selected.add(agent)

    # Always run EnergyAgent (core to any DC site selection)
    selected.add("EnergyAgent")

    # Add ResilienceAgent when risk tolerance is low
    if preferences.risk_tolerance == "low":
        selected.add("ResilienceAgent")

    # Add LandPlanningAgent unless explicitly avoided
    if "land" not in preferences.must_avoid:
        selected.add("LandPlanningAgent")

    agents_to_run = sorted(selected, key=AVAILABLE_AGENTS.index)
    agents_to_skip = [a for a in AVAILABLE_AGENTS if a not in selected]

    return agents_to_run, agents_to_skip


def optimise_report_blueprint(
    user_query: str,
    preferences: UserPreferences,
    policy: dict,
) -> ReportBlueprint:
    """Generate an optimised ReportBlueprint using LLM + policy weights.

    Falls back to a rule-based blueprint if the LLM is unavailable.
    """
    agents_to_run, agents_to_skip = _select_agents(preferences)

    system = (
        "You are a research architect designing a structured evidence report. "
        "Given user preferences and policy weights, produce a ReportBlueprint as strict JSON. "
        "JSON must have keys: title (string), goal (string), "
        "sections (array of {name, purpose, depth, required_evidence}), "
        "agents_to_run (array of agent names from the available list), "
        "agents_to_skip (array of agent names), "
        "agent_tasks (array of {agent, goal, required_outputs, section_targets}). "
        "depth values must be one of: short, medium, detailed. "
        "Order sections so the most decision-relevant content appears first. "
        "If risk_tolerance is low, place Risk section early. "
        "Use the policy weights to prioritise: higher decision_relevance → more decision-focused sections; "
        "higher risk_severity → more risk detail; higher conciseness → fewer, shorter sections. "
        "Return ONLY the JSON object, no other text."
    )

    context = {
        "user_query": user_query,
        "preferences": preferences.to_dict(),
        "available_agents": agents_to_run,
        "skipped_agents": agents_to_skip,
        "policy_weights": policy,
        "instruction": (
            "Design a report blueprint that serves the stated audience and priorities. "
            "Include only sections that add decision value. Avoid generic background sections."
        ),
    }

    try:
        result = structured_chat(
            system,
            json.dumps(context),
            ReportBlueprintPayload,
        )
    except Exception:
        # LLM unavailable or returned bad JSON — use rule-based fallback
        return _default_blueprint(user_query, preferences, agents_to_run, agents_to_skip)

    # Parse LLM response into typed objects
    try:
        sections = [
            ReportSection(
                name=s.name,
                purpose=s.purpose,
                depth=s.depth,
                required_evidence=s.required_evidence,
            )
            for s in result.sections
        ]

        agent_tasks = [
            AgentTask(
                agent=t.agent,
                goal=t.goal,
                required_outputs=t.required_outputs,
                section_targets=t.section_targets,
            )
            for t in result.agent_tasks
            if t.agent in agents_to_run
        ]

        # Fill in any missing agent tasks with defaults
        tasked_agents = {t.agent for t in agent_tasks}
        fallback = _default_blueprint(user_query, preferences, agents_to_run, agents_to_skip)
        for ft in fallback.agent_tasks:
            if ft.agent not in tasked_agents and ft.agent in agents_to_run:
                agent_tasks.append(ft)

        return ReportBlueprint(
            title=result.title or "UK Data Centre Site Feasibility Report",
            goal=result.goal or user_query[:150],
            sections=sections,
            agents_to_run=result.agents_to_run or agents_to_run,
            agents_to_skip=result.agents_to_skip or agents_to_skip,
            agent_tasks=agent_tasks,
        )
    except Exception:
        return _default_blueprint(user_query, preferences, agents_to_run, agents_to_skip)
