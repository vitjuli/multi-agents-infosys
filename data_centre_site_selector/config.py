from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


@dataclass(frozen=True)
class CandidateRegion:
    region: str
    lat: float
    lon: float
    workload_hint: str = ""
    lad_name_hint: str | None = None


CANDIDATE_REGIONS: list[CandidateRegion] = [
    CandidateRegion("Slough / West London", 51.5105, -0.5950, "low-latency west London data-centre cluster", "Slough"),
    CandidateRegion("Manchester", 53.4808, -2.2426, "northern enterprise and connectivity hub", "Manchester"),
    CandidateRegion("Birmingham / West Midlands", 52.4862, -1.8904, "central UK connectivity and enterprise hub", "Birmingham"),
    CandidateRegion("Teesside / North East England", 54.5742, -1.2348, "industrial energy transition cluster", "Middlesbrough"),
    CandidateRegion("Edinburgh / Central Scotland", 55.9533, -3.1883, "cooler climate and Scottish enterprise hub", "Edinburgh"),
    CandidateRegion("Cardiff / South Wales", 51.4816, -3.1791, "South Wales connectivity and energy corridor", "Cardiff"),
    CandidateRegion("Bristol / South West England", 51.4545, -2.5879, "western connectivity and regional demand hub", "Bristol"),
    CandidateRegion("Leeds / Yorkshire", 53.8008, -1.5491, "Yorkshire enterprise and regional demand hub", "Leeds"),
]


HUBS = {
    "London": (51.5074, -0.1278),
    "Manchester": (53.4808, -2.2426),
    "Birmingham": (52.4862, -1.8904),
}


WORKLOAD_WEIGHTS: dict[str, dict[str, float]] = {
    "ai_training": {
        "energy": 0.28,
        "water": 0.14,
        "climate": 0.20,
        "latency": 0.06,
        "resilience": 0.12,
        "land": 0.16,
        "planning_risk": 0.10,
    },
    "ai_inference": {
        "energy": 0.20,
        "water": 0.10,
        "climate": 0.10,
        "latency": 0.22,
        "resilience": 0.16,
        "land": 0.12,
        "planning_risk": 0.10,
    },
    "financial_low_latency": {
        "energy": 0.14,
        "water": 0.05,
        "climate": 0.05,
        "latency": 0.42,
        "resilience": 0.18,
        "land": 0.06,
        "planning_risk": 0.10,
    },
    "enterprise_colocation": {
        "energy": 0.18,
        "water": 0.08,
        "climate": 0.08,
        "latency": 0.22,
        "resilience": 0.18,
        "land": 0.12,
        "planning_risk": 0.10,
        "population": 0.10,
    },
    "backup_disaster_recovery": {
        "energy": 0.16,
        "water": 0.08,
        "climate": 0.10,
        "latency": 0.10,
        "resilience": 0.34,
        "land": 0.16,
        "planning_risk": 0.12,
        "london_separation": 0.12,
    },
}
