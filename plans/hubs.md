# Plan: refine hub-based latency scoring

Status: awaiting approval. After approval, tick items in the checklist below
as each is completed.

## Status checklist

- [ ] 1. Add `DataHub` dataclass and `UK_DATA_HUBS` constant to `config.py`
- [ ] 2. Verify hub coordinates against published operator addresses
- [ ] 3. Add `hub_distances(df)` to `scoring.py` and rewire `add_raw_scores`
- [ ] 4. Delete `data_derived_hubs` (no other callers after step 3)
- [ ] 5. Run baseline pipeline before the change and capture JSON output
- [ ] 6. Run pipeline after the change and diff against baseline
- [ ] 7. Sanity-check distances and `latency_score_raw` against expected values
- [ ] 8. Present unified diff in chat for review; await approval before commit

## Goal

`scoring.data_derived_hubs` currently picks the top-N LADs by population and
treats them as data hubs. Replace it with a fixed list of real UK datacentre
and fibre-interchange clusters. Recompute `nearest_major_hub_distance_km` and
`primary_hub_distance_km` against that list. Everything downstream of those
columns, including the `latency_score_raw` formula and the
`backup_disaster_recovery` workload's `primary_hub_separation` term, stays
unchanged.

## Current behaviour (what is being replaced)

`data_centre_site_selector/scoring.py:25-41`:

```python
def data_derived_hubs(df, top_n=3):
    usable = df.dropna(subset=["lat", "lon"]).copy()
    if "population_lad" in usable:
        usable["_hub_weight"] = pd.to_numeric(usable["population_lad"], errors="coerce").fillna(0)
    else:
        usable["_hub_weight"] = 0
    if usable["_hub_weight"].sum() == 0:
        usable["_hub_weight"] = (
            usable["renewable_project_count_50km"].fillna(0)
            if "renewable_project_count_50km" in usable else 1
        )
    return usable.sort_values("_hub_weight", ascending=False).head(top_n)
```

In the 8-row cached run, three regions are tied at `latency_score_raw = 10`
because they are themselves selected as hubs by population, while Edinburgh
drops to 3.74 because it is far from those LADs. Across the full UK LAD set
the picked "hubs" would include Birmingham and Leeds (the most populous LADs),
plus another populous LAD that is not a commercial datacentre cluster. The
function is currently a population proxy with the wrong name.

## Files touched

| File | Change |
|---|---|
| `data_centre_site_selector/config.py` | Add `DataHub` dataclass and `UK_DATA_HUBS` tuple with one-line provenance per hub. |
| `data_centre_site_selector/scoring.py` | Import `UK_DATA_HUBS`. Add `hub_distances(df)`. Replace the hubs block inside `add_raw_scores`. Delete `data_derived_hubs`. |

No other modules are touched. The new `src/planning/`, `src/rl/`,
`src/preferences/`, `src/reports/` modules are not on the deterministic-scoring
path and are unaffected.

## Design

### `config.py` additions

```python
@dataclass(frozen=True)
class DataHub:
    name: str
    lat: float
    lon: float
    note: str  # one-line provenance


UK_DATA_HUBS: tuple[DataHub, ...] = (
    DataHub("Slough",           51.5105, -0.5950, "M4 corridor; Equinix LD4/5/6, Virtus, Yondr cluster"),
    DataHub("London Docklands", 51.5074,  0.0099, "Telehouse North/East/West, Equinix LD8"),
    DataHub("Manchester",       53.4794, -2.2453, "MA1 internet exchange and northern colo cluster"),
    DataHub("Edinburgh",        55.9533, -3.1883, "Scottish anchor; subsea-cable landings"),
    DataHub("Cardiff",          51.4816, -3.1791, "Welsh anchor; Next Generation Data nearby in Newport"),
)
```

Coordinates above are reasonable centres. Step 2 of the status checklist is
to verify each against the published address of the named anchor operator and
adjust to that lat/lon if necessary.

### `scoring.py` additions

New import at the top of the module:

```python
from .config import UK_DATA_HUBS, WORKLOAD_WEIGHTS
```

New function:

```python
def hub_distances(df: pd.DataFrame) -> pd.DataFrame:
    """Distance from each candidate to every UK_DATA_HUBS entry, in km."""
    out = df.copy()
    cols: list[str] = []
    for hub in UK_DATA_HUBS:
        slug = hub.name.lower().replace(" ", "_")
        col = f"distance_to_{slug}_km"
        # h=hub binds the loop variable so the closure captures this hub,
        # not the last one assigned.
        out[col] = out.apply(
            lambda r, h=hub: haversine_km(r["lat"], r["lon"], h.lat, h.lon),
            axis=1,
        )
        cols.append(col)
    out["nearest_major_hub_distance_km"] = out[cols].min(axis=1)
    primary_slug = UK_DATA_HUBS[0].name.lower().replace(" ", "_")
    out["primary_hub_distance_km"] = out[f"distance_to_{primary_slug}_km"]
    return out
```

