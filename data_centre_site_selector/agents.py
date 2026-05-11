from __future__ import annotations

import json
import os
import time
from typing import Any

import pandas as pd
from openai import OpenAI

from .config import (
    DEFAULT_MODEL,
    FAST_MODEL,
    REASONING_MODEL,
    WEB_MODEL,
    load_environment,
)
from .logging_utils import get_logger

"""CAM'S COMMENTS:
agents.py

   * parse\_agent\_json??
   * could improve the initialisation prompts?


"""

AGENT_NAMES = [
    "EnergyAgent",
    "WaterAgent",
    "ClimateCoolingAgent",
    "LatencyAgent",
    "ResilienceAgent",
    "LandPlanningAgent",
]

REASONING_AGENTS = {
    "CriticAgent",
    "SynthesisAgent",
    "PlannerCriticAgent",
    "ExplainerAgent",
}
WEB_RESEARCH_AGENTS = {"PolicyResearchAgent", "GrantResearchAgent"}


logger = get_logger("agents")


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
            if isinstance(parsed.get("key_points"), dict):
                parsed["key_points"] = [
                    f"{key}: {value}" for key, value in parsed["key_points"].items()
                ]
            elif isinstance(parsed.get("key_points"), str):
                parsed["key_points"] = [parsed["key_points"]]
            if isinstance(parsed.get("risks"), dict):
                parsed["risks"] = [
                    f"{key}: {value}" for key, value in parsed["risks"].items()
                ]
            elif isinstance(parsed.get("risks"), str):
                parsed["risks"] = [parsed["risks"]]
            return parsed
    except Exception:
        pass
    return {
        "agent": agent,
        "summary": text,
        "key_points": [],
        "risks": ["JSON parsing failed."],
        "confidence": "low",
    }


class AgentRunner:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_retries: int = 1,
        timeout: float = 45.0,
        enabled: bool | None = None,
        fast_model: str = FAST_MODEL,
        reasoning_model: str = REASONING_MODEL,
        web_model: str = WEB_MODEL,
        enable_web: bool = False,
    ) -> None:
        load_environment()
        self.model = model
        self.fast_model = fast_model
        self.reasoning_model = reasoning_model
        self.web_model = web_model
        self.enable_web = enable_web
        self.max_retries = max_retries
        self.disabled_reason = "OPENAI_API_KEY is not set"
        if enabled is None:
            self.enabled = bool(os.getenv("OPENAI_API_KEY"))
        else:
            self.enabled = enabled and bool(os.getenv("OPENAI_API_KEY"))
            self.disabled_reason = (
                "OpenAI agents disabled by CLI flag"
                if not enabled
                else self.disabled_reason
            )
        self.client = OpenAI(timeout=timeout) if self.enabled else None

    def model_for_agent(self, agent: str) -> str:
        if agent in WEB_RESEARCH_AGENTS:
            return self.web_model
        if agent in REASONING_AGENTS:
            return self.reasoning_model or self.model
        return self.fast_model or self.model

    def run(
        self, agent: str, query: str, workload: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if not self.enabled or self.client is None:
            logger.info(
                "%s: using deterministic fallback (%s).", agent, self.disabled_reason
            )
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
        selected_model = self.model_for_agent(agent)
        logger.info("%s: calling OpenAI model '%s'.", agent, selected_model)
        logger.debug("%s payload keys=%s.", agent, list(payload.keys()))
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=selected_model,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": json.dumps(user, default=str)},
                    ],
                )
                text = response.choices[0].message.content or ""
                logger.info("%s: received model response.", agent)
                logger.debug("%s response chars=%s.", agent, len(text))
                return parse_agent_json(text, agent)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "%s: model call attempt %s failed: %s.", agent, attempt + 1, exc
                )
                time.sleep(0.5 * (attempt + 1))
        logger.info("%s: using deterministic fallback after model failure.", agent)
        return fallback(agent, f"model call failed: {last_error}")

    def run_web_research(self, query: str, payload: dict[str, Any]) -> dict[str, Any]:
        agent = "PolicyResearchAgent"
        if not self.enable_web:
            return fallback(agent, "web research disabled")
        if not self.enabled or self.client is None:
            logger.info(
                "%s: using deterministic fallback (%s).", agent, self.disabled_reason
            )
            return fallback(agent, self.disabled_reason)
        if not hasattr(self.client, "responses"):
            return fallback(
                agent, "installed OpenAI client does not expose the Responses API"
            )
        request = {
            "query": query,
            "policy_context": payload,
            "instruction": (
                "Search the web for current UK government policy, grants, tax reliefs, planning support, "
                "AI Growth Zones, Investment Zones, and Freeport incentives relevant to data-centre site selection. "
                "Prefer official UK government sources. Return strict JSON with keys: agent, summary, key_points, risks, confidence, sources."
            ),
        }
        last_error = None
        selected_model = self.model_for_agent(agent)
        logger.info(
            "%s: calling OpenAI model '%s' with web search.", agent, selected_model
        )
        logger.debug("%s web payload keys=%s.", agent, list(payload.keys()))
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.responses.create(
                    model=selected_model,
                    tools=[{"type": "web_search_preview"}],
                    input=json.dumps(request, default=str),
                    temperature=0.2,
                )
                text = getattr(response, "output_text", "") or ""
                parsed = parse_agent_json(text, agent)
                parsed.setdefault("sources", [])
                logger.debug(
                    "%s web response chars=%s sources=%s.",
                    agent,
                    len(text),
                    len(parsed.get("sources", [])),
                )
                return parsed
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "%s: web model call attempt %s failed: %s.", agent, attempt + 1, exc
                )
                time.sleep(0.5 * (attempt + 1))
        return fallback(agent, f"web model call failed: {last_error}")


