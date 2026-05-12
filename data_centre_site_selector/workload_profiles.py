from __future__ import annotations

from typing import Any

WORKLOAD_PROFILES: dict[str, str] = {
    "ai_training": "Large batch GPU/HPC training where power, cooling, land, and low-carbon supply dominate.",
    "ai_inference": "User-facing AI serving where latency, resilience, power, and demand proximity matter.",
    "financial_low_latency": "Market-data and trading workloads where network latency and resilience dominate.",
    "enterprise_colocation": "Mixed customer colocation where latency, resilience, power, land, and demand proximity are balanced.",
    "backup_disaster_recovery": "Secondary/DR workloads where resilience and separation from primary hubs dominate.",
}

WORKLOAD_WEIGHT_DIMENSIONS: tuple[str, ...] = (
    "energy",
    "water",
    "climate",
    "latency",
    "resilience",
    "land",
    "planning_risk",
    "population",
    "primary_hub_separation",
)

CORE_WEIGHT_DIMENSIONS: tuple[str, ...] = (
    "energy",
    "water",
    "climate",
    "latency",
    "resilience",
    "land",
    "planning_risk",
)


def workload_profile_options() -> tuple[str, ...]:
    return tuple(WORKLOAD_PROFILES)


def normalise_workload_weights(weights: dict[str, Any]) -> dict[str, float]:
    """Validate and normalise agent-supplied workload weights."""
    cleaned: dict[str, float] = {}
    for key in WORKLOAD_WEIGHT_DIMENSIONS:
        try:
            value = float(weights.get(key, 0.0))
        except (TypeError, ValueError):
            value = 0.0
        if value > 0:
            cleaned[key] = value

    for key in CORE_WEIGHT_DIMENSIONS:
        cleaned.setdefault(key, 0.0)

    if sum(cleaned.values()) <= 0:
        cleaned = {key: 1.0 for key in CORE_WEIGHT_DIMENSIONS}

    total = sum(cleaned.values())
    return {
        key: round(value / total, 4)
        for key, value in cleaned.items()
        if value > 0 or key in CORE_WEIGHT_DIMENSIONS
    }


def heuristic_workload_weights(
    query: str,
    workload: str,
    optimisation_choices: list[str] | None = None,
) -> dict[str, float]:
    """Deterministic fallback for the workload-weight agent.

    The fallback starts from equal core dimensions, then adjusts priorities from
    the selected workload profile and explicit optimisation choices.
    """
    weights = {key: 1.0 for key in CORE_WEIGHT_DIMENSIONS}
    text = f"{query} {' '.join(optimisation_choices or [])}".lower()

    def boost(key: str, amount: float) -> None:
        weights[key] = weights.get(key, 0.0) + amount

    if workload == "ai_training":
        boost("energy", 1.7)
        boost("climate", 1.1)
        boost("land", 0.8)
        boost("water", 0.5)
    elif workload == "ai_inference":
        boost("latency", 1.6)
        boost("resilience", 0.8)
        boost("energy", 0.6)
    elif workload == "financial_low_latency":
        boost("latency", 3.2)
        boost("resilience", 1.2)
        boost("planning_risk", 0.3)
    elif workload == "enterprise_colocation":
        boost("latency", 1.0)
        boost("resilience", 0.8)
        boost("energy", 0.5)
        boost("population", 0.8)
    elif workload == "backup_disaster_recovery":
        boost("resilience", 2.4)
        boost("land", 0.8)
        boost("primary_hub_separation", 1.0)
        boost("planning_risk", 0.6)

    keyword_boosts = {
        "energy": ("power", "grid", "electricity", "renewable", "ppa"),
        "water": ("water", "cooling-water", "abstraction"),
        "climate": ("cooling", "climate", "heat", "carbon", "co2", "emission"),
        "latency": ("latency", "connectivity", "near london", "near users"),
        "resilience": ("resilience", "flood", "availability", "uptime", "risk"),
        "land": ("land", "brownfield", "campus", "site", "planning"),
        "planning_risk": ("planning risk", "permit", "approval", "constraint"),
        "population": ("population", "demand", "customer", "users"),
    }
    for key, keywords in keyword_boosts.items():
        if any(keyword in text for keyword in keywords):
            boost(key, 0.7)

    optimisation_map = {
        "co2": ("energy", "climate"),
        "population_strain": ("water", "population"),
        "political_favour": ("planning_risk",),
        "cost": ("land", "energy"),
        "latency": ("latency",),
        "resilience": ("resilience",),
        "land_use": ("land", "planning_risk"),
        "infrastructure": ("energy", "latency"),
    }
    for choice in optimisation_choices or []:
        for key in optimisation_map.get(choice, ()):
            boost(key, 0.8)

    return normalise_workload_weights(weights)
