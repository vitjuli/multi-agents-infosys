from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = ROOT / "reports"

LAD_BOUNDARIES = RAW_DIR / "ons_lad_boundaries_dec2024_buc.geojson"
REPD_XLSX = RAW_DIR / "desnz_repd_latest.xlsx"
GSP_ZIP = RAW_DIR / "neso_gsp_regions_20250102.zip"
FLOOD_ZONES_ZIP = RAW_DIR / "ea_flood_map_for_planning_flood_zones.geojson.zip"
POPULATION_XLSX = RAW_DIR / "ons_population_estimates_mid2024_la.xlsx"
BROWNFIELD_LAND_CSV = RAW_DIR / "planning_brownfield_land.csv"
BROWNFIELD_SITE_CSV = RAW_DIR / "planning_brownfield_site.csv"

CANDIDATE_FEATURES_CSV = PROCESSED_DIR / "candidate_region_features.csv"
LATEST_RANKINGS_CSV = PROCESSED_DIR / "latest_rankings.csv"
LATEST_REPORT_MD = REPORTS_DIR / "latest_report.md"
LATEST_SUMMARY_REPORT_MD = REPORTS_DIR / "latest_summary.md"
LATEST_PDF_REPORT = REPORTS_DIR / "latest_report.pdf"
LATEST_PDF_PLOTS_DIR = REPORTS_DIR / "report_plots"


def ensure_dirs() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
