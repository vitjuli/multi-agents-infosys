from __future__ import annotations

import math
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import CANDIDATE_REGIONS
from .data_paths import (
    BROWNFIELD_LAND_CSV,
    BROWNFIELD_SITE_CSV,
    FLOOD_ZONES_ZIP,
    GSP_ZIP,
    LAD_BOUNDARIES,
    POPULATION_XLSX,
    REPD_XLSX,
)
from .geo_utils import find_vector_member, has_geopandas, haversine_km, osgb_to_wgs84, parse_point_wkt


def log(message: str) -> None:
    print(f"[features] {message}", flush=True)


def norm_col(col: Any) -> str:
    return "".join(ch.lower() for ch in str(col) if ch.isalnum())


def detect_column(columns: list[str], candidates: list[str]) -> str | None:
    normalised = {norm_col(c): c for c in columns}
    for cand in candidates:
        key = norm_col(cand)
        if key in normalised:
            return normalised[key]
    for col in columns:
        key = norm_col(col)
        if any(norm_col(cand) in key for cand in candidates):
            return col
    return None


def note(notes: list[str], message: str) -> None:
    if message not in notes:
        notes.append(message)


def candidate_frame() -> pd.DataFrame:
    return pd.DataFrame([c.__dict__ for c in CANDIDATE_REGIONS]).rename(columns={"lad_name_hint": "lad_name_hint"})


def add_lad_features(df: pd.DataFrame, diagnostics: list[str]) -> pd.DataFrame:
    df["lad_code"] = np.nan
    df["lad_name"] = df["lad_name_hint"]
    if not LAD_BOUNDARIES.exists():
        diagnostics.append("LAD boundaries missing; used candidate LAD name hints only.")
        return df
    if not has_geopandas():
        diagnostics.append("geopandas/shapely unavailable; skipped LAD point-in-polygon join.")
        return df
    try:
        import geopandas as gpd
        from shapely.geometry import Point

        lad = gpd.read_file(LAD_BOUNDARIES)
        code_col = detect_column(list(lad.columns), ["LAD24CD", "lad code", "ladcd", "ctyua24cd", "local authority district code"])
        name_col = detect_column(list(lad.columns), ["LAD24NM", "lad name", "ladnm", "ctyua24nm", "local authority district name"])
        pts = gpd.GeoDataFrame(df.copy(), geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])], crs="EPSG:4326")
        joined = gpd.sjoin(pts, lad[[c for c in [code_col, name_col, "geometry"] if c]], how="left", predicate="within")
        if code_col:
            df["lad_code"] = joined[code_col].values
        if name_col:
            df["lad_name"] = joined[name_col].fillna(df["lad_name_hint"]).values
        diagnostics.append("Computed LAD joins using ONS LAD boundaries.")
    except Exception as exc:
        diagnostics.append(f"LAD spatial join failed: {exc}. Used candidate LAD name hints only.")
    return df


