#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
import sys
from zipfile import ZipFile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_centre_site_selector.data_paths import RAW_DIR
from data_centre_site_selector.geo_utils import find_vector_member, has_geopandas


def log(message: str) -> None:
    print(f"[inspect] {message}", flush=True)


def size_mb(path: Path) -> str:
    return f"{path.stat().st_size / (1024 * 1024):.1f} MB" if path.exists() else "missing"


def inspect_csv(path: Path) -> None:
    try:
        df = pd.read_csv(path, nrows=3)
        print(f"Columns ({len(df.columns)}): {list(df.columns)}")
        print("Example rows:")
        print(df.head(3).to_string())
    except Exception as exc:
        print(f"CSV inspection failed: {exc}")


def inspect_xlsx(path: Path) -> None:
    try:
        xl = pd.ExcelFile(path)
        print(f"Sheets: {xl.sheet_names}")
        for sheet in xl.sheet_names[:5]:
            try:
                df = pd.read_excel(path, sheet_name=sheet, nrows=3)
                print(f"Sheet {sheet} columns: {list(df.columns)}")
                print(df.head(2).to_string())
            except Exception as exc:
                print(f"Sheet {sheet} failed: {exc}")
    except Exception as exc:
        print(f"Excel inspection failed: {exc}")


def inspect_geo(path: Path) -> None:
    if not has_geopandas():
        print("geopandas/shapely not installed; CRS and geometry-type inspection skipped.")
        return
    try:
        import geopandas as gpd

        gdf = gpd.read_file(path, rows=5)
        print(f"CRS: {gdf.crs}")
        print(f"Geometry types: {gdf.geometry.geom_type.unique().tolist()}")
        print(f"Columns: {list(gdf.columns)}")
        print(gdf.head(3).drop(columns='geometry', errors='ignore').to_string())
    except Exception as exc:
        print(f"Geospatial inspection failed: {exc}")


def inspect_zip(path: Path) -> None:
    try:
        with ZipFile(path) as zf:
            names = zf.namelist()
        print(f"ZIP members: {len(names)}")
        print(f"First members: {names[:20]}")
        member = find_vector_member(path)
        print(f"Detected vector member: {member}")
        if member and has_geopandas():
            import geopandas as gpd

            gdf = gpd.read_file(f"zip://{path}!{member}", rows=5)
            print(f"CRS: {gdf.crs}")
            print(f"Geometry types: {gdf.geometry.geom_type.unique().tolist()}")
            print(f"Columns: {list(gdf.columns)}")
    except Exception as exc:
        print(f"ZIP inspection failed: {exc}")


def main() -> None:
    files = sorted(RAW_DIR.glob("*"))
    if not files:
        print(f"No files found in {RAW_DIR}")
        return
    for path in files:
        log(f"Inspecting {path.name}.")
        print("\n" + "=" * 80)
        print(f"{path.name}")
        print(f"Exists: {path.exists()}")
        print(f"Size: {size_mb(path)}")
        suffix = path.suffix.lower()
        print(f"Detected format: {suffix or 'unknown'}")
        if suffix == ".csv":
            inspect_csv(path)
        elif suffix in {".xlsx", ".xls"}:
            inspect_xlsx(path)
        elif suffix in {".geojson", ".json", ".shp"}:
            inspect_geo(path)
        elif suffix == ".zip":
            inspect_zip(path)
        else:
            print("No specialised inspector for this format.")
        log(f"Finished {path.name}.")


if __name__ == "__main__":
    main()
