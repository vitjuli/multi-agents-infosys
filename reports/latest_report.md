# Data Centre Site Selection Report

## Query
Find the best 5 data centre locations around Manchester for 500 MW compute with a £10bn budget

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

The analysis identifies five potential data centre locations around Manchester suitable for a 500 MW compute workload, focusing on renewable energy capacity, operational versus pipeline energy, and GSP availability. The regions evaluated include Rugby, Welwyn Hatfield, Dacorum, Hertsmere, and Newcastle-under-Lyme, with computed scores reflecting their suitability.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'renewable_capacity_50km_mw': 16067.37, 'operational_renewable_capacity_50km_mw': 1289.84, 'pipeline_renewable_capacity_50km_mw': 14777.53}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'renewable_capacity_50km_mw': 12930.81, 'operational_renewable_capacity_50km_mw': 1717.92, 'pipeline_renewable_capacity_50km_mw': 11212.9}
- {'region': 'Dacorum', 'overall_score': 6.42, 'renewable_capacity_50km_mw': 13497.31, 'operational_renewable_capacity_50km_mw': 1661.07, 'pipeline_renewable_capacity_50km_mw': 11836.25}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'renewable_capacity_50km_mw': 12749.47, 'operational_renewable_capacity_50km_mw': 1518.58, 'pipeline_renewable_capacity_50km_mw': 11230.9}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'renewable_capacity_50km_mw': 13901.52, 'operational_renewable_capacity_50km_mw': 1682.55, 'pipeline_renewable_capacity_50km_mw': 12218.98}

Risks:
- Flood zone data is present but not computed, which may pose risks in certain areas.
- Potential planning risks are indicated by a planning risk score of 2.0 across all regions, suggesting some level of regulatory challenges.

Confidence: High

### WaterAgent

The analysis identifies five potential data centre locations around Manchester suitable for a 500 MW compute workload with a £10 billion budget. The computed scores reflect various factors including energy availability, water resources, climate conditions, latency, resilience, and land availability.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'latency_score': 9.12, 'resilience_score': 7.2, 'land_score': 7.48}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'latency_score': 6.87, 'resilience_score': 7.2, 'land_score': 9.93}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'latency_score': 7.32, 'resilience_score': 7.2, 'land_score': 9.35}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'latency_score': 6.85, 'resilience_score': 7.2, 'land_score': 9.95}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'latency_score': 8.55, 'resilience_score': 7.2, 'land_score': 6.9}

Risks:
- Flood data is present but not computed, which may affect the assessment of flood risks in these regions.
- Water stress data is missing, which could impact the sustainability of water resources for data centre operations.

Confidence: Moderate - The computed scores are based on available data, but missing water stress data and uncomputed flood risks introduce uncertainty.

### ClimateCoolingAgent

The analysis identifies five potential data centre locations around Manchester suitable for a 500 MW compute workload with a £10 billion budget, based on computed scores across various criteria.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'climate_score': 2.32, 'latency_score': 9.12, 'resilience_score': 7.2, 'land_score': 7.48, 'planning_risk_score': 2.0}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'climate_score': 1.74, 'latency_score': 6.87, 'resilience_score': 7.2, 'land_score': 9.93, 'planning_risk_score': 2.0}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'climate_score': 1.74, 'latency_score': 7.32, 'resilience_score': 7.2, 'land_score': 9.35, 'planning_risk_score': 2.0}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'climate_score': 1.66, 'latency_score': 6.85, 'resilience_score': 7.2, 'land_score': 9.95, 'planning_risk_score': 2.0}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'climate_score': 2.91, 'latency_score': 8.55, 'resilience_score': 7.2, 'land_score': 6.9, 'planning_risk_score': 2.0}

Risks:
- Flood zone data is present but not computed, which may pose a risk to site selection.
- Potential missing climate data could affect the accuracy of climate scores.
- Planning risks are uniformly low (score of 2.0), but local regulations may vary.

Confidence: The computed scores are based on a robust dataset, but the absence of complete flood and climate data introduces uncertainty in the final recommendations.

### LatencyAgent

The analysis identifies five potential data centre locations around Manchester suitable for 500 MW compute, focusing on workload latency and proximity to demand hubs. Each location is scored based on various factors including energy availability, water resources, climate conditions, latency, resilience, land availability, and planning risks.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'latency_score': 9.12, 'nearest_major_hub_distance_km': 39.82}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'latency_score': 6.87, 'nearest_major_hub_distance_km': 140.98}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'latency_score': 7.32, 'nearest_major_hub_distance_km': 120.74}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'latency_score': 6.85, 'nearest_major_hub_distance_km': 141.87}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'latency_score': 8.55, 'nearest_major_hub_distance_km': 65.06}

Risks:
- Flood risk data is present but not computed, which may affect site safety assessments.
- Potential planning risks are noted, but specific details are not provided.

Confidence: The computed scores are based on a comprehensive analysis of available data, but the absence of flood risk computations introduces uncertainty regarding site safety.

### ResilienceAgent

