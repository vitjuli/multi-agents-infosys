#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW_DIR="$ROOT_DIR/data/raw"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$RAW_DIR"

"$PYTHON_BIN" - "$RAW_DIR" <<'PY'
from __future__ import annotations

import html.parser
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path


RAW_DIR = Path(sys.argv[1])
USER_AGENT = "Mozilla/5.0 (compatible; infosys-data-downloader/1.0)"


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if href:
            self.links.append(href)


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def links_from_page(url: str) -> list[str]:
    parser = LinkParser()
    parser.feed(fetch_text(url))
    return [urllib.parse.urljoin(url, link.replace("&amp;", "&")) for link in parser.links]


def ckan_package(package_id: str) -> dict:
    url = f"https://ckan.publishing.service.gov.uk/api/3/action/package_show?id={package_id}"
    data = json.loads(fetch_text(url))
    if not data.get("success"):
        raise RuntimeError(f"CKAN package lookup failed for {package_id}")
    return data["result"]


def select_resource(resources: list[dict], *, needles: tuple[str, ...], formats: tuple[str, ...] = ()) -> dict:
    scored: list[tuple[int, dict]] = []
    for resource in resources:
        url = resource.get("url") or ""
        fmt = (resource.get("format") or "").lower()
        name = (resource.get("name") or "").lower()
        blob = f"{name} {fmt} {url.lower()}"
        if not url:
            continue
        score = 0
        for needle in needles:
            if needle.lower() in blob:
                score += 10
        for wanted_format in formats:
            if fmt == wanted_format.lower() or url.lower().endswith(f".{wanted_format.lower()}"):
                score += 20
        if score:
            scored.append((score, resource))
    if not scored:
        raise RuntimeError(f"Could not find resource matching {needles} / {formats}")
    return sorted(scored, key=lambda item: item[0], reverse=True)[0][1]


def find_link(url: str, *, include: tuple[str, ...], exclude: tuple[str, ...] = ()) -> str:
    matches: list[str] = []
    for link in links_from_page(url):
        lower = urllib.parse.unquote(link.lower())
        if all(term.lower() in lower for term in include) and not any(term.lower() in lower for term in exclude):
            matches.append(link)
    if not matches:
        raise RuntimeError(f"Could not find link on {url} containing {include}")
    return matches[0]


def looks_valid(path: Path, expected: str | None) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False

    prefix = path.read_bytes()[:512].lstrip()
    if expected in {"xlsx", "zip"}:
        return prefix.startswith(b"PK")
    if expected == "csv":
        return not prefix.lower().startswith((b"<!doctype html", b"<html"))
    if expected == "geojson":
        return prefix.startswith(b"{")
    return True


def download(url: str, output_name: str, *, expected: str | None = None, min_csv_rows: int = 0) -> None:
    output_path = RAW_DIR / output_name
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")

    print(f"\nDownloading {output_name}")
    print(f"  {url}")

    if looks_valid(output_path, expected) and not bool(int(os.environ.get("FORCE_DOWNLOAD", "0"))):
        if expected == "csv" and min_csv_rows:
            rows = output_path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
            if len([row for row in rows if row.strip()]) < min_csv_rows:
                output_path.unlink()
            else:
                size = output_path.stat().st_size
                print(f"  already present, keeping {size / (1024 * 1024):.1f} MB")
                return
        else:
            size = output_path.stat().st_size
            print(f"  already present, keeping {size / (1024 * 1024):.1f} MB")
            return

    if shutil.which("curl"):
        subprocess.run(
            [
                "curl",
                "--fail",
                "--location",
                "--retry",
                "3",
                "--connect-timeout",
                "30",
                "--user-agent",
                USER_AGENT,
                "--output",
                str(tmp_path),
                url,
            ],
            check=True,
        )
    else:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            tmp_path.write_bytes(response.read())

    size = tmp_path.stat().st_size
    if size == 0:
        raise RuntimeError(f"{output_name} downloaded as an empty file")

    if not looks_valid(tmp_path, expected):
        raise RuntimeError(f"{output_name} did not match expected content type {expected}")
    if expected == "csv" and min_csv_rows:
        rows = tmp_path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        if len([row for row in rows if row.strip()]) < min_csv_rows:
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError(f"{output_name} contained fewer than {min_csv_rows} non-empty CSV rows")

    tmp_path.replace(output_path)
    print(f"  saved {size / (1024 * 1024):.1f} MB")


