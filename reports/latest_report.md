# Data Centre Site Selection Report

## Query
Find the best 5 data centre locations around London for 100 MW compute with a £400m budget

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

The analysis identifies the top five data centre locations around London for a 100 MW compute workload with a £400 million budget, focusing on renewable energy capacity, operational versus pipeline energy, and GSP availability.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'renewable_capacity_50km_mw': 16067.37, 'operational_renewable_capacity_50km_mw': 1289.84, 'pipeline_renewable_capacity_50km_mw': 14777.53, 'nearest_major_hub_distance_km': 39.82}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'renewable_capacity_50km_mw': 12930.81, 'operational_renewable_capacity_50km_mw': 1717.92, 'pipeline_renewable_capacity_50km_mw': 11212.9, 'nearest_major_hub_distance_km': 140.98}
- {'region': 'Dacorum', 'overall_score': 6.42, 'renewable_capacity_50km_mw': 13497.31, 'operational_renewable_capacity_50km_mw': 1661.07, 'pipeline_renewable_capacity_50km_mw': 11836.25, 'nearest_major_hub_distance_km': 120.74}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'renewable_capacity_50km_mw': 12749.47, 'operational_renewable_capacity_50km_mw': 1518.58, 'pipeline_renewable_capacity_50km_mw': 11230.9, 'nearest_major_hub_distance_km': 141.87}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'renewable_capacity_50km_mw': 13901.52, 'operational_renewable_capacity_50km_mw': 1682.55, 'pipeline_renewable_capacity_50km_mw': 12218.98, 'nearest_major_hub_distance_km': 65.06}

Risks:
- Flood zone data is present but not computed, which may pose a risk to site selection.
- Potential limitations in operational renewable capacity may affect sustainability goals.

Confidence: High

### WaterAgent

The analysis identifies five potential data centre locations around London suitable for a 100 MW compute workload within a £400 million budget, focusing on energy efficiency, water availability, and resilience.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'latency_score': 9.12, 'resilience_score': 7.2}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'latency_score': 6.87, 'resilience_score': 7.2}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'latency_score': 7.32, 'resilience_score': 7.2}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'latency_score': 6.85, 'resilience_score': 7.2}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'latency_score': 8.55, 'resilience_score': 7.2}

Risks:
- Potential water stress not fully assessed due to missing data.
- Flood zone data is present but not computed, which may pose risks in certain areas.
- Distance from major hubs may affect latency and operational efficiency.

Confidence: Moderate - The computed scores are based on available data, but missing water stress and flood zone assessments introduce uncertainty.

### ClimateCoolingAgent

The analysis identifies five potential data centre locations around London suitable for a 100 MW compute workload with a £400m budget, focusing on energy efficiency, water availability, climate conditions, latency, resilience, land availability, and planning risks.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'climate_score': 2.32, 'latency_score': 9.12, 'resilience_score': 7.2, 'land_score': 7.48, 'planning_risk_score': 2.0}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'climate_score': 1.74, 'latency_score': 6.87, 'resilience_score': 7.2, 'land_score': 9.93, 'planning_risk_score': 2.0}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'climate_score': 1.74, 'latency_score': 7.32, 'resilience_score': 7.2, 'land_score': 9.35, 'planning_risk_score': 2.0}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'climate_score': 1.66, 'latency_score': 6.85, 'resilience_score': 7.2, 'land_score': 9.95, 'planning_risk_score': 2.0}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'climate_score': 2.91, 'latency_score': 8.55, 'resilience_score': 7.2, 'land_score': 6.9, 'planning_risk_score': 2.0}

Risks:
- Flood data is present but not fully computed due to file size limitations.
- Potential missing climate data could affect the accuracy of climate scores.

Confidence: Moderate

### LatencyAgent

The analysis identifies five optimal data centre locations around London for a 100 MW compute workload with a £400 million budget, focusing on energy efficiency, water availability, climate factors, latency, resilience, land availability, and planning risks.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'latency_score': 9.12, 'renewable_capacity_50km_mw': 16067.37}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'latency_score': 6.87, 'renewable_capacity_50km_mw': 12930.81}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'latency_score': 7.32, 'renewable_capacity_50km_mw': 13497.31}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'latency_score': 6.85, 'renewable_capacity_50km_mw': 12749.47}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'latency_score': 8.55, 'renewable_capacity_50km_mw': 13901.52}