def add_population_features(df: pd.DataFrame, diagnostics: list[str]) -> pd.DataFrame:
    df["population_lad"] = np.nan
    if not POPULATION_XLSX.exists():
        diagnostics.append("Population workbook missing.")
        return df
    try:
        xl = pd.ExcelFile(POPULATION_XLSX)
        best = "MYE2 - Persons" if "MYE2 - Persons" in xl.sheet_names else None
        if best is None:
            for sheet in xl.sheet_names:
                sample = pd.read_excel(POPULATION_XLSX, sheet_name=sheet, nrows=12, header=None)
                text = " ".join(map(str, sample.to_numpy().ravel())).lower()
                if "all ages" in text and "geography" in text and "code" in text:
                    best = sheet
                    break
        best = best or xl.sheet_names[-1]
        pop = pd.read_excel(POPULATION_XLSX, sheet_name=best, header=None)
        header_idx = 0
        for i in range(min(20, len(pop))):
            row = " ".join(map(str, pop.iloc[i].tolist())).lower()
            if "code" in row and "name" in row and ("all ages" in row or "population" in row):
                header_idx = i
                break
        pop = pd.read_excel(POPULATION_XLSX, sheet_name=best, header=header_idx)
        pop.columns = [str(c).strip() for c in pop.columns]
        code_col = detect_column(list(pop.columns), ["code", "geography code", "lad code", "area code"])
        name_col = detect_column(list(pop.columns), ["name", "geography", "area name", "local authority"])
        total_col = detect_column(list(pop.columns), ["All ages", "Estimated Population mid-2024", "total", "persons"])
        if total_col is None:
            numeric = [c for c in pop.columns if pd.api.types.is_numeric_dtype(pop[c])]
            total_col = numeric[-1] if numeric else None
        if total_col is None or (code_col is None and name_col is None):
            diagnostics.append(f"Could not detect population columns in sheet {best}.")
            return df
        subset = pop[[c for c in [code_col, name_col, total_col] if c]].copy()
        subset[total_col] = pd.to_numeric(subset[total_col], errors="coerce")
        if code_col and df["lad_code"].notna().any():
            df = df.merge(subset[[code_col, total_col]], left_on="lad_code", right_on=code_col, how="left")
            df["population_lad"] = df[total_col]
            df = df.drop(columns=[c for c in [code_col, total_col] if c in df.columns and c not in ["lad_code"]], errors="ignore")
        if df["population_lad"].isna().any() and name_col:
            mapping = subset.dropna(subset=[name_col]).groupby(subset[name_col].astype(str).str.lower())[total_col].first()
            df["population_lad"] = df.apply(
                lambda r: mapping.get(str(r.get("lad_name_hint") or r.get("lad_name")).lower(), r["population_lad"]),
                axis=1,
            )
        diagnostics.append(f"Joined population estimates from sheet {best}; Scotland may be missing in England/Wales workbook.")
    except Exception as exc:
        diagnostics.append(f"Population processing failed: {exc}.")
    return df


def _coordinate_columns(df: pd.DataFrame) -> tuple[str | None, str | None, str | None, str | None]:
    cols = list(df.columns)
    lat = detect_column(cols, ["latitude", "lat"])
    lon = detect_column(cols, ["longitude", "lon", "lng"])
    x = detect_column(cols, ["x-coordinate", "x coordinate", "easting"])
    y = detect_column(cols, ["y-coordinate", "y coordinate", "northing"])
    return lat, lon, x, y


def add_renewable_features(df: pd.DataFrame, diagnostics: list[str]) -> pd.DataFrame:
    for col in [
        "renewable_capacity_25km_mw",
        "renewable_capacity_50km_mw",
        "renewable_project_count_50km",
        "operational_renewable_capacity_50km_mw",
        "pipeline_renewable_capacity_50km_mw",
    ]:
        df[col] = 0.0
    if not REPD_XLSX.exists():
        diagnostics.append("DESNZ REPD workbook missing.")
        return df
    try:
        xl = pd.ExcelFile(REPD_XLSX)
        sheet = "REPD" if "REPD" in xl.sheet_names else xl.sheet_names[-1]
        repd = pd.read_excel(REPD_XLSX, sheet_name=sheet)
        repd.columns = [str(c).strip() for c in repd.columns]
        cap_col = detect_column(list(repd.columns), ["Installed Capacity (MWelec)", "capacity mw", "capacity"])
        status_col = detect_column(list(repd.columns), ["Development Status", "Development Status (short)", "status"])
        lat_col, lon_col, x_col, y_col = _coordinate_columns(repd)
        if cap_col is None:
            diagnostics.append("REPD capacity column not detected; renewable features left as zero.")
            return df
        repd["capacity_mw"] = pd.to_numeric(repd[cap_col], errors="coerce").fillna(0)
        coords = []
        if lat_col and lon_col:
            coords = list(zip(pd.to_numeric(repd[lat_col], errors="coerce"), pd.to_numeric(repd[lon_col], errors="coerce")))
        elif x_col and y_col:
            for x, y in zip(pd.to_numeric(repd[x_col], errors="coerce"), pd.to_numeric(repd[y_col], errors="coerce")):
                coords.append(osgb_to_wgs84(x, y) if not pd.isna(x) and not pd.isna(y) else None)
        else:
            diagnostics.append("REPD coordinates not detected; local-authority aggregation hook is available but not populated in this baseline.")
            return df
        repd["coord"] = coords
        repd = repd[repd["coord"].notna()].copy()
        repd["lat"] = [c[0] for c in repd["coord"]]
        repd["lon"] = [c[1] for c in repd["coord"]]
        statuses = repd[status_col].astype(str).str.lower() if status_col else pd.Series("", index=repd.index)
        operational = statuses.str.contains("operat|generat|commission", regex=True, na=False)
        pipeline = ~operational
        for idx, cand in df.iterrows():
            dists = repd.apply(lambda r: haversine_km(cand["lat"], cand["lon"], r["lat"], r["lon"]), axis=1)
            within25 = dists <= 25
            within50 = dists <= 50
            df.loc[idx, "renewable_capacity_25km_mw"] = repd.loc[within25, "capacity_mw"].sum()
            df.loc[idx, "renewable_capacity_50km_mw"] = repd.loc[within50, "capacity_mw"].sum()
            df.loc[idx, "renewable_project_count_50km"] = int(within50.sum())
            df.loc[idx, "operational_renewable_capacity_50km_mw"] = repd.loc[within50 & operational, "capacity_mw"].sum()
            df.loc[idx, "pipeline_renewable_capacity_50km_mw"] = repd.loc[within50 & pipeline, "capacity_mw"].sum()
        diagnostics.append(f"Computed renewable radius features from DESNZ REPD sheet {sheet}.")
    except Exception as exc:
        diagnostics.append(f"Renewable processing failed: {exc}.")
    return df