def ons_lad_boundaries() -> None:
    package = ckan_package("local-authority-districts-december-2024-boundaries-uk-buc")
    resource = select_resource(package["resources"], needles=("geojson",), formats=("geojson",))
    download(resource["url"], "ons_lad_boundaries_dec2024_buc.geojson", expected="geojson")


def renewable_energy_planning_database() -> None:
    page = "https://www.gov.uk/government/publications/renewable-energy-planning-database-quarterly-extract"
    links = links_from_page(page)
    attachments = [
        link
        for link in links
        if re.search(r"\.(xlsx|xls|ods)(?:$|[?#])", urllib.parse.urlparse(link).path, re.I)
    ]
    if not attachments:
        raise RuntimeError("Could not find the REPD spreadsheet attachment")
    download(attachments[0], "desnz_repd_latest.xlsx", expected="xlsx")


def neso_gsp_regions() -> None:
    page = "https://www.neso.energy/data-portal/gis-boundaries-gb-grid-supply-points/gsp_regions_20250102"
    html = fetch_text(page)
    (RAW_DIR / "neso_gsp_page.html").write_text(html, encoding="utf-8")
    matches = re.findall(r'href=["\']([^"\']+gsp_regions_20250102\.zip[^"\']*)["\']', html, flags=re.I)
    if not matches:
        raise RuntimeError("Could not find the NESO GSP ZIP link")
    download(urllib.parse.urljoin(page, matches[0]), "neso_gsp_regions_20250102.zip", expected="zip")


def environment_agency_flood_zones() -> None:
    package = ckan_package("flood-map-for-planning-flood-zones1")
    resource = select_resource(package["resources"], needles=("geojson.zip", "flood_map_for_planning_flood_zones"), formats=("zip",))
    download(resource["url"], "ea_flood_map_for_planning_flood_zones.geojson.zip", expected="zip")


def ons_population_estimates() -> None:
    download(
        "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/estimatesofthepopulationforenglandandwales/mid20242023localauthorityboundaries/mye24tablesew.xlsx",
        "ons_population_estimates_mid2024_la.xlsx",
        expected="xlsx",
    )


def planning_brownfield() -> None:
    download(
        "https://files.planning.data.gov.uk/dataset/brownfield-land.csv",
        "planning_brownfield_land.csv",
        expected="csv",
    )
    download(
        "https://files.planning.data.gov.uk/dataset/brownfield-site.csv",
        "planning_brownfield_site.csv",
        expected="csv",
    )


def ukpn_data_centres() -> None:
    params = {
        "lang": "en",
        "timezone": "Europe/London",
        "use_labels": "true",
        "delimiter": ",",
    }
    api_key = os.environ.get("UKPN_OPENDATASOFT_API_KEY")
    if api_key:
        params["apikey"] = api_key
    url = "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/ukpn-data-centres-by-local-authority/exports/csv?"
    url += urllib.parse.urlencode(params)

    try:
        download(url, "ukpn_data_centres_by_local_authority.csv", expected="csv", min_csv_rows=2)
    except RuntimeError as exc:
        (RAW_DIR / "ukpn_data_centres_by_local_authority.csv").unlink(missing_ok=True)
        print(f"\nSkipping UKPN data centres by local authority: {exc}")
        print("  UKPN currently requires login/API access for this dataset.")
        print("  Set UKPN_OPENDATASOFT_API_KEY and rerun if your account has access.")


def print_haduk_note() -> None:
    print(
        """
HadUK-Grid climate data is not downloaded automatically because CEDA normally requires
an authenticated account. For this project, use the administrative-region HadUK-Grid
product once you have CEDA access:

  wget --user "$CEDA_USERNAME" --ask-password \\
    --recursive --no-parent --no-host-directories --cut-dirs=3 \\
    --accept "*.nc" \\
    "https://data.ceda.ac.uk/badc/ukmo-hadobs/data/insitu/MOHC/HadOBS/HadUK-Grid/" \\
    -P data/raw/haduk_grid/
""".rstrip()
    )


def main() -> None:
    tasks = [
        ons_lad_boundaries,
        renewable_energy_planning_database,
        neso_gsp_regions,
        environment_agency_flood_zones,
        ons_population_estimates,
        planning_brownfield,
        ukpn_data_centres,
    ]
    for task in tasks:
        task()

    print_haduk_note()
    print(f"\nDone. Raw files are in {RAW_DIR}")


if __name__ == "__main__":
    main()
PY
