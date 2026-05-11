from __future__ import annotations

import json
import os
import time
from typing import Any

from openai import OpenAI

from .config import DEFAULT_MODEL


AGENT_NAMES = [
    "EnergyAgent",
    "WaterAgent",
    "ClimateCoolingAgent",
    "LatencyAgent",
    "ResilienceAgent",
    "LandPlanningAgent",
]


def fallback(agent: str, reason: str) -> dict[str, Any]:
    return {
        "agent": agent,
        "summary": f"Deterministic fallback used: {reason}",
        "key_points": ["numeric scoring available", "model explanation unavailable"],
        "risks": ["Review computed features and placeholder assumptions manually."],
        "confidence": "low",
    }


def parse_agent_json(text: str, agent: str) -> dict[str, Any]:
    try:
        start = text.find("{")
        end = text.rfind("}")
        payload = text[start : end + 1] if start >= 0 and end > start else text
        parsed = json.loads(payload)
        if isinstance(parsed, dict):
            parsed.setdefault("agent", agent)
            parsed.setdefault("key_points", [])
            parsed.setdefault("risks", [])
            parsed.setdefault("confidence", "medium")
            return parsed
    except Exception:
        pass
    return {"agent": agent, "summary": text, "key_points": [], "risks": ["JSON parsing failed."], "confidence": "low"}


class AgentRunner:
    def __init__(self, model: str = DEFAULT_MODEL, max_retries: int = 1, timeout: float = 8.0, enabled: bool | None = None) -> None:
        self.model = model
        self.max_retries = max_retries
        self.disabled_reason = "OPENAI_API_KEY is not set"
        if enabled is None:
            self.enabled = bool(os.getenv("OPENAI_API_KEY"))
        else:
            self.enabled = enabled and bool(os.getenv("OPENAI_API_KEY"))
            self.disabled_reason = "OpenAI agents disabled by CLI flag" if not enabled else self.disabled_reason
        self.client = OpenAI(timeout=timeout) if self.enabled else None

    def run(self, agent: str, query: str, workload: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled or self.client is None:
            return fallback(agent, self.disabled_reason)
        system = (
            f"You are {agent}, a specialist data-centre site-selection analyst. "
            "Explain computed scores; do not invent missing data. Distinguish computed facts from heuristics. "
            "Return strict JSON with keys: agent, summary, key_points, risks, confidence."
        )
        user = {
            "query": query,
            "workload": workload,
            "agent": agent,
            "features": payload,
        }
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": json.dumps(user, default=str)},
                    ],
                )
                text = response.choices[0].message.content or ""
                return parse_agent_json(text, agent)
            except Exception as exc:
                last_error = exc
                time.sleep(0.5 * (attempt + 1))
        return fallback(agent, f"model call failed: {last_error}")


def top_rows_payload(ranked, top_k: int = 5) -> list[dict[str, Any]]:
    records = ranked.head(top_k).replace({float("nan"): None}).to_dict(orient="records")
    keep = [
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
        "operational_renewable_capacity_50km_mw",
        "pipeline_renewable_capacity_50km_mw",
        "brownfield_hectares_50km",
        "nearest_major_hub_distance_km",
        "distance_to_london_km",
        "flood_zone_2_intersects",
        "flood_zone_3_intersects",
        "flood_zone_overlap_warning",
        "data_quality_notes",
    ]
    return [{k: row.get(k) for k in keep if k in row} for row in records]


def run_specialist_agents(runner: AgentRunner, query: str, workload: str, ranked, top_k: int) -> list[dict[str, Any]]:
    rows = top_rows_payload(ranked, top_k)
    prompts = {
        "EnergyAgent": {"focus": "renewable capacity, operational versus pipeline energy, and GSP availability", "rows": rows},
        "WaterAgent": {"focus": "placeholder water scores and missing water-stress data", "rows": rows},
        "ClimateCoolingAgent": {"focus": "latitude cooling proxy and missing climate data", "rows": rows},
        "LatencyAgent": {"focus": "distances to London, Manchester, Birmingham and workload latency trade-offs", "rows": rows},
        "ResilienceAgent": {"focus": "flood-zone flags, missingness, resilience constraints", "rows": rows},
        "LandPlanningAgent": {"focus": "brownfield land availability and planning risk", "rows": rows},
    }
    return [runner.run(agent, query, workload, prompts[agent]) for agent in AGENT_NAMES]


def run_critic(runner: AgentRunner, query: str, workload: str, ranked, agent_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {
        "ranked_table": top_rows_payload(ranked, 8),
        "agent_summaries": agent_summaries,
        "instruction": "Identify weaknesses, missing datasets, overconfident assumptions, and next datasets to add.",
    }
    return runner.run("CriticAgent", query, workload, payload)


def run_synthesis(runner: AgentRunner, query: str, workload: str, ranked, agent_summaries: list[dict[str, Any]], critic: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "ranked_table": top_rows_payload(ranked, 8),
        "agent_summaries": agent_summaries,
        "critic": critic,
        "instruction": "Produce a final recommendation report grounded in the deterministic ranking.",
    }
    return runner.run("SynthesisAgent", query, workload, payload)
