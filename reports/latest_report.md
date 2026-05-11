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

The analysis identifies Leeds/Yorkshire as the top location for a 100 MW AI training data centre based on computed scores across various factors including renewable energy capacity, operational energy, and general site availability.

Key points:
- top_location: {'region': 'Leeds / Yorkshire', 'overall_score': 6.828, 'renewable_capacity_50km_mw': 24187.26, 'operational_renewable_capacity_50km_mw': 4012.57, 'pipeline_renewable_capacity_50km_mw': 20174.68, 'land_score_raw': 3.41, 'planning_risk_score_raw': 2.0}
- other_locations: [{'region': 'Manchester', 'overall_score': 6.632, 'renewable_capacity_50km_mw': 11645.39}, {'region': 'Edinburgh / Central Scotland', 'overall_score': 6.34, 'renewable_capacity_50km_mw': 13841.96}, {'region': 'Birmingham / West Midlands', 'overall_score': 6.316, 'renewable_capacity_50km_mw': 17434.94}, {'region': 'Teesside / North East England', 'overall_score': 5.297, 'renewable_capacity_50km_mw': 9755.32}]

Risks:
- planning_risk: All regions have a planning risk score of 2.0, indicating a moderate level of planning risk.
- flood_data: Flood zone data is present but not computed, which may pose a risk if not assessed.

Confidence: High confidence in the computed scores based on the available data, but caution is advised regarding uncomputed flood data.

### WaterAgent

The analysis identifies the best locations in the UK for a 100 MW AI training data centre based on computed scores across various factors. The top regions are Leeds/Yorkshire, Manchester, Edinburgh/Central Scotland, Birmingham/West Midlands, and Teesside/North East England.

Key points:
- top_location: {'region': 'Leeds / Yorkshire', 'overall_score': 6.828, 'energy_score': 10.0, 'water_score': 7.0, 'climate_score': 5.215, 'latency_score': 8.713, 'resilience_score': 7.2, 'land_score': 3.409, 'planning_risk_score': 2.0}
- other_locations: [{'region': 'Manchester', 'overall_score': 6.632, 'energy_score': 6.359, 'water_score': 7.0, 'climate_score': 4.504, 'latency_score': 10.0, 'resilience_score': 7.2, 'land_score': 9.01, 'planning_risk_score': 2.0}, {'region': 'Edinburgh / Central Scotland', 'overall_score': 6.34, 'energy_score': 7.921, 'water_score': 7.0, 'climate_score': 10.0, 'latency_score': 3.743, 'resilience_score': 7.2, 'land_score': 0.0, 'planning_risk_score': 2.0}, {'region': 'Birmingham / West Midlands', 'overall_score': 6.316, 'energy_score': 9.496, 'water_score': 7.0, 'climate_score': 2.293, 'latency_score': 10.0, 'resilience_score': 7.2, 'land_score': 4.387, 'planning_risk_score': 2.0}, {'region': 'Teesside / North East England', 'overall_score': 5.297, 'energy_score': 5.375, 'water_score': 7.0, 'climate_score': 6.935, 'latency_score': 6.928, 'resilience_score': 7.2, 'land_score': 0.837, 'planning_risk_score': 2.0}]

Risks:
- flood_data: Flood zone data is present but not computed due to file size limitations, which may pose a risk if the site is in a flood-prone area.
- data_quality: Some data may be missing or incomplete, particularly in Scotland, which could affect the overall assessment.

Confidence: High confidence in computed scores based on available data, but caution is advised due to potential missing flood data and regional discrepancies.

### ClimateCoolingAgent

The analysis identifies Leeds / Yorkshire as the best location for a 100 MW AI training data centre in the UK, based on computed scores across various factors including energy, water, climate, latency, resilience, land availability, and planning risk.

Key points:
- best_location: {'region': 'Leeds / Yorkshire', 'overall_score': 6.828370123055496, 'energy_score': 10.0, 'water_score': 7.0, 'climate_score': 5.2153907708722365, 'latency_score': 8.712632782430486, 'resilience_score': 7.2, 'land_score': 3.4087449813312554, 'planning_risk_score': 2.0}
- other_locations: [{'region': 'Manchester', 'overall_score': 6.632074522235644}, {'region': 'Edinburgh / Central Scotland', 'overall_score': 6.340221979603375}, {'region': 'Birmingham / West Midlands', 'overall_score': 6.316035948674587}, {'region': 'Teesside / North East England', 'overall_score': 5.297284456120575}]

Risks:
- flood_data: Flood data is present but not computed due to large file size. This may pose a risk if the site is in a flood-prone area.
- data_quality: Some data quality notes indicate potential missing data, particularly for Scotland in the England/Wales workbook.

Confidence: High confidence in the computed scores based on available data, but caution is advised regarding the flood data and potential data quality issues.

### LatencyAgent

The analysis identifies Leeds/Yorkshire as the top location for a 100 MW AI training data centre in the UK, based on computed scores across various factors including energy availability, latency, and proximity to major hubs.