Risks:
- Potential planning risks are uniformly low across all regions, but the actual flood data has not been computed for detailed risk assessment.
- Distances to major demand hubs vary significantly, which may impact latency and operational efficiency.

Confidence: The scores are computed based on a comprehensive analysis of various factors, including energy and water availability, climate conditions, and proximity to demand hubs. However, the lack of flood data computation may introduce uncertainty in risk assessments.

### ResilienceAgent

The analysis identifies five optimal data centre locations around London for a 100 MW compute workload with a £400 million budget, focusing on resilience, energy capacity, and environmental factors.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'latency_score': 9.12, 'resilience_score': 7.2, 'land_score': 7.48}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'latency_score': 6.87, 'resilience_score': 7.2, 'land_score': 9.93}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'latency_score': 7.32, 'resilience_score': 7.2, 'land_score': 9.35}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'latency_score': 6.85, 'resilience_score': 7.2, 'land_score': 9.95}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'latency_score': 8.55, 'resilience_score': 7.2, 'land_score': 6.9}

Risks:
- Flood zone data is present but not fully computed, which may affect flood risk assessments.
- Potential missing data in population estimates, particularly for Scotland, could impact demographic analyses.

Confidence: High

### LandPlanningAgent

The analysis identifies five potential data centre locations around London suitable for a 100 MW compute workload, focusing on brownfield land availability and planning risk. The overall scores reflect a combination of energy, water, climate, latency, resilience, land availability, and planning risk metrics.

Key points:
- {'region': 'Rugby', 'overall_score': 6.543, 'brownfield_hectares_50km': 211238.22, 'renewable_capacity_50km_mw': 16067.37, 'planning_risk_score_raw': 2.0}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.447, 'brownfield_hectares_50km': 142918.39, 'renewable_capacity_50km_mw': 12930.81, 'planning_risk_score_raw': 2.0}
- {'region': 'Dacorum', 'overall_score': 6.421, 'brownfield_hectares_50km': 417148.7, 'renewable_capacity_50km_mw': 13497.31, 'planning_risk_score_raw': 2.0}
- {'region': 'Hertsmere', 'overall_score': 6.358, 'brownfield_hectares_50km': 86709.99, 'renewable_capacity_50km_mw': 12749.47, 'planning_risk_score_raw': 2.0}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.395, 'brownfield_hectares_50km': 33017.23, 'renewable_capacity_50km_mw': 13901.52, 'planning_risk_score_raw': 2.0}

Risks:
- Potential planning risks are uniformly low across all regions, but local regulations may still pose challenges.
- Flood data has not been fully computed, which could affect site viability in certain areas.

Confidence: High


## Critic Review
### CriticAgent

The analysis evaluates potential data centre locations around London for a 100 MW compute workload within a £400 million budget. It considers factors such as energy efficiency, water availability, climate conditions, latency, resilience, land availability, and planning risks. However, the analysis is limited by missing flood data and potential gaps in water stress and climate data.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'climate_score': 2.32, 'latency_score': 9.12, 'resilience_score': 7.2, 'land_score': 7.48, 'planning_risk_score': 2.0}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'climate_score': 1.74, 'latency_score': 6.87, 'resilience_score': 7.2, 'land_score': 9.93, 'planning_risk_score': 2.0}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'climate_score': 1.74, 'latency_score': 7.32, 'resilience_score': 7.2, 'land_score': 9.35, 'planning_risk_score': 2.0}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'climate_score': 1.66, 'latency_score': 6.85, 'resilience_score': 7.2, 'land_score': 9.95, 'planning_risk_score': 2.0}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'climate_score': 2.91, 'latency_score': 8.55, 'resilience_score': 7.2, 'land_score': 6.9, 'planning_risk_score': 2.0}

Risks:
- Flood zone data is present but not computed, which may pose a risk to site selection.
- Potential limitations in operational renewable capacity may affect sustainability goals.
- Potential water stress not fully assessed due to missing data.
- Potential missing climate data could affect the accuracy of climate scores.
- Distances to major demand hubs vary significantly, which may impact latency and operational efficiency.

Confidence: Moderate - The computed scores are based on available data, but missing flood, water stress, and climate data introduce uncertainty.


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
The analysis identifies the top five data centre locations around London for a 100 MW compute workload with a £400 million budget. The evaluation considers factors such as energy efficiency, water availability, climate conditions, latency, resilience, land availability, and planning risks. However, the analysis is limited by missing flood data and potential gaps in water stress and climate data.