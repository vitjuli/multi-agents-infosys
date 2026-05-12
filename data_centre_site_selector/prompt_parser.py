from __future__ import annotations

import re

from .logging_utils import get_logger
from .schemas import UserConstraints
from .workload_profiles import WORKLOAD_PROFILES

"""CAM'S COMMENTS:
prompt\_parset.py

    * how should we choose the keywords
    * Non\_UK\_Hints, i.e. a list of other countries? lol. Don't we ideally just want it to stick to the country given? Shouldn't hardcode all countries surely to check we are asking for the UK (if we are constraining to that).
    * Suggested constraints?
"""

logger = get_logger("prompt")


WORKLOAD_KEYWORDS = {
    "ai_training": (
        "ai training",
        "training",
        "gpu cluster",
        "gpu",
        "model training",
        "hpc",
    ),
    "ai_inference": (
        "inference",
        "serving",
        "llm serving",
        "real-time ai",
        "ai service",
    ),
    "financial_low_latency": (
        "financial",
        "low latency",
        "trading",
        "exchange",
        "market data",
    ),
    "enterprise_colocation": ("colocation", "colo", "enterprise", "saas", "cloud"),
    "backup_disaster_recovery": (
        "backup",
        "disaster recovery",
        "dr",
        "resilience",
        "secondary",
    ),
}

OPTIMISATION_KEYWORDS = {
    "co2": ("co2", "carbon", "emission", "net zero", "renewable", "green"),
    "population_strain": (
        "water strain",
        "energy strain",
        "population",
        "community",
        "populus",
        "water stress",
    ),
    "political_favour": (
        "political",
        "planning",
        "grant",
        "tax",
        "policy",
        "favour",
        "disfavour",
    ),
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

NON_UK_HINTS = (
    "germany",
    "france",
    "republic of ireland",
    "dublin",
    "netherlands",
    "amsterdam",
    "us",
    "usa",
    "america",
    "europe",
)

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


def parse_radius_miles(text: str) -> tuple[float, str] | None:
    patterns = [
        r"within\s+([0-9]+(?:\.[0-9]+)?)\s*(mile|miles|mi|km|kilometre|kilometres|kilometer|kilometers)\s+of\s+([a-z][a-z\s\-']+)",
        r"around\s+([a-z][a-z\s\-']+)\s+within\s+([0-9]+(?:\.[0-9]+)?)\s*(mile|miles|mi|km|kilometre|kilometres|kilometer|kilometers)",
    ]
    lowered = text.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered, re.I)
        if not match:
            continue
        if pattern.startswith("within"):
            amount = float(match.group(1))
            unit = match.group(2).lower()
            location = match.group(3).strip(" .,\n\t")
        else:
            location = match.group(1).strip(" .,\n\t")
            amount = float(match.group(2))
            unit = match.group(3).lower()
        miles = amount * 0.621371 if unit.startswith("km") or unit.startswith("kilo") else amount
        return miles, location.title()
    return None


def detect_workload(text: str, fallback: str = "ai_training") -> str:
    lowered = text.lower()
    for workload, keywords in WORKLOAD_KEYWORDS.items():
        if any(contains_keyword(lowered, keyword) for keyword in keywords):
            return workload
    return fallback if fallback in WORKLOAD_PROFILES else "ai_training"


def detect_region(text: str) -> tuple[str, str | None, str | None]:
    lowered = text.lower()
    invalid = next(
        (
            hint
            for hint in NON_UK_HINTS
            if re.search(rf"\b{re.escape(hint)}\b", lowered)
        ),
        None,
    )
    matches = sorted(
        (
            (alias, value)
            for alias, value in REGION_ALIASES.items()
            if re.search(rf"\b{re.escape(alias)}\b", lowered)
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    if matches:
        level, label = matches[0][1]
        return level, label, invalid
    return "uk", "UK-wide", invalid


def detect_choices(text: str) -> tuple[list[str], list[str]]:
    lowered = text.lower()
    choices = [
        key
        for key, keywords in OPTIMISATION_KEYWORDS.items()
        if any(contains_keyword(lowered, keyword) for keyword in keywords)
    ]
    policies = [
        choice
        for choice in choices
        if choice in {"political_favour", "land_use", "resilience"}
    ]
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
    target_location: str | None = None,
    target_radius_miles: float | None = None,
    compute_mw: float | None = None,
    optimisation_choices: list[str] | None = None,
) -> UserConstraints:
    combined = " ".join(
        part
        for part in [prompt, region or "", " ".join(optimisation_choices or [])]
        if part
    )
    parsed_radius = parse_radius_miles(combined)
    region_level, region_text, invalid_region = detect_region(combined)
    derived_target_location = target_location
    derived_target_radius_miles = target_radius_miles
    if parsed_radius and not target_location and target_radius_miles is None:
        derived_target_radius_miles, derived_target_location = parsed_radius
        region_level = "radius"
        region_text = (
            f"within {derived_target_radius_miles:.0f} miles of {derived_target_location}"
        )
    if (
        region
        and region_level == "uk"
        and region.lower() not in {"uk", "uk-wide", "united kingdom", "britain"}
    ):
        region_level, region_text = "city", region
    if derived_target_location and derived_target_radius_miles is not None:
        region_level = "radius"
        region_text = (
            f"within {derived_target_radius_miles:.0f} miles of {derived_target_location}"
        )
    elif derived_target_location and not region:
        region_level = "city"
        region_text = derived_target_location
    chosen_region_text = region_text
    if region and derived_target_location is None:
        chosen_region_text = region
    choices, policies = detect_choices(combined)
    constraints = UserConstraints(
        prompt=prompt,
        workload=workload or detect_workload(combined),
        compute_mw=compute_mw if compute_mw is not None else parse_compute_mw(combined),
        region_text=chosen_region_text,
        region_level=region_level,
        target_location=derived_target_location,
        target_radius_miles=derived_target_radius_miles,
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
    logger.debug(
        "Parsed user constraints from prompt=%r result=%s.",
        prompt,
        constraints.to_dict(),
    )
    return constraints