Key points:
- top_location: {'region': 'Leeds / Yorkshire', 'overall_score': 6.828, 'distance_to_london_km': 272.43, 'latency_score_raw': 8.71, 'energy_score_raw': 10.0, 'renewable_capacity_50km_mw': 24187.26}
- other_locations: [{'region': 'Manchester', 'overall_score': 6.632, 'distance_to_london_km': 261.98, 'latency_score_raw': 10.0}, {'region': 'Edinburgh / Central Scotland', 'overall_score': 6.34, 'distance_to_london_km': 533.65, 'latency_score_raw': 3.74}, {'region': 'Birmingham / West Midlands', 'overall_score': 6.316, 'distance_to_london_km': 162.5, 'latency_score_raw': 10.0}, {'region': 'Teesside / North East England', 'overall_score': 5.297, 'distance_to_london_km': 348.94, 'latency_score_raw': 6.93}]

Risks:
- flooding: Flood data is present but not fully computed, which may pose risks in certain areas.
- planning_risk: All regions have a planning risk score of 2.0, indicating potential bureaucratic challenges.

Confidence: High confidence in computed scores based on available data, but caution is advised due to incomplete flood data and potential regional discrepancies.

### ResilienceAgent

The analysis identifies the best UK locations for a 100 MW AI training data centre based on computed scores across various factors, including energy availability, climate resilience, and planning risks. Leeds/Yorkshire ranks highest, followed closely by Manchester and Edinburgh/Central Scotland.

Key points:
- top_location: {'region': 'Leeds / Yorkshire', 'overall_score': 6.828, 'energy_score': 10.0, 'water_score': 7.0, 'climate_score': 5.215, 'latency_score': 8.713, 'resilience_score': 7.2, 'land_score': 3.409, 'planning_risk_score': 2.0}
- second_location: {'region': 'Manchester', 'overall_score': 6.632, 'energy_score': 6.359, 'water_score': 7.0, 'climate_score': 4.504, 'latency_score': 10.0, 'resilience_score': 7.2, 'land_score': 9.01, 'planning_risk_score': 2.0}
- third_location: {'region': 'Edinburgh / Central Scotland', 'overall_score': 6.34, 'energy_score': 7.921, 'water_score': 7.0, 'climate_score': 10.0, 'latency_score': 3.743, 'resilience_score': 7.2, 'land_score': 0.0, 'planning_risk_score': 2.0}

Risks:
- flood_zone_data: Flood zone data is present but not fully computed due to large file size, which may affect site selection.
- data_quality: Potential missing data for Scotland in the England/Wales workbook may impact the accuracy of the analysis.

Confidence: High confidence in the computed scores based on available data, but caution is advised due to incomplete flood zone assessments and potential data gaps.

### LandPlanningAgent

The analysis identifies the best UK locations for a 100 MW AI training data centre based on various computed scores, focusing on brownfield land availability and planning risk. Leeds/Yorkshire emerges as the top candidate, followed closely by Manchester and Edinburgh/Central Scotland.

Key points:
- top_location: {'region': 'Leeds / Yorkshire', 'overall_score': 6.828, 'energy_score': 10.0, 'water_score': 7.0, 'climate_score': 5.215, 'latency_score': 8.713, 'resilience_score': 7.2, 'land_score': 3.409, 'planning_risk_score': 2.0, 'brownfield_hectares': 3972.41}
- second_location: {'region': 'Manchester', 'overall_score': 6.632, 'energy_score': 6.359, 'water_score': 7.0, 'climate_score': 4.504, 'latency_score': 10.0, 'resilience_score': 7.2, 'land_score': 9.01, 'planning_risk_score': 2.0, 'brownfield_hectares': 35334.22}
- third_location: {'region': 'Edinburgh / Central Scotland', 'overall_score': 6.34, 'energy_score': 7.921, 'water_score': 7.0, 'climate_score': 10.0, 'latency_score': 3.743, 'resilience_score': 7.2, 'land_score': 0.0, 'planning_risk_score': 2.0, 'brownfield_hectares': 0.0}

Risks:
- Planning risk remains a concern across all regions, with a score of 2.0 indicating potential challenges in obtaining necessary approvals.
- Leeds/Yorkshire has a relatively low land score, which may limit available sites for development.
- Edinburgh has no brownfield hectares available, which could pose a significant barrier for site selection.

Confidence: High confidence in the computed scores based on the available data, though caution is advised regarding planning risks and land availability.


## Critic Review
### CriticAgent

The analysis identifies Leeds/Yorkshire as the top location for a 100 MW AI training data centre in the UK, based on computed scores across various factors. However, there are notable weaknesses and missing datasets that could impact the decision-making process.

Key points:
- Leeds/Yorkshire has the highest overall score (6.828) and the best energy score (10.0).
- Other strong contenders include Manchester (6.632) and Edinburgh/Central Scotland (6.34).
- All regions have a planning risk score of 2.0, indicating moderate planning challenges.
- Flood zone data is present but not fully computed, which may pose risks if sites are in flood-prone areas.

Risks:
- Flood data is not computed due to file size limitations, which may lead to overlooking flood risks.
- Potential missing data for Scotland in the England/Wales workbook could affect the overall assessment.
- The land score for Leeds/Yorkshire is relatively low (3.41), which may limit available sites for development.
- Edinburgh has no brownfield hectares available, posing a significant barrier for site selection.

Confidence: High confidence in the computed scores based on available data, but caution is advised due to incomplete flood data, potential data quality issues, and planning risks.


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
The analysis identifies Leeds/Yorkshire as the best location for a 100 MW AI training data centre in the UK, based on computed scores across various factors including energy availability, water resources, climate conditions, latency, resilience, land availability, and planning risk.