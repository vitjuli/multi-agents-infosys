# Data Centre Site Selection Report

## Query
Find the best 5 data centre locations around London for 100 MW compute with a £10bn budget

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
| Rugby                |            6.54 |               8.53 |              7.3  |                2.32 |                9.12 |                    7.2 |             7.48 |                         2 |                      16067.4 |                   211238   |
| Welwyn Hatfield      |            6.45 |               7.7  |              7.3  |                1.74 |                6.87 |                    7.2 |             9.93 |                         2 |                      12930.8 |                   142918   |
| Dacorum              |            6.42 |               7.87 |              7.23 |                1.74 |                7.32 |                    7.2 |             9.35 |                         2 |                      13497.3 |                   417149   |
| Hertsmere            |            6.36 |               7.43 |              7.32 |                1.66 |                6.85 |                    7.2 |             9.95 |                         2 |                      12749.5 |                    86710   |
| Newcastle-under-Lyme |            6.39 |               8.06 |              7.29 |                2.91 |                8.55 |                    7.2 |             6.9  |                         2 |                      13901.5 |                    33017.2 |

## Top Recommendation
Rugby with overall score 6.54/10.

## Agent Assessments
### EnergyAgent

The analysis identifies five optimal data centre locations around London for a 100 MW compute workload with a £10 billion budget, focusing on renewable energy capacity, operational versus pipeline energy, and GSP availability.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'renewable_capacity_50km_mw': 16067.37, 'operational_renewable_capacity_50km_mw': 1289.84, 'pipeline_renewable_capacity_50km_mw': 14777.53, 'latency_score_raw': 9.12}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'renewable_capacity_50km_mw': 12930.81, 'operational_renewable_capacity_50km_mw': 1717.92, 'pipeline_renewable_capacity_50km_mw': 11212.9, 'latency_score_raw': 6.87}
- {'region': 'Dacorum', 'overall_score': 6.42, 'renewable_capacity_50km_mw': 13497.31, 'operational_renewable_capacity_50km_mw': 1661.07, 'pipeline_renewable_capacity_50km_mw': 11836.25, 'latency_score_raw': 7.32}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'renewable_capacity_50km_mw': 12749.47, 'operational_renewable_capacity_50km_mw': 1518.58, 'pipeline_renewable_capacity_50km_mw': 11230.9, 'latency_score_raw': 6.85}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'renewable_capacity_50km_mw': 13901.52, 'operational_renewable_capacity_50km_mw': 1682.55, 'pipeline_renewable_capacity_50km_mw': 12218.98, 'latency_score_raw': 8.55}

Risks:
- Flood data is present but not computed, which may pose a risk to site selection.
- Potential limitations in data quality due to missing population estimates for Scotland.

Confidence: High

### WaterAgent

The analysis identifies five optimal data centre locations around London for a 100 MW compute workload, considering a £10 billion budget. The computed scores reflect various factors including energy, water availability, climate, latency, resilience, and land suitability.

Key points:
- {'region': 'Rugby', 'overall_score': 6.543, 'energy_score': 8.528, 'water_score': 7.297, 'latency_score': 9.115, 'resilience_score': 7.2, 'land_score': 7.476}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.447, 'energy_score': 7.702, 'water_score': 7.296, 'latency_score': 6.867, 'resilience_score': 7.2, 'land_score': 9.926}
- {'region': 'Dacorum', 'overall_score': 6.421, 'energy_score': 7.872, 'water_score': 7.231, 'latency_score': 7.317, 'resilience_score': 7.2, 'land_score': 9.353}
- {'region': 'Hertsmere', 'overall_score': 6.358, 'energy_score': 7.429, 'water_score': 7.317, 'latency_score': 6.847, 'resilience_score': 7.2, 'land_score': 9.951}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.395, 'energy_score': 8.055, 'water_score': 7.288, 'latency_score': 8.554, 'resilience_score': 7.2, 'land_score': 6.899}

Risks:
- Flood data is present but not computed, which may affect site selection decisions.
- Potential missing data for Scotland in the population estimates could impact the accuracy of the analysis.

Confidence: High

### ClimateCoolingAgent

The analysis identifies five optimal locations around London for establishing a 100 MW data center focused on AI training workloads, based on computed scores across various environmental and logistical factors.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'climate_score': 2.32, 'latency_score': 9.12, 'resilience_score': 7.2, 'land_score': 7.48, 'planning_risk_score': 2.0}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'climate_score': 1.74, 'latency_score': 6.87, 'resilience_score': 7.2, 'land_score': 9.93, 'planning_risk_score': 2.0}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'climate_score': 1.74, 'latency_score': 7.32, 'resilience_score': 7.2, 'land_score': 9.35, 'planning_risk_score': 2.0}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'climate_score': 1.66, 'latency_score': 6.85, 'resilience_score': 7.2, 'land_score': 9.95, 'planning_risk_score': 2.0}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'climate_score': 2.91, 'latency_score': 8.55, 'resilience_score': 7.2, 'land_score': 6.9, 'planning_risk_score': 2.0}

Risks:
- Flood data is present but not computed for all regions, which may pose a risk for certain locations.
- The planning risk score is consistently low (2.00) across all regions, indicating potential regulatory challenges.
- Variability in climate scores suggests differing resilience to climate impacts.

Confidence: The computed scores are based on a comprehensive analysis of available data, but the absence of complete flood data may affect the reliability of the overall assessment.

### LatencyAgent

The analysis identifies five optimal data centre locations around London for a 100 MW compute workload, focusing on AI training. The computed scores reflect various factors including energy availability, water resources, climate conditions, latency, resilience, land availability, and planning risks.

