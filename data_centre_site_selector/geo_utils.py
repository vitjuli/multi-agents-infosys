from __future__ import annotations

import importlib.util
import math
import re
from pathlib import Path
from typing import Any
from zipfile import ZipFile

"""CAM'S COMMENTS:
geo\_utils.py

   * Which format do we need our geographical data to be in?
   * what is a parse point?
   * what do any of these functions even do?
"""


def optional_import(name: str):
    if importlib.util.find_spec(name) is None:
        return None
    return __import__(name)


def has_geopandas() -> bool:
    return (
        importlib.util.find_spec("geopandas") is not None
        and importlib.util.find_spec("shapely") is not None
    )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def parse_point_wkt(value: Any) -> tuple[float, float] | None:
    if value is None:
        return None
    text = str(value)
    if not text or text.lower() == "nan":
        return None
    match = re.search(r"POINT\s*\(?\s*\(?\s*([-0-9.]+)\s+([-0-9.]+)\s*\)?", text, re.I)
    if not match:
        return None
    lon, lat = float(match.group(1)), float(match.group(2))
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None


def osgb_to_wgs84(x: float, y: float) -> tuple[float, float] | None:
    try:
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(float(x), float(y))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon
    except Exception:
        pass
    try:
        # Coarse fallback for hackathon use when pyproj is not installed. British
        # National Grid has a true-origin latitude near 49N and false northing
        # around -100 km; this is not a substitute for EPSG transformation, but
        # it is adequate for rough radius features until pyproj is installed.
        x_f = float(x)
        y_f = float(y)
        lat = 49.0 + (y_f + 100000.0) / 111320.0
        lon = -2.0 + (x_f - 400000.0) / (111320.0 * math.cos(math.radians(lat)))
        if 49 <= lat <= 62 and -9 <= lon <= 3:
            return lat, lon
    except Exception:
        return None
    return None


def find_vector_member(zip_path: Path) -> str | None:
    if not zip_path.exists():
        return None
    with ZipFile(zip_path) as zf:
        names = zf.namelist()
    for suffix in (".geojson", ".json", ".shp"):
        for name in names:
            if name.lower().endswith(suffix) and not Path(name).name.startswith("."):
                return name
    return None


def clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    if value != value:
        return value
    return max(low, min(high, value))