def top_rows_payload(ranked, top_k: int = 5) -> list[dict[str, Any]]:
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
        "primary_hub_distance_km",
        "flood_zone_2_intersects",
        "flood_zone_3_intersects",
        "flood_zone_overlap_warning",
        "data_quality_notes",
    ]
    records = ranked.head(top_k)[[k for k in keep if k in ranked.columns]].to_dict(
        orient="records"
    )
    return [
        {k: (None if pd.isna(row.get(k)) else row.get(k)) for k in keep if k in row}
        for row in records
    ]


def run_specialist_agents(
    runner: AgentRunner, query: str, workload: str, ranked, top_k: int
) -> list[dict[str, Any]]:
    rows = top_rows_payload(ranked, top_k)
    prompts = {
        "EnergyAgent": {
            "focus": "renewable capacity, operational versus pipeline energy, and GSP availability",
            "rows": rows,
        },
        "WaterAgent": {
            "focus": "placeholder water scores and missing water-stress data",
            "rows": rows,
        },
        "ClimateCoolingAgent": {
            "focus": "latitude cooling proxy and missing climate data",
            "rows": rows,
        },
        "LatencyAgent": {
            "focus": "distances to data-derived demand hubs and workload latency trade-offs",
            "rows": rows,
        },
        "ResilienceAgent": {
            "focus": "flood-zone flags, missingness, resilience constraints",
            "rows": rows,
        },
        "LandPlanningAgent": {
            "focus": "brownfield land availability and planning risk",
            "rows": rows,
        },
    }
    return [runner.run(agent, query, workload, prompts[agent]) for agent in AGENT_NAMES]


def run_critic(
    runner: AgentRunner,
    query: str,
    workload: str,
    ranked,
    agent_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = {
        "ranked_table": top_rows_payload(ranked, 8),
        "agent_summaries": agent_summaries,
        "instruction": "Identify weaknesses, missing datasets, overconfident assumptions, and next datasets to add.",
    }
    return runner.run("CriticAgent", query, workload, payload)


def run_synthesis(
    runner: AgentRunner,
    query: str,
    workload: str,
    ranked,
    agent_summaries: list[dict[str, Any]],
    critic: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "ranked_table": top_rows_payload(ranked, 8),
        "agent_summaries": agent_summaries,
        "critic": critic,
        "instruction": "Produce a final recommendation report grounded in the deterministic ranking.",
    }
    return runner.run("SynthesisAgent", query, workload, payload)
