# Data Centre Site Selection Report

## Query
Find the best UK location for a data centre

## Workload Profile
`ai_training` weights: energy=0.28, water=0.14, climate=0.20, latency=0.06, resilience=0.12, land=0.16, planning_risk=0.10

## Dataset Availability
- ONS LAD boundaries: used if geospatial dependencies are installed; otherwise LAD hints are retained.
- DESNZ REPD renewables: used for radius capacity features when coordinates are detected.
- NESO GSP regions: used if geospatial dependencies are installed.
- EA flood zones: cached in feature table only when explicitly built with flood processing.
- ONS population: joined where LAD code/name matches the England/Wales workbook.
- Brownfield land/site: point-based radius counts and hectares are computed where point WKT is present.
- Diagnostics: Generated 361 dynamic candidates from ONS LAD boundary centroids. | Using LAD codes and names from generated boundary-centroid candidates. | Joined population estimates from sheet MYE2 - Persons; Scotland may be missing in England/Wales workbook. | Computed renewable radius features from DESNZ REPD sheet REPD. | Computed GSP joins from Proj_4326/GSP_regions_4326_20250102.geojson. | Flood ZIP present but not loaded by default because it is large; rerun build with --include-flood to compute. | Computed brownfield radius features from available point columns; England-only caveat applies.

## Ranked Candidates
| region               |   overall_score |   energy_score_raw |   water_score_raw |   climate_score_raw |   latency_score_raw |   resilience_score_raw |   land_score_raw |   planning_risk_score_raw |   renewable_capacity_50km_mw |   brownfield_hectares_50km |
|:---------------------|----------------:|-------------------:|------------------:|--------------------:|--------------------:|-----------------------:|-----------------:|--------------------------:|-----------------------------:|---------------------------:|
| Hertsmere            |            6.54 |               7.51 |              7.32 |                1.66 |                9.42 |                    7.2 |             9.95 |                         2 |                      12864   |                    86710   |
| Dacorum              |            6.54 |               7.85 |              7.23 |                1.74 |                9.36 |                    7.2 |             9.35 |                         2 |                      13372.8 |                   417149   |
| Welwyn Hatfield      |            6.51 |               7.4  |              7.3  |                1.74 |                9.32 |                    7.2 |             9.93 |                         2 |                      12213.8 |                   142918   |
| St Albans            |            6.38 |               7.08 |              7.25 |                1.75 |                9.24 |                    7.2 |             9.72 |                         2 |                      12222.7 |                   418010   |
| Newcastle-under-Lyme |            6.45 |               8.17 |              7.29 |                2.91 |                8.82 |                    7.2 |             6.9  |                         2 |                      14246.7 |                    33017.2 |

## Top Recommendation
Hertsmere with overall score 6.54/10.

## Agent Assessments
### EnergyAgent

Deterministic fallback used: OpenAI agents disabled by CLI flag

Key points:
- numeric scoring available
- model explanation unavailable

Risks:
- Review computed features and placeholder assumptions manually.

Confidence: low

### WaterAgent

Deterministic fallback used: OpenAI agents disabled by CLI flag

Key points:
- numeric scoring available
- model explanation unavailable

Risks:
- Review computed features and placeholder assumptions manually.

Confidence: low

### ClimateCoolingAgent

Deterministic fallback used: OpenAI agents disabled by CLI flag

Key points:
- numeric scoring available
- model explanation unavailable

Risks:
- Review computed features and placeholder assumptions manually.

Confidence: low

### LatencyAgent

Deterministic fallback used: OpenAI agents disabled by CLI flag

Key points:
- numeric scoring available
- model explanation unavailable

Risks:
- Review computed features and placeholder assumptions manually.

Confidence: low

### ResilienceAgent

Deterministic fallback used: OpenAI agents disabled by CLI flag

Key points:
- numeric scoring available
- model explanation unavailable

Risks:
- Review computed features and placeholder assumptions manually.

Confidence: low

### LandPlanningAgent

Deterministic fallback used: OpenAI agents disabled by CLI flag

Key points:
- numeric scoring available
- model explanation unavailable

Risks:
- Review computed features and placeholder assumptions manually.

Confidence: low


## Critic Review
### CriticAgent

Deterministic fallback used: OpenAI agents disabled by CLI flag

Key points:
- numeric scoring available
- model explanation unavailable

Risks:
- Review computed features and placeholder assumptions manually.

Confidence: low


## Uncertainties
- Water score is heuristic until water-stress, abstraction, and cooling-water datasets are added.
- Climate score uses latitude as a crude cooling proxy until HadUK-Grid or similar climate data is available.
- Flood-zone processing may be skipped unless the large EA file is explicitly processed and cached.
- Existing data-centre capacity and grid headroom/connection queue data are placeholders or missing.

## Next Data Sources to Add
- Water stress and abstraction licence datasets.
- HadUK-Grid climate normals and heatwave projections.
- DNO/TO grid capacity, connection queue, substation headroom, and constraint datasets.
- Commercial fibre/backbone latency and peering data.
- UK-wide population and business demand data, especially for Scottish candidates.

## Prototype Disclaimer
This is a hackathon prototype using public datasets and heuristic scoring. It is not an investment-grade site-selection tool. Some scores, especially water and climate, are placeholders until appropriate datasets are added.

## Final Recommendation
Deterministic fallback used: OpenAI agents disabled by CLI flag