In `add_raw_scores`, the existing block

```python
hubs = data_derived_hubs(out)
hub_distance_cols = []
for idx, hub in hubs.reset_index(drop=True).iterrows():
    col = f"distance_to_data_hub_{idx + 1}_km"
    out[col] = out.apply(
        lambda r: haversine_km(r["lat"], r["lon"], hub["lat"], hub["lon"]), axis=1
    )
    hub_distance_cols.append(col)
out["nearest_major_hub_distance_km"] = (
    out[hub_distance_cols].min(axis=1) if hub_distance_cols else 250.0
)
out["primary_hub_distance_km"] = (
    out[hub_distance_cols[0]] if hub_distance_cols else out["nearest_major_hub_distance_km"]
)
```

becomes one call:

```python
out = hub_distances(out)
```

`data_derived_hubs` and the `_hub_weight` logic are deleted (no other
callers). Net diff: roughly 25 lines added in `config.py`, 10 added and 25
removed in `scoring.py`.

### Primary hub

`primary_hub_distance_km` defaults to the first entry in `UK_DATA_HUBS`
(Slough). The `backup_disaster_recovery` workload uses it as a
"further-is-better" signal; Slough is the right primary because it is the UK's
largest commercial cluster.

### Untouched

`latency_score_raw = clamp(10 - nearest_major_hub_distance_km / 45)` stays as
written. The 45 km divisor is its own argument and out of scope here.

## Verification

The cached `data/processed/candidate_region_features.csv` is from before the
dynamic-candidates code was introduced (no `candidate_source` column). The
check at `orchestrator.load_or_build_features` will trigger a feature rebuild
on the next run. If the LAD boundaries raw file is missing, the rebuild will
raise and the pipeline will halt; in that case rerun `data_download.sh`
first.

Steps:

1. Baseline run before the change, into a fresh file:

   ```bash
   python -m data_centre_site_selector.main \
     --no-agents --rebuild-features --json \
     > /tmp/hubs_before.json
   ```

2. Apply the change.

3. After-run with the same flags into `/tmp/hubs_after.json`.

4. The following columns are expected to differ between the two runs (because
   they depend on `latency_score_raw` directly or transitively):

   - `distance_to_*_km` columns (renamed and recomputed)
   - `nearest_major_hub_distance_km`
   - `primary_hub_distance_km`
   - `latency_score_raw`
   - `infrastructure_score_raw` (latency is 25% of its blend)
   - `estimated_capex_per_mw_gbp` (depends on `infrastructure_score_raw`)
   - `cost_score_raw` (derived from capex)
   - `overall_score` (workload-weighted blend including latency)
   - `production_score` (depends on all of the above)

5. The following columns must be byte-identical between the two runs:

   - `energy_score_raw`, `water_score_raw`, `climate_score_raw`,
     `resilience_score_raw`, `land_score_raw`, `planning_risk_score_raw`
   - `co2_score_raw`, `population_strain_score_raw`,
     `political_favour_score_raw`, `land_use_score_raw`
   - all raw feature columns (`renewable_capacity_*`, `brownfield_*`,
     `nearest_gsp_distance_km`, etc.)

6. Sanity-check distances:
   - Slough LAD ≈ 0 km from the Slough hub.
   - Tower Hamlets ≈ 0–3 km from London Docklands.
   - Manchester LAD ≈ 0 km from the Manchester hub.
   - Highland and Western Isles: nearest hub Edinburgh, distance 200–400 km,
     `latency_score_raw` in the 1–6 range. This is the correct shape, not a
     bug.

## Out of scope

- `latency_score_raw` formula and the 45 km divisor
- Resilience, water, climate, political-favour, cost axes
- LLM `HubResearchAgent` that annotates the hub list (next change)
- Adding tests for `scoring.py` (separate follow-up)
- Anything in `src/planning/`, `src/rl/`, `src/preferences/`, `src/reports/`

## After implementation

No commit from me. Unified diff goes to chat for review. You decide whether
to stage and commit.

## Follow-up changes queued (separate plans)

1. LLM `HubResearchAgent` that annotates each hub with operator presence,
   grid status, recent announcements, with source URLs and confidence. This
   is where the multi-agent layer adds signals the CSV cannot give.
2. Sensitivity check on the 45 km latency divisor.
3. Resilience fix: either always cache flood data or replace the flood-only
   resilience proxy so the axis carries information by default.