def add_brownfield_features(df: pd.DataFrame, diagnostics: list[str]) -> pd.DataFrame:
    for col in ["brownfield_site_count_25km", "brownfield_hectares_25km", "brownfield_site_count_50km", "brownfield_hectares_50km"]:
        df[col] = 0.0
    frames = []
    for path in [BROWNFIELD_LAND_CSV, BROWNFIELD_SITE_CSV]:
        if not path.exists():
            diagnostics.append(f"{path.name} missing.")
            continue
        try:
            usecols = None
            sample = pd.read_csv(path, nrows=0)
            cols = list(sample.columns)
            keep = [c for c in cols if norm_col(c) in {"point", "hectares", "organisation", "name", "reference"}]
            usecols = keep or None
            raw = pd.read_csv(path, usecols=usecols)
            point_col = detect_column(list(raw.columns), ["point"])
            hect_col = detect_column(list(raw.columns), ["hectares"])
            if point_col is None:
                diagnostics.append(f"{path.name} has no detected point column; skipped radius features.")
                continue
            coords = raw[point_col].map(parse_point_wkt)
            part = pd.DataFrame({"coord": coords})
            part["hectares"] = pd.to_numeric(raw[hect_col], errors="coerce").fillna(0) if hect_col else 0.0
            part = part[part["coord"].notna()].copy()
            part["lat"] = [c[0] for c in part["coord"]]
            part["lon"] = [c[1] for c in part["coord"]]
            frames.append(part)
        except Exception as exc:
            diagnostics.append(f"Brownfield file {path.name} failed: {exc}.")
    if not frames:
        diagnostics.append("No usable brownfield point features found.")
        return df
    sites = pd.concat(frames, ignore_index=True)
    for idx, cand in df.iterrows():
        dists = sites.apply(lambda r: haversine_km(cand["lat"], cand["lon"], r["lat"], r["lon"]), axis=1)
        within25 = dists <= 25
        within50 = dists <= 50
        df.loc[idx, "brownfield_site_count_25km"] = int(within25.sum())
        df.loc[idx, "brownfield_hectares_25km"] = sites.loc[within25, "hectares"].sum()
        df.loc[idx, "brownfield_site_count_50km"] = int(within50.sum())
        df.loc[idx, "brownfield_hectares_50km"] = sites.loc[within50, "hectares"].sum()
    diagnostics.append("Computed brownfield radius features from available point columns; England-only caveat applies.")
    return df