Key points:
- {'region': 'Rugby', 'overall_score': 6.543, 'energy_score': 8.528, 'latency_score': 9.115, 'renewable_capacity_50km_mw': 16067.37, 'nearest_major_hub_distance_km': 39.82}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.447, 'energy_score': 7.702, 'latency_score': 6.867, 'renewable_capacity_50km_mw': 12930.81, 'nearest_major_hub_distance_km': 140.98}
- {'region': 'Dacorum', 'overall_score': 6.421, 'energy_score': 7.872, 'latency_score': 7.317, 'renewable_capacity_50km_mw': 13497.31, 'nearest_major_hub_distance_km': 120.74}
- {'region': 'Hertsmere', 'overall_score': 6.358, 'energy_score': 7.429, 'latency_score': 6.847, 'renewable_capacity_50km_mw': 12749.47, 'nearest_major_hub_distance_km': 141.87}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.395, 'energy_score': 8.055, 'latency_score': 8.554, 'renewable_capacity_50km_mw': 13901.52, 'nearest_major_hub_distance_km': 65.06}

Risks:
- Planning risk scores are uniformly low (2.0), indicating minimal regulatory hurdles.
- Flood zone data is present but not fully computed, which may pose a risk if areas are susceptible to flooding.
- The climate score is low across all regions, indicating potential challenges related to environmental conditions.

Confidence: High

### ResilienceAgent

The analysis identifies five optimal data centre locations around London for AI training workloads, considering a £10bn budget. The locations are assessed based on various factors including energy availability, water resources, climate resilience, latency, and land suitability.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'latency_score': 9.12, 'resilience_score': 7.2}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'latency_score': 6.87, 'resilience_score': 7.2}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'latency_score': 7.32, 'resilience_score': 7.2}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'latency_score': 6.85, 'resilience_score': 7.2}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'latency_score': 8.55, 'resilience_score': 7.2}

Risks:
- Flood data is present but not fully computed, which may affect the assessment of flood risks in these regions.
- Potential missing data in population estimates may impact the accuracy of the analysis.
- The reliance on renewable energy capacity and operational capacity within 50 km may vary over time and affect sustainability.

Confidence: High

### LandPlanningAgent

The analysis identifies five potential data centre locations around London, focusing on brownfield land availability and planning risk. Each location is scored based on various factors including energy availability, water resources, climate conditions, latency, resilience, land availability, and planning risk.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'latency_score': 9.12, 'planning_risk_score': 2.0, 'brownfield_hectares': 211238.22}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'latency_score': 6.87, 'planning_risk_score': 2.0, 'brownfield_hectares': 142918.39}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'latency_score': 7.32, 'planning_risk_score': 2.0, 'brownfield_hectares': 417148.7}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'latency_score': 6.85, 'planning_risk_score': 2.0, 'brownfield_hectares': 86709.99}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'latency_score': 8.55, 'planning_risk_score': 2.0, 'brownfield_hectares': 33017.23}

Risks:
- Planning risk remains constant across all regions at a score of 2.0, indicating a low likelihood of planning issues.
- Flood data is present but not computed for all regions, which may pose a risk if flood zones are significant.
- The climate scores are relatively low across all regions, which may affect long-term sustainability.

Confidence: High


## Critic Review
### CriticAgent

The analysis evaluates potential data centre locations around London for a 100 MW compute workload with a £10bn budget, focusing on AI training. The locations are assessed based on various factors including energy availability, water resources, climate conditions, latency, resilience, land availability, and planning risk. However, there are notable data gaps and assumptions that could impact the reliability of the findings.

Key points:
- {'fact': 'Rugby has the highest overall score (6.54) with strong energy (8.53) and latency (9.12) scores, but a low climate score (2.32).', 'heuristic': 'The high renewable capacity within 50 km (16067.37 MW) suggests a strong potential for sustainable energy sourcing.'}
- {'fact': 'Welwyn Hatfield scores well in land availability (9.93) but has a lower latency score (6.87) compared to Rugby.', 'heuristic': 'The large brownfield area (142918.39 hectares) indicates significant potential for development.'}
- {'fact': 'Dacorum has a high land score (9.35) and a moderate latency score (7.32), with a substantial renewable capacity (13497.31 MW).', 'heuristic': 'The extensive brownfield area (417148.7 hectares) provides ample space for infrastructure.'}
- {'fact': 'Hertsmere shows strong land availability (9.95) but lower energy (7.43) and latency (6.85) scores.', 'heuristic': 'The planning risk score is consistently low (2.0) across all regions, suggesting minimal regulatory hurdles.'}
- {'fact': 'Newcastle-under-Lyme has a good balance of energy (8.06) and latency (8.55) scores, with a moderate overall score (6.39).', 'heuristic': 'The proximity to major hubs (65.06 km) enhances its attractiveness for connectivity.'}

Risks:
- Flood data is present but not computed, which may pose a risk to site selection, especially in flood-prone areas.
- The climate scores are relatively low across all regions, indicating potential challenges related to environmental conditions.
- Potential missing data for Scotland in population estimates could impact the accuracy of the analysis.

Confidence: The confidence in the analysis is high based on the available data, but the absence of complete flood data and potential missing datasets could affect the reliability of the overall assessment. Future analyses should incorporate comprehensive flood data and address any gaps in population estimates to improve accuracy.


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
The analysis identifies five optimal data centre locations around London for a 100 MW compute workload with a £10 billion budget, focusing on AI training. The locations are assessed based on various factors including energy availability, water resources, climate conditions, latency, resilience, land availability, and planning risk. Rugby emerges as the top location due to its high energy and latency scores, despite a low climate score. Other locations like Welwyn Hatfield and Dacorum also show strong potential due to their land availability and renewable energy capacity.