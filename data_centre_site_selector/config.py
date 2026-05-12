from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

"""CAM'S COMMENTS:
config.py

   * candidate regions are hardcoded. Coordinates are extremely specific.
   * HUBS??? What are they?
   * Workload weights are hardcoded? What do they all even mean there is a category for each section but what does any of this mean?

"""


def load_environment() -> None:
    """Load repo-local .env values when python-dotenv is available."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")


load_environment()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
FAST_MODEL = os.getenv("OPENAI_MODEL_FAST", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
REASONING_MODEL = os.getenv(
    "OPENAI_MODEL_REASONING", os.getenv("OPENAI_MODEL", "gpt-4o")
)
WEB_MODEL = os.getenv("OPENAI_MODEL_WEB", REASONING_MODEL)


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
        "primary_hub_separation": 0.12,
    },
}


@dataclass(frozen=True)
class DataHub:
    name: str
    lat: float
    lon: float
    note: str


# Fixed list of UK commercial datacentre / fibre-interchange clusters.
# First entry is the "primary" used by the backup_disaster_recovery workload's
# primary_hub_separation term.
UK_DATA_HUBS: tuple[DataHub, ...] = (
    DataHub("Slough",           51.5105, -0.5950, "M4 corridor; Equinix LD4/5/6, Virtus, Yondr cluster"),
    DataHub("London Docklands", 51.5101, -0.0049, "Telehouse North/East/West, Equinix LD8; Coriander Avenue E14"),
    DataHub("Manchester",       53.4794, -2.2453, "MA1 internet exchange and northern colo cluster"),
    DataHub("Edinburgh",        55.9533, -3.1883, "Scottish anchor; iomart, Pulsant, subsea-cable landings"),
    DataHub("Cardiff",          51.4816, -3.1791, "Welsh anchor; Next Generation Data ~25 km NE in Newport"),
)