def add_gsp_features(df: pd.DataFrame, diagnostics: list[str]) -> pd.DataFrame:
    df["gsp_region"] = np.nan
    df["nearest_gsp_distance_km"] = np.nan
    member = find_vector_member(GSP_ZIP)
    if not member:
        diagnostics.append("NESO GSP vector member not found in ZIP.")
        return df
    if not has_geopandas():
        diagnostics.append("geopandas/shapely unavailable; skipped GSP spatial join.")
        return df
    try:
        import geopandas as gpd
        from shapely.geometry import Point

        path = f"zip://{GSP_ZIP}!{member}"
        gsp = gpd.read_file(path)
        name_col = detect_column(list(gsp.columns), ["name", "gsp", "region", "GSP Group"])
        pts = gpd.GeoDataFrame(df.copy(), geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])], crs="EPSG:4326")
        joined = gpd.sjoin(pts, gsp[[c for c in [name_col, "geometry"] if c]], how="left", predicate="within")
        if name_col:
            df["gsp_region"] = joined[name_col].values
        gsp27700 = gsp.to_crs("EPSG:27700")
        pts27700 = pts.to_crs("EPSG:27700")
        centroids = gsp27700.geometry.centroid
        df["nearest_gsp_distance_km"] = [centroids.distance(point).min() / 1000 for point in pts27700.geometry]
        diagnostics.append(f"Computed GSP joins from {member}.")
    except Exception as exc:
        diagnostics.append(f"GSP processing failed: {exc}.")
    return df


def add_flood_features(df: pd.DataFrame, diagnostics: list[str], load_flood: bool = False) -> pd.DataFrame:
    df["flood_zone_2_intersects"] = np.nan
    df["flood_zone_3_intersects"] = np.nan
    df["flood_zone_overlap_warning"] = "not computed"
    if not FLOOD_ZONES_ZIP.exists():
        diagnostics.append("EA flood zones ZIP missing.")
        return df
    if not load_flood:
        diagnostics.append("Flood ZIP present but not loaded by default because it is large; rerun build with --include-flood to compute.")
        df["flood_zone_overlap_warning"] = "flood data present but not computed; large file skipped"
        return df
    if not has_geopandas():
        diagnostics.append("geopandas/shapely unavailable; skipped flood processing.")
        df["flood_zone_overlap_warning"] = "missing geospatial dependencies"
        return df
    try:
        import geopandas as gpd
        from shapely.geometry import Point

        member = find_vector_member(FLOOD_ZONES_ZIP)
        if not member:
            diagnostics.append("No GeoJSON/shapefile found inside flood ZIP.")
            return df
        pts = gpd.GeoDataFrame(df.copy(), geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])], crs="EPSG:4326").to_crs("EPSG:27700")
        path = f"zip://{FLOOD_ZONES_ZIP}!{member}"
        flood = gpd.read_file(path, bbox=tuple(pts.buffer(15000).total_bounds)).to_crs("EPSG:27700")
        zone_col = detect_column(list(flood.columns), ["floodzone", "zone", "flood zone"])
        for idx, point in zip(df.index, pts.geometry):
            nearby = flood[flood.intersects(point.buffer(15000))]
            text = nearby[zone_col].astype(str).str.lower() if zone_col else pd.Series("", index=nearby.index)
            df.loc[idx, "flood_zone_2_intersects"] = bool(text.str.contains("2").any()) if zone_col else bool(len(nearby))
            df.loc[idx, "flood_zone_3_intersects"] = bool(text.str.contains("3").any()) if zone_col else False
            df.loc[idx, "flood_zone_overlap_warning"] = "computed within 15km candidate buffer"
        diagnostics.append("Computed flood-zone intersections with candidate buffers.")
    except Exception as exc:
        diagnostics.append(f"Flood processing failed: {exc}.")
        df["flood_zone_overlap_warning"] = f"flood processing failed: {exc}"
    return df


def build_candidate_features(include_flood: bool = False) -> tuple[pd.DataFrame, list[str]]:
    diagnostics: list[str] = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        log("Creating fixed candidate region table.")
        df = candidate_frame()
        log("Joining candidates to ONS LAD boundaries.")
        df = add_lad_features(df, diagnostics)
        log("Joining ONS population estimates.")
        df = add_population_features(df, diagnostics)
        log("Computing renewable energy radius features from DESNZ REPD.")
        df = add_renewable_features(df, diagnostics)
        log("Joining NESO GSP regions and nearest GSP distances.")
        df = add_gsp_features(df, diagnostics)
        log("Checking EA flood-zone availability.")
        df = add_flood_features(df, diagnostics, load_flood=include_flood)
        log("Computing brownfield land/site radius features.")
        df = add_brownfield_features(df, diagnostics)
        log("Feature build complete.")
    df["data_quality_notes"] = " | ".join(diagnostics)
    return df, diagnostics
