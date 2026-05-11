from __future__ import annotations

from typing import Any

import pandas as pd

from .geo_utils import clamp
from .logging_utils import get_logger
from .policy import policy_score
from .schemas import SearchStage, UserConstraints
from .scoring import score_for_workload

"""CAM'S COMMENTS:
data\_analysis.py

   * production scores and formulas???
   * where does the metadata go from add\_metadata? What is the data alteration pipeline here?
   * What are all the scores? 
   * Hardcoded production\_score weights?

"""
logger = get_logger("analysis")


def _linear(value: float, low: float, high: float, invert: bool = False) -> float:
    if pd.isna(value) or high <= low:
        return 5.0
    score = 10 * (float(value) - low) / (high - low)
    if invert:
        score = 10 - score
    return clamp(score)


def json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def add_metadata(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "alt_m" not in out:
        out["alt_m"] = pd.NA
    if "country" not in out:
        out["country"] = "United Kingdom"
    if "aliases" not in out:
        out["aliases"] = out["region"].astype(str).str.lower()
    return out


def add_production_scores(
    df: pd.DataFrame, constraints: UserConstraints
) -> pd.DataFrame:
    logger.debug(
        "Adding production scores rows=%s workload=%s optimise=%s.",
        len(df),
        constraints.workload,
        constraints.optimisation_choices,
    )
    out = score_for_workload(add_metadata(df), constraints.workload)
    cap = out["renewable_capacity_50km_mw"].fillna(0)
    op = out["operational_renewable_capacity_50km_mw"].fillna(0)
    population = out["population_lad"].fillna(out["population_lad"].median())
    brownfield = out["brownfield_hectares_50km"].fillna(0)
    gsp_distance = out["nearest_gsp_distance_km"].fillna(
        out["nearest_gsp_distance_km"].median()
    )

    out["co2_score_raw"] = (
        0.50 * out["energy_score_raw"]
        + 0.35 * op.map(lambda v: _linear(v, 0, max(250, op.quantile(0.9))))
        + 0.15 * cap.map(lambda v: _linear(v, 0, max(500, cap.quantile(0.9))))
    ).map(clamp)
    out["emissions_intensity_proxy_kgco2e_per_mwh"] = (
        280 - (out["co2_score_raw"] * 18)
    ).map(lambda v: max(65.0, v))
    out["population_strain_score_raw"] = (
        0.55 * out["water_score_raw"]
        + 0.25
        * population.map(
            lambda v: _linear(v, population.min(), population.max(), invert=True)
        )
        + 0.20 * out["resilience_score_raw"]
    ).map(clamp)
    out["political_favour_score_raw"] = out.apply(
        lambda row: policy_score(row["region"], row.get("country")), axis=1
    )
    out["infrastructure_score_raw"] = (
        0.45 * out["energy_score_raw"]
        + 0.25 * out["latency_score_raw"]
        + 0.20
        * gsp_distance.map(
            lambda v: _linear(v, 0, max(20, gsp_distance.quantile(0.9)), invert=True)
        )
        + 0.10
        * brownfield.map(lambda v: _linear(v, 0, max(50, brownfield.quantile(0.9))))
    ).map(clamp)
    out["land_use_score_raw"] = (
        0.75 * out["land_score_raw"]
        + 0.25
        * brownfield.map(lambda v: _linear(v, 0, max(50, brownfield.quantile(0.9))))
    ).map(clamp)
    out["estimated_capex_per_mw_gbp"] = out.apply(estimate_capex_per_mw, axis=1)
    capex = out["estimated_capex_per_mw_gbp"]
    out["cost_score_raw"] = capex.map(
        lambda v: _linear(v, capex.min(), capex.max(), invert=True)
    )
    out["production_score"] = production_score(out, constraints)
    out = out.sort_values("production_score", ascending=False).reset_index(drop=True)
    logger.debug(
        "Production scoring complete top=%s.",
        out[
            [
                "region",
                "production_score",
                "co2_score_raw",
                "population_strain_score_raw",
                "cost_score_raw",
            ]
        ]
        .head(5)
        .to_dict(orient="records"),
    )
    return out


def estimate_capex_per_mw(row: pd.Series) -> float:
    base = 8_500_000.0
    land_adjustment = (5.0 - float(row.get("land_score_raw", 5.0))) * 180_000
    infrastructure_adjustment = (
        5.0 - float(row.get("infrastructure_score_raw", 5.0))
    ) * 220_000
    return max(6_500_000.0, base + land_adjustment + infrastructure_adjustment)


def production_score(df: pd.DataFrame, constraints: UserConstraints) -> pd.Series:
    weights = {
        "co2": 0.22,
        "population_strain": 0.18,
        "political_favour": 0.16,
        "cost": 0.12,
        "latency": 0.10,
        "resilience": 0.10,
        "land_use": 0.08,
        "infrastructure": 0.14,
    }
    requested = set(constraints.optimisation_choices)
    if requested:
        for key in list(weights):
            weights[key] *= 1.35 if key in requested else 0.80
    numerator = (
        weights["co2"] * df["co2_score_raw"]
        + weights["population_strain"] * df["population_strain_score_raw"]
        + weights["political_favour"] * df["political_favour_score_raw"]
        + weights["cost"] * df["cost_score_raw"]
        + weights["latency"] * df["latency_score_raw"]
        + weights["resilience"] * df["resilience_score_raw"]
        + weights["land_use"] * df["land_use_score_raw"]
        + weights["infrastructure"] * df["infrastructure_score_raw"]
        + 0.18 * df["overall_score"]
    )
    return (numerator / (sum(weights.values()) + 0.18)).map(clamp)


def filter_for_scope(df: pd.DataFrame, constraints: UserConstraints) -> pd.DataFrame:
    if (
        constraints.region_level == "uk"
        or not constraints.region_text
        or constraints.region_text == "UK-wide"
    ):
        return df.copy()
    if constraints.region_level == "country":
        return df[
            df["country"].str.lower() == str(constraints.region_text).lower()
        ].copy()
    return df[df["region"].str.lower() == str(constraints.region_text).lower()].copy()


def top_region_records(df: pd.DataFrame, top_k: int) -> list[dict[str, Any]]:
    keep = [
        "region",
        "country",
        "lat",
        "lon",
        "alt_m",
        "production_score",
        "overall_score",
        "co2_score_raw",
        "population_strain_score_raw",
        "political_favour_score_raw",
        "cost_score_raw",
        "infrastructure_score_raw",
        "renewable_capacity_50km_mw",
        "brownfield_hectares_50km",
        "estimated_capex_per_mw_gbp",
    ]
    records = df.head(top_k)[[key for key in keep if key in df.columns]].to_dict(
        orient="records"
    )
    return [
        {key: json_value(row.get(key)) for key in keep if key in row} for row in records
    ]


def nested_search(
    features: pd.DataFrame, constraints: UserConstraints, top_k: int
) -> tuple[pd.DataFrame, list[SearchStage]]:
    scored = add_production_scores(features, constraints)
    logger.debug(
        "Nested search started level=%s region=%s total_candidates=%s.",
        constraints.region_level,
        constraints.region_text,
        len(scored),
    )
    stages = [
        SearchStage(
            level="uk",
            label="UK-wide screening",
            candidate_count=len(scored),
            criteria=[
                "CO2 proxy",
                "population water/energy strain",
                "policy favour",
                "cost",
                "infrastructure",
                "land reuse",
            ],
            top_regions=top_region_records(scored, top_k),
        )
    ]
    scoped = scored
    if constraints.region_level in {"country", "city"}:
        country_label = constraints.region_text
        if constraints.region_level == "city":
            match = scored[
                scored["region"].str.lower() == str(constraints.region_text).lower()
            ]
            country_label = (
                match.iloc[0]["country"] if len(match) else constraints.region_text
            )
        country_df = scored[
            scored["country"].str.lower() == str(country_label).lower()
        ].copy()
        stages.append(
            SearchStage(
                level="country",
                label=f"{country_label} screening",
                candidate_count=len(country_df),
                criteria=[
                    "national policy fit",
                    "grid and renewable capacity",
                    "land/planning risk",
                ],
                top_regions=top_region_records(country_df, top_k),
                blocked_reason=(
                    None
                    if len(country_df)
                    else f"No cached candidate regions for {country_label}."
                ),
            )
        )
        scoped = country_df
        logger.debug(
            "Country scoped candidates label=%s count=%s.",
            country_label,
            len(country_df),
        )
    if constraints.region_level == "city":
        scoped = filter_for_scope(scored, constraints)
        logger.debug(
            "Local scoped candidates label=%s count=%s.",
            constraints.region_text,
            len(scoped),
        )
        stages.append(
            SearchStage(
                level="city",
                label=f"{constraints.region_text} site-cluster screening",
                candidate_count=len(scoped),
                criteria=[
                    "local infrastructure",
                    "site-level policy eligibility",
                    "cost feasibility",
                    "community strain",
                ],
                top_regions=top_region_records(scoped, top_k),
                blocked_reason=(
                    None
                    if len(scoped)
                    else f"No cached candidate region for {constraints.region_text}."
                ),
            )
        )
    scoped = scoped.reset_index(drop=True)
    logger.debug(
        "Nested search complete scoped_count=%s stages=%s.",
        len(scoped),
        [stage.label for stage in stages],
    )
    return scoped, stages
