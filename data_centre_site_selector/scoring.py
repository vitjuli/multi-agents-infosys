from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .config import HUBS, WORKLOAD_WEIGHTS
from .geo_utils import clamp, haversine_km


def _linear(value: float, low: float, high: float) -> float:
    if pd.isna(value):
        return 5.0
    if high <= low:
        return 5.0
    return clamp(10 * (float(value) - low) / (high - low))


def add_raw_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    cap = out["renewable_capacity_50km_mw"].fillna(0)
    op = out["operational_renewable_capacity_50km_mw"].fillna(0)
    pipe = out["pipeline_renewable_capacity_50km_mw"].fillna(0)
    cap_score = cap.map(lambda v: _linear(v, 0, max(500, cap.quantile(0.9))))
    op_score = op.map(lambda v: _linear(v, 0, max(250, op.quantile(0.9))))
    pipe_score = pipe.map(lambda v: _linear(v, 0, max(250, pipe.quantile(0.9))))
    gsp_bonus = out["gsp_region"].notna().astype(float) * 0.8
    out["energy_score_raw"] = (0.55 * cap_score + 0.25 * op_score + 0.20 * pipe_score + gsp_bonus).map(clamp)

    southeast = out["region"].str.contains("Slough|London|Bristol", case=False, na=False)
    out["water_score_raw"] = np.where(southeast, 5.5, 7.0)
    out["water_score_note"] = "placeholder heuristic; replace with water-stress and abstraction/licensing datasets"

    min_lat, max_lat = out["lat"].min(), out["lat"].max()
    out["climate_score_raw"] = out["lat"].map(lambda v: _linear(v, min_lat, max_lat))
    out["climate_score_note"] = "placeholder latitude cooling proxy; replace with HadUK-Grid or equivalent climate data"

    for hub, (lat, lon) in HUBS.items():
        out[f"distance_to_{hub.lower()}_km"] = out.apply(lambda r: haversine_km(r["lat"], r["lon"], lat, lon), axis=1)
    out["nearest_major_hub_distance_km"] = out[[f"distance_to_{h.lower()}_km" for h in HUBS]].min(axis=1)
    out["latency_score_raw"] = out["nearest_major_hub_distance_km"].map(lambda d: clamp(10 - (d / 45)))

    z2 = out["flood_zone_2_intersects"].fillna(False).astype(bool)
    z3 = out["flood_zone_3_intersects"].fillna(False).astype(bool)
    missing_flood = out["flood_zone_2_intersects"].isna() | out["flood_zone_3_intersects"].isna()
    out["resilience_score_raw"] = 8.0 - z2.astype(float) * 1.5 - z3.astype(float) * 3.5 - missing_flood.astype(float) * 0.8
    out["resilience_score_raw"] = out["resilience_score_raw"].map(clamp)

    hectares = out["brownfield_hectares_50km"].fillna(0)
    count = out["brownfield_site_count_50km"].fillna(0)
    land_base = 0.65 * hectares.map(lambda v: _linear(v, 0, max(50, hectares.quantile(0.9)))) + 0.35 * count.map(lambda v: _linear(v, 0, max(20, count.quantile(0.9))))
    london_penalty = out["region"].str.contains("Slough|London", case=False, na=False).astype(float) * 1.0
    out["land_score_raw"] = (land_base - london_penalty).map(clamp)

    out["planning_risk_score_raw"] = (
        z2.astype(float) * 1.5
        + z3.astype(float) * 3.0
        + missing_flood.astype(float) * 1.0
        + out["region"].str.contains("Slough|London", case=False, na=False).astype(float) * 1.5
        + out["data_quality_notes"].fillna("").str.contains("failed|missing|skipped|unavailable", case=False).astype(float) * 1.0
    ).map(clamp)
    return out


def score_for_workload(df: pd.DataFrame, workload: str) -> pd.DataFrame:
    if workload not in WORKLOAD_WEIGHTS:
        raise ValueError(f"Unknown workload '{workload}'. Choose one of: {', '.join(WORKLOAD_WEIGHTS)}")
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
    if "london_separation" in weights:
        positive += weights["london_separation"] * out["distance_to_london_km"].map(lambda v: _linear(v, 40, 450))
    risk = weights.get("planning_risk", 0) * out["planning_risk_score_raw"]
    denom = sum(v for k, v in weights.items() if k != "planning_risk")
    out["overall_score"] = ((positive - risk) / max(denom, 0.01)).map(clamp)
    out["workload"] = workload
    return out.sort_values("overall_score", ascending=False).reset_index(drop=True)


def workload_summary(workload: str) -> str:
    weights = WORKLOAD_WEIGHTS[workload]
    parts = [f"{key}={value:.2f}" for key, value in weights.items()]
    return ", ".join(parts)