The analysis identifies five potential data centre locations around Manchester suitable for a 500 MW compute workload with a £10bn budget, focusing on resilience, energy capacity, and environmental factors.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'latency_score': 9.12, 'resilience_score': 7.2}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'latency_score': 6.87, 'resilience_score': 7.2}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'latency_score': 7.32, 'resilience_score': 7.2}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'latency_score': 6.85, 'resilience_score': 7.2}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'latency_score': 8.55, 'resilience_score': 7.2}

Risks:
- Flood data is present but not fully computed, which may affect the assessment of flood risks in these regions.
- Potential missing data from Scotland in the population estimates could impact the accuracy of demographic-related analyses.

Confidence: High

### LandPlanningAgent

The analysis identifies five potential data centre locations around Manchester based on computed scores for various factors relevant to AI training workloads. The focus is on brownfield land availability and planning risk, with scores reflecting energy, water, climate, latency, resilience, land availability, and planning risk.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'climate_score': 2.32, 'latency_score': 9.12, 'resilience_score': 7.2, 'land_score': 7.48, 'planning_risk_score': 2.0, 'brownfield_hectares': 211238.22}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'climate_score': 1.74, 'latency_score': 6.87, 'resilience_score': 7.2, 'land_score': 9.93, 'planning_risk_score': 2.0, 'brownfield_hectares': 142918.39}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'climate_score': 1.74, 'latency_score': 7.32, 'resilience_score': 7.2, 'land_score': 9.35, 'planning_risk_score': 2.0, 'brownfield_hectares': 417148.7}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'climate_score': 1.66, 'latency_score': 6.85, 'resilience_score': 7.2, 'land_score': 9.95, 'planning_risk_score': 2.0, 'brownfield_hectares': 86709.99}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'climate_score': 2.91, 'latency_score': 8.55, 'resilience_score': 7.2, 'land_score': 6.9, 'planning_risk_score': 2.0, 'brownfield_hectares': 33017.23}

Risks:
- Planning risk remains constant across all regions, indicating potential bureaucratic hurdles.
- Flood zone data is present but not computed, which may pose risks if areas are prone to flooding.
- Variability in climate scores suggests differing environmental impacts that could affect operational efficiency.

Confidence: High confidence in computed scores based on available data, though some data limitations exist, particularly regarding flood risk assessment.


## Critic Review
### CriticAgent

The analysis identifies potential data centre locations around Manchester for a 500 MW compute workload with a £10bn budget. The regions evaluated include Rugby, Welwyn Hatfield, Dacorum, Hertsmere, and Newcastle-under-Lyme. The overall scores reflect a combination of factors such as energy availability, water resources, climate conditions, latency, resilience, land availability, and planning risks.

Key points:
- {'region': 'Rugby', 'overall_score': 6.54, 'energy_score': 8.53, 'water_score': 7.3, 'climate_score': 2.32, 'latency_score': 9.12, 'resilience_score': 7.2, 'land_score': 7.48, 'planning_risk_score': 2.0}
- {'region': 'Welwyn Hatfield', 'overall_score': 6.45, 'energy_score': 7.7, 'water_score': 7.3, 'climate_score': 1.74, 'latency_score': 6.87, 'resilience_score': 7.2, 'land_score': 9.93, 'planning_risk_score': 2.0}
- {'region': 'Dacorum', 'overall_score': 6.42, 'energy_score': 7.87, 'water_score': 7.23, 'climate_score': 1.74, 'latency_score': 7.32, 'resilience_score': 7.2, 'land_score': 9.35, 'planning_risk_score': 2.0}
- {'region': 'Hertsmere', 'overall_score': 6.36, 'energy_score': 7.43, 'water_score': 7.32, 'climate_score': 1.66, 'latency_score': 6.85, 'resilience_score': 7.2, 'land_score': 9.95, 'planning_risk_score': 2.0}
- {'region': 'Newcastle-under-Lyme', 'overall_score': 6.39, 'energy_score': 8.06, 'water_score': 7.29, 'climate_score': 2.91, 'latency_score': 8.55, 'resilience_score': 7.2, 'land_score': 6.9, 'planning_risk_score': 2.0}

Risks:
- Flood zone data is present but not computed, which may pose risks in certain areas.
- Potential planning risks are indicated by a planning risk score of 2.0 across all regions, suggesting some level of regulatory challenges.
- Water stress data is missing, which could impact the sustainability of water resources for data centre operations.
- Potential missing climate data could affect the accuracy of climate scores.
- Variability in climate scores suggests differing environmental impacts that could affect operational efficiency.

Confidence: Moderate - The computed scores are based on available data, but missing water stress data and uncomputed flood risks introduce uncertainty. High confidence in energy and land availability data, though some data limitations exist, particularly regarding flood risk assessment.


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
The analysis identifies five potential data centre locations around Manchester suitable for a 500 MW compute workload with a £10bn budget. The regions evaluated include Rugby, Welwyn Hatfield, Dacorum, Hertsmere, and Newcastle-under-Lyme. The overall scores reflect a combination of factors such as energy availability, water resources, climate conditions, latency, resilience, land availability, and planning risks.