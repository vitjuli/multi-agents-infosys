"""Task Dispatcher.

Converts an approved ReportBlueprint into concrete calls to the existing
AgentRunner, enriching each agent's payload with blueprint context and
the agent-specific task. Returns structured AgentOutput objects.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

# Ensure repo root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from data_centre_site_selector.agents import AgentRunner, top_rows_payload
from ..preferences.schemas import AgentOutput, AgentTask, ReportBlueprint

# Short alias → canonical AgentRunner name
_ALIAS_MAP: dict[str, str] = {
    "energy":    "EnergyAgent",
    "water":     "WaterAgent",
    "climate":   "ClimateCoolingAgent",
    "latency":   "LatencyAgent",
    "resilience":"ResilienceAgent",
    "land":      "LandPlanningAgent",
    # Also accept canonical names directly
    "EnergyAgent":          "EnergyAgent",
    "WaterAgent":           "WaterAgent",
    "ClimateCoolingAgent":  "ClimateCoolingAgent",
    "LatencyAgent":         "LatencyAgent",
    "ResilienceAgent":      "ResilienceAgent",
    "LandPlanningAgent":    "LandPlanningAgent",
}

# Default focus text for each agent (matches existing agents.py prompts)
_DEFAULT_FOCUS: dict[str, str] = {
    "EnergyAgent":         "renewable capacity, operational versus pipeline energy, and GSP availability",
    "WaterAgent":          "placeholder water scores and missing water-stress data",
    "ClimateCoolingAgent": "latitude cooling proxy and missing climate data",
    "LatencyAgent":        "distances to data-derived demand hubs and workload latency trade-offs",
    "ResilienceAgent":     "flood-zone flags, missingness, resilience constraints",
    "LandPlanningAgent":   "brownfield land availability and planning risk",
}


def _resolve_agent_name(name: str) -> str | None:
    return _ALIAS_MAP.get(name)


def _raw_to_agent_output(raw: dict[str, Any], task: AgentTask) -> AgentOutput:
    """Convert raw AgentRunner response dict into a typed AgentOutput."""
    key_points = raw.get("key_points", [])
    risks = raw.get("risks", [])
    if isinstance(risks, str):
        risks = [risks]

    # Build minimal claim objects from key_points
    claims = [
        {
            "text": point,
            "category": "finding",
            "decision_relevance": 0.7,
            "risk_severity": 0.0,
            "evidence_strength": 0.6 if raw.get("confidence", "low") != "low" else 0.3,
            "uncertainty_importance": 0.4,
        }
        for point in (key_points if isinstance(key_points, list) else [])
    ]

    uncertainties = [
        item for item in risks
        if any(w in item.lower() for w in ["placeholder", "missing", "uncertain", "heuristic", "proxy"])
    ]
    data_gaps = [
        item for item in risks
        if any(w in item.lower() for w in ["dataset", "data", "missing", "unavailable", "not modelled"])
    ]

    return AgentOutput(
        agent_name=raw.get("agent", task.agent),
        section_targets=task.section_targets,
        claims=claims,
        risks=[r for r in risks if r not in uncertainties],
        uncertainties=uncertainties,
        data_gaps=data_gaps,
        recommendation_impact=raw.get("summary", "")[:300],
        raw=raw,
    )


def run_agents_from_blueprint(
    blueprint: ReportBlueprint,
    runner: AgentRunner,
    user_query: str,
    workload: str,
    ranked: pd.DataFrame,
    top_k: int = 5,
) -> list[AgentOutput]:
    """Call existing specialist agents as directed by the blueprint.

    For each agent in blueprint.agents_to_run:
    - Finds the corresponding AgentTask (or uses defaults)
    - Enriches the payload with blueprint context
    - Calls the existing AgentRunner.run()
    - Converts the response to a typed AgentOutput

    Agents in blueprint.agents_to_skip are not called.
    """
    rows = top_rows_payload(ranked, top_k)
    task_by_agent = {t.agent: t for t in blueprint.agent_tasks}

    outputs: list[AgentOutput] = []
    blueprint_context = {
        "report_goal": blueprint.goal,
        "report_title": blueprint.title,
        "sections": [s.name for s in blueprint.sections],
    }

    for agent_alias in blueprint.agents_to_run:
        canonical = _resolve_agent_name(agent_alias)
        if canonical is None:
            print(f"  [dispatcher] Unknown agent '{agent_alias}' — skipping.", flush=True)
            continue

        task = task_by_agent.get(canonical) or task_by_agent.get(agent_alias)
        if task is None:
            # Construct a minimal default task
            task = AgentTask(
                agent=canonical,
                goal=f"Provide analysis for: {', '.join(s.name for s in blueprint.sections[:3])}",
                required_outputs=["key findings", "risks", "uncertainties"],
                section_targets=[s.name for s in blueprint.sections[:2]],
            )

        payload: dict[str, Any] = {
            "focus": _DEFAULT_FOCUS.get(canonical, "site selection analysis"),
            "rows": rows,
            "blueprint_task": {
                "goal": task.goal,
                "required_outputs": task.required_outputs,
                "section_targets": task.section_targets,
            },
            "blueprint_context": blueprint_context,
            "output_schema": {
                "agent_name": canonical,
                "claims": "list of key findings with evidence",
                "risks": "list of risk strings",
                "uncertainties": "list of data uncertainty notes",
                "data_gaps": "list of missing dataset descriptions",
                "recommendation_impact": "brief string on impact on final recommendation",
            },
        }

        print(f"  Running {canonical}...", flush=True)
        raw = runner.run(canonical, user_query, workload, payload)
        outputs.append(_raw_to_agent_output(raw, task))

    return outputs
