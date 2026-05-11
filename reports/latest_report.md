# Data Centre Site Selection Report

## Query
Find the best UK location for a 100 MW AI training data centre

## Workload Profile
`ai_training` weights: energy=0.28, water=0.14, climate=0.20, latency=0.06, resilience=0.12, land=0.16, planning_risk=0.10

## Dataset Availability
- ONS LAD boundaries: used if geospatial dependencies are installed; otherwise LAD hints are retained.
- DESNZ REPD renewables: used for radius capacity features when coordinates are detected.
- NESO GSP regions: used if geospatial dependencies are installed.
- EA flood zones: cached in feature table only when explicitly built with flood processing.
- ONS population: joined where LAD code/name matches the England/Wales workbook.
- Brownfield land/site: point-based radius counts and hectares are computed where point WKT is present.
- Diagnostics: Computed LAD joins using ONS LAD boundaries. | Joined population estimates from sheet MYE2 - Persons; Scotland may be missing in England/Wales workbook. | Computed renewable radius features from DESNZ REPD sheet REPD. | Computed GSP joins from Proj_4326/GSP_regions_4326_20250102.geojson. | Flood ZIP present but not loaded by default because it is large; rerun build with --include-flood to compute. | Computed brownfield radius features from available point columns; England-only caveat applies.

## Ranked Candidates
| region                        |   overall_score |   energy_score_raw |   water_score_raw |   climate_score_raw |   latency_score_raw |   resilience_score_raw |   land_score_raw |   planning_risk_score_raw |   renewable_capacity_50km_mw |   brownfield_hectares_50km |
|:------------------------------|----------------:|-------------------:|------------------:|--------------------:|--------------------:|-----------------------:|-----------------:|--------------------------:|-----------------------------:|---------------------------:|
| Leeds / Yorkshire             |            6.83 |              10    |                 7 |                5.22 |                8.71 |                    7.2 |             3.41 |                         2 |                     24187.3  |                    3972.41 |
| Manchester                    |            6.63 |               6.36 |                 7 |                4.5  |               10    |                    7.2 |             9.01 |                         2 |                     11645.4  |                   35334.2  |
| Edinburgh / Central Scotland  |            6.34 |               7.92 |                 7 |               10    |                3.74 |                    7.2 |             0    |                         2 |                     13842    |                       0    |
| Birmingham / West Midlands    |            6.32 |               9.5  |                 7 |                2.29 |               10    |                    7.2 |             4.39 |                         2 |                     17434.9  |                    5192.16 |
| Teesside / North East England |            5.3  |               5.37 |                 7 |                6.93 |                6.93 |                    7.2 |             0.84 |                         2 |                      9755.32 |                    1177.73 |

## Top Recommendation
Leeds / Yorkshire with overall score 6.83/10.

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