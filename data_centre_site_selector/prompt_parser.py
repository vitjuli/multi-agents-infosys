from __future__ import annotations

import re

from .config import WORKLOAD_WEIGHTS
from .logging_utils import get_logger
from .schemas import UserConstraints


logger = get_logger("prompt")


WORKLOAD_KEYWORDS = {
    "ai_training": ("ai training", "training", "gpu cluster", "gpu", "model training", "hpc"),
    "ai_inference": ("inference", "serving", "llm serving", "real-time ai", "ai service"),
    "financial_low_latency": ("financial", "low latency", "trading", "exchange", "market data"),
    "enterprise_colocation": ("colocation", "colo", "enterprise", "saas", "cloud"),
    "backup_disaster_recovery": ("backup", "disaster recovery", "dr", "resilience", "secondary"),
}

OPTIMISATION_KEYWORDS = {
    "co2": ("co2", "carbon", "emission", "net zero", "renewable", "green"),
    "population_strain": ("water strain", "energy strain", "population", "community", "populus", "water stress"),
    "political_favour": ("political", "planning", "grant", "tax", "policy", "favour", "disfavour"),
    "cost": ("cheap", "cost", "budget", "capex", "opex"),
    "latency": ("latency", "near london", "near users", "connectivity"),
    "resilience": ("flood", "resilience", "risk", "backup", "climate"),
    "land_use": ("brownfield", "land", "site reuse", "planning constraint"),
}

REGION_ALIASES: dict[str, tuple[str, str]] = {
    "uk": ("uk", "uk-wide"),
    "united kingdom": ("uk", "uk-wide"),
    "britain": ("uk", "uk-wide"),
    "england": ("country", "England"),
    "scotland": ("country", "Scotland"),
    "wales": ("country", "Wales"),
    "northern ireland": ("country", "Northern Ireland"),
}

NON_UK_HINTS = ("germany", "france", "republic of ireland", "dublin", "netherlands", "amsterdam", "us", "usa", "america", "europe")

SUGGESTED_CONSTRAINTS = [
    "Target compute capacity in MW or an expected rack/GPU footprint.",
    "Region scope: UK-wide, England, Scotland, Wales, Northern Ireland, or a specific UK city/cluster.",
    "Budget in GBP, ideally separating build capex and annual operating spend.",
    "Optimisation priorities: CO2, water strain, energy strain, latency, resilience, land reuse, policy support, cost.",
    "Hard constraints: flood exclusion, brownfield-only, renewable PPA preference, maximum distance to a major hub.",
]


def parse_budget_gbp(text: str) -> float | None:
    patterns = [
        r"(?:£|gbp\s*)\s*([0-9]+(?:\.[0-9]+)?)\s*(bn|billion|m|million|k|thousand)?",
        r"([0-9]+(?:\.[0-9]+)?)\s*(bn|billion|m|million|k|thousand)\s*(?:gbp|pounds|pound|budget)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if not match:
            continue
        amount = float(match.group(1))
        unit = (match.group(2) or "").lower()
        if unit in {"bn", "billion"}:
            return amount * 1_000_000_000
        if unit in {"m", "million"}:
            return amount * 1_000_000
        if unit in {"k", "thousand"}:
            return amount * 1_000
        return amount
    return None


def parse_compute_mw(text: str) -> float | None:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(mw|megawatt|megawatts)\b", text, re.I)
    return float(match.group(1)) if match else None


def detect_workload(text: str, fallback: str = "ai_training") -> str:
    lowered = text.lower()
    for workload, keywords in WORKLOAD_KEYWORDS.items():
        if any(contains_keyword(lowered, keyword) for keyword in keywords):
            return workload
    return fallback if fallback in WORKLOAD_WEIGHTS else "ai_training"


def detect_region(text: str) -> tuple[str, str | None, str | None]:
    lowered = text.lower()
    invalid = next((hint for hint in NON_UK_HINTS if re.search(rf"\b{re.escape(hint)}\b", lowered)), None)
    matches = sorted(
        ((alias, value) for alias, value in REGION_ALIASES.items() if re.search(rf"\b{re.escape(alias)}\b", lowered)),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    if matches:
        level, label = matches[0][1]
        return level, label, invalid
    return "uk", "UK-wide", invalid


def detect_choices(text: str) -> tuple[list[str], list[str]]:
    lowered = text.lower()
    choices = [key for key, keywords in OPTIMISATION_KEYWORDS.items() if any(contains_keyword(lowered, keyword) for keyword in keywords)]
    policies = [choice for choice in choices if choice in {"political_favour", "land_use", "resilience"}]
    if not choices:
        choices = ["co2", "population_strain", "political_favour", "cost"]
    return choices, policies


def contains_keyword(text: str, keyword: str) -> bool:
    if any(not ch.isalnum() and ch != " " for ch in keyword):
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def parse_user_constraints(
    prompt: str,
    workload: str | None = None,
    budget_gbp: float | None = None,
    region: str | None = None,
    compute_mw: float | None = None,
    optimisation_choices: list[str] | None = None,
) -> UserConstraints:
    combined = " ".join(part for part in [prompt, region or "", " ".join(optimisation_choices or [])] if part)
    region_level, region_text, invalid_region = detect_region(combined)
    if region and region_level == "uk" and region.lower() not in {"uk", "uk-wide", "united kingdom", "britain"}:
        region_level, region_text = "city", region
    choices, policies = detect_choices(combined)
    constraints = UserConstraints(
        prompt=prompt,
        workload=workload or detect_workload(combined),
        compute_mw=compute_mw if compute_mw is not None else parse_compute_mw(combined),
        region_text=region or region_text,
        region_level=region_level,
        budget_gbp=budget_gbp if budget_gbp is not None else parse_budget_gbp(combined),
        optimisation_choices=optimisation_choices or choices,
        policy_constraints=policies,
        invalid_region=invalid_region,
    )
    if constraints.compute_mw is None:
        constraints.unspecified_fields.append("compute_mw")
    if constraints.budget_gbp is None:
        constraints.unspecified_fields.append("budget_gbp")
    if not constraints.region_text:
        constraints.unspecified_fields.append("region")
        constraints.region_text = "UK-wide"
    constraints.suggested_constraints = SUGGESTED_CONSTRAINTS
    logger.debug("Parsed user constraints from prompt=%r result=%s.", prompt, constraints.to_dict())
    return constraints
