from __future__ import annotations

import pandas as pd

from .config import WORKLOAD_WEIGHTS
from .geo_utils import clamp, haversine_km
from .logging_utils import get_logger


logger = get_logger("scoring")


def _linear(value: float, low: float, high: float) -> float:
    if pd.isna(value):
        return 5.0
    if high <= low:
        return 5.0
    return clamp(10 * (float(value) - low) / (high - low))


def data_derived_hubs(df: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    usable = df.dropna(subset=["lat", "lon"]).copy()
    if usable.empty:
        return usable
    if "population_lad" in usable:
        usable["_hub_weight"] = pd.to_numeric(usable["population_lad"], errors="coerce").fillna(0)
    else:
        usable["_hub_weight"] = 0
    if usable["_hub_weight"].sum() == 0:
        usable["_hub_weight"] = usable["renewable_project_count_50km"].fillna(0) if "renewable_project_count_50km" in usable else 1
    return usable.sort_values("_hub_weight", ascending=False).head(top_n)


def add_raw_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    logger.debug("Adding raw scores rows=%s columns=%s.", len(out), list(out.columns))
    cap = out["renewable_capacity_50km_mw"].fillna(0)
    op = out["operational_renewable_capacity_50km_mw"].fillna(0)
    pipe = out["pipeline_renewable_capacity_50km_mw"].fillna(0)
    cap_score = cap.map(lambda v: _linear(v, 0, max(500, cap.quantile(0.9))))
    op_score = op.map(lambda v: _linear(v, 0, max(250, op.quantile(0.9))))
    pipe_score = pipe.map(lambda v: _linear(v, 0, max(250, pipe.quantile(0.9))))
    gsp_bonus = out["gsp_region"].notna().astype(float) * 0.8
    out["energy_score_raw"] = (0.55 * cap_score + 0.25 * op_score + 0.20 * pipe_score + gsp_bonus).map(clamp)

    pop = pd.to_numeric(out.get("population_lad", pd.Series(index=out.index)), errors="coerce")
    if pop.notna().any():
        pop_score = pop.fillna(pop.median()).map(lambda v: _linear(v, pop.min(), pop.max()))
    else:
        pop_score = pd.Series(5.0, index=out.index)
    out["water_score_raw"] = (7.5 - 2.0 * (pop_score / 10)).map(clamp)
    out["water_score_note"] = "placeholder population-pressure heuristic; replace with water-stress and abstraction/licensing datasets"

    min_lat, max_lat = out["lat"].min(), out["lat"].max()
    out["climate_score_raw"] = out["lat"].map(lambda v: _linear(v, min_lat, max_lat))
    out["climate_score_note"] = "placeholder latitude cooling proxy; replace with HadUK-Grid or equivalent climate data"

    hubs = data_derived_hubs(out)
    logger.debug("Data-derived hubs selected=%s.", hubs[["region", "population_lad", "lat", "lon"]].to_dict(orient="records") if len(hubs) else [])
    hub_distance_cols = []
    for idx, hub in hubs.reset_index(drop=True).iterrows():
        col = f"distance_to_data_hub_{idx + 1}_km"
        out[col] = out.apply(lambda r: haversine_km(r["lat"], r["lon"], hub["lat"], hub["lon"]), axis=1)
        hub_distance_cols.append(col)
    out["nearest_major_hub_distance_km"] = out[hub_distance_cols].min(axis=1) if hub_distance_cols else 250.0
    out["primary_hub_distance_km"] = out[hub_distance_cols[0]] if hub_distance_cols else out["nearest_major_hub_distance_km"]
    out["latency_score_raw"] = out["nearest_major_hub_distance_km"].map(lambda d: clamp(10 - (d / 45)))

    z2 = out["flood_zone_2_intersects"].fillna(False).astype(bool)
    z3 = out["flood_zone_3_intersects"].fillna(False).astype(bool)
    missing_flood = out["flood_zone_2_intersects"].isna() | out["flood_zone_3_intersects"].isna()
    out["resilience_score_raw"] = 8.0 - z2.astype(float) * 1.5 - z3.astype(float) * 3.5 - missing_flood.astype(float) * 0.8
    out["resilience_score_raw"] = out["resilience_score_raw"].map(clamp)

    hectares = out["brownfield_hectares_50km"].fillna(0)
    count = out["brownfield_site_count_50km"].fillna(0)
    land_base = 0.65 * hectares.map(lambda v: _linear(v, 0, max(50, hectares.quantile(0.9)))) + 0.35 * count.map(lambda v: _linear(v, 0, max(20, count.quantile(0.9))))
    out["land_score_raw"] = land_base.map(clamp)

    out["planning_risk_score_raw"] = (
        z2.astype(float) * 1.5
        + z3.astype(float) * 3.0
        + missing_flood.astype(float) * 1.0
        + out["data_quality_notes"].fillna("").str.contains("failed|missing|skipped|unavailable", case=False).astype(float) * 1.0
    ).map(clamp)
    logger.debug(
        "Raw score ranges energy=%s water=%s climate=%s latency=%s resilience=%s land=%s planning_risk=%s.",
        (float(out["energy_score_raw"].min()), float(out["energy_score_raw"].max())),
        (float(out["water_score_raw"].min()), float(out["water_score_raw"].max())),
        (float(out["climate_score_raw"].min()), float(out["climate_score_raw"].max())),
        (float(out["latency_score_raw"].min()), float(out["latency_score_raw"].max())),
        (float(out["resilience_score_raw"].min()), float(out["resilience_score_raw"].max())),
        (float(out["land_score_raw"].min()), float(out["land_score_raw"].max())),
        (float(out["planning_risk_score_raw"].min()), float(out["planning_risk_score_raw"].max())),
    )
    return out


def score_for_workload(df: pd.DataFrame, workload: str) -> pd.DataFrame:
    if workload not in WORKLOAD_WEIGHTS:
        raise ValueError(f"Unknown workload '{workload}'. Choose one of: {', '.join(WORKLOAD_WEIGHTS)}")
    logger.debug("Scoring workload=%s weights=%s rows=%s.", workload, WORKLOAD_WEIGHTS[workload], len(df))
    out = add_raw_scores(df)
    weights = WORKLOAD_WEIGHTS[workload]
    positive = (
        weights.get("energy", 0) * out["energy_score_raw"]
        + weights.get("water", 0) * out["water_score_raw"]
        + weights.get("climate", 0) * out["climate_score_raw"]
        + weights.get("latency", 0) * out["latency_score_raw"]
        + weights.get("resilience", 0) * out["resilience_score_raw"]
        + weights.get("land", 0) * out["land_score_raw"]
    )
    if "population" in weights:
        pop = out["population_lad"].fillna(out["population_lad"].median())
        positive += weights["population"] * pop.map(lambda v: _linear(v, pop.min(), pop.max()))
    if "primary_hub_separation" in weights:
        positive += weights["primary_hub_separation"] * out["primary_hub_distance_km"].map(lambda v: _linear(v, 40, 450))
    risk = weights.get("planning_risk", 0) * out["planning_risk_score_raw"]
    denom = sum(v for k, v in weights.items() if k != "planning_risk")
    out["overall_score"] = ((positive - risk) / max(denom, 0.01)).map(clamp)
    out["workload"] = workload
    out = out.sort_values("overall_score", ascending=False).reset_index(drop=True)
    logger.debug("Workload scoring complete top=%s.", out[["region", "overall_score"]].head(5).to_dict(orient="records"))
    return out


def workload_summary(workload: str) -> str:
    weights = WORKLOAD_WEIGHTS[workload]
    parts = [f"{key}={value:.2f}" for key, value in weights.items()]
    return ", ".join(parts)
