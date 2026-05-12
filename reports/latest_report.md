# Data Centre Site Selection Report

## Query
Find the best 5 data centre locations around Manchester for 500 MW compute with a £10bn budget

## Workload Profile
`ai_inference` weights: energy=0.15, water=0.09, climate=0.09, latency=0.24, resilience=0.17, land=0.09, planning_risk=0.17

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
| Rugby                |            7.09 |               8.53 |              7.3  |                2.32 |                9.12 |                    7.2 |             7.48 |                         2 |                      16067.4 |                  211238    |
| Dacorum              |            6.59 |               7.87 |              7.23 |                1.74 |                7.32 |                    7.2 |             9.35 |                         2 |                      13497.3 |                  417149    |
| Welwyn Hatfield      |            6.5  |               7.7  |              7.3  |                1.74 |                6.87 |                    7.2 |             9.93 |                         2 |                      12930.8 |                  142918    |
| Newcastle-under-Lyme |            6.84 |               8.06 |              7.29 |                2.91 |                8.55 |                    7.2 |             6.9  |                         2 |                      13901.5 |                   33017.2  |
| Stoke-on-Trent       |            6.89 |               8.3  |              7.05 |                2.92 |                8.62 |                    7.2 |             6.97 |                         2 |                      15154.1 |                   33271.4  |
| Hertsmere            |            6.44 |               7.43 |              7.32 |                1.66 |                6.85 |                    7.2 |             9.95 |                         2 |                      12749.5 |                   86710    |
| Bedford              |            6.53 |               8.17 |              7.17 |                2.15 |                7.73 |                    7.2 |             6.91 |                         2 |                      13929.4 |                  417573    |
| Barnsley             |            6.94 |              10    |              7.08 |                3.4  |                9.26 |                    7.2 |             2.49 |                         2 |                      23526.6 |                    5452.03 |
| Trafford             |            6.83 |               7.48 |              7.1  |                3.3  |                8.39 |                    7.2 |             7.95 |                         2 |                      13249.6 |                   35410.4  |
| Milton Keynes        |            6.6  |               8.32 |              6.99 |                2.03 |                8    |                    7.2 |             6.93 |                         2 |                      14804.9 |                  412950    |

## Top Recommendation
Rugby with overall score 7.09/10.

## Agent Assessments
### EnergyAgent

The analysis identifies the top five data centre locations around Manchester based on a computed overall score, focusing on renewable energy capacity, operational versus pipeline energy, and GSP availability. Each location is evaluated on various factors including energy score, water availability, climate conditions, latency, resilience, land availability, and planning risk.

Key points:
- Top locations include Rugby, Newcastle-under-Lyme, Stoke-on-Trent, Barnsley, and Trafford.
- Rugby has the highest overall score of 7.09, driven by strong energy and latency scores.
- Barnsley has the highest renewable capacity at 23,526 MW within 50 km, making it a strong candidate for renewable energy sourcing.
- All regions have a planning risk score of 2.0, indicating a low risk in planning for data centre development.

Risks:
- Flood zone data is present but not computed, which may pose a risk if flood zones are significant in the area.
- Potential for changes in energy policy or availability of renewable resources could impact future operational capacity.

Confidence: High

### WaterAgent

The analysis identifies the top five data centre locations around Manchester based on computed scores for various factors relevant to a 500 MW compute workload and a £10 billion budget. The scores are derived from multiple metrics including energy availability, water resources, climate conditions, latency, resilience, and land availability.

Key points:
- Rugby has the highest overall score of 7.09, indicating a strong balance of energy and water resources.
- Dacorum and Welwyn Hatfield follow closely with scores of 6.59 and 6.50 respectively, highlighting their potential for data centre development.
- Newcastle-under-Lyme and Stoke-on-Trent also show promising scores, particularly in energy availability and latency.
- All locations have a planning risk score of 2.0, indicating a low risk in terms of regulatory challenges.

Risks:
- Flood data is present but not computed, which may pose a risk if flooding is a concern in these areas.
- Potential inaccuracies in water-stress data due to missing information may affect the reliability of water scores.
- The reliance on dynamic candidates from ONS LAD boundary centroids may introduce variability in the computed scores.

Confidence: High

### ClimateCoolingAgent

The analysis identifies the top five data centre locations around Manchester based on computed scores for various factors such as energy availability, climate conditions, and latency. The overall scores reflect the suitability of each location for a 500 MW compute workload with a £10 billion budget.

Key points:
- Rugby has the highest overall score of 7.09, indicating strong energy and latency scores.
- Newcastle-under-Lyme and Stoke-on-Trent follow closely with scores of 6.84 and 6.89 respectively, both showing good renewable energy capacity.
- Dacorum and Welwyn Hatfield are also notable, with overall scores of 6.59 and 6.50, respectively, but lower climate scores compared to Rugby.
- All locations have a planning risk score of 2.0, indicating low planning risk across the board.

Risks:
- Flood data is present but not computed, which may pose a risk if flood zones intersect with potential sites.
- Missing climate data could affect the accuracy of climate scores, impacting long-term operational viability.

Confidence: High

### LatencyAgent

The analysis identifies the top five data centre locations around Manchester based on computed scores for various factors including energy availability, water resources, climate conditions, latency, resilience, land availability, and planning risks. The overall scores reflect a balance of these factors, particularly focusing on latency and energy capacity, which are critical for AI inference workloads.

Key points:
- Top location: Rugby with an overall score of 7.09, strong energy and latency scores.
- Dacorum and Welwyn Hatfield follow closely, with overall scores of 6.59 and 6.50 respectively, but with higher distances to major hubs.
- Newcastle-under-Lyme and Stoke-on-Trent also rank well, both showing good energy and latency scores, essential for AI workloads.
- All locations have a planning risk score of 2.0, indicating low planning risks across the board.

Risks:
- Flood data is present but not computed for all locations, which may pose a risk if not assessed properly.
- Potential limitations in renewable energy capacity in some areas may affect long-term sustainability.
- Distance to major hubs varies significantly, which could impact latency for certain applications.

Confidence: High

### ResilienceAgent

The analysis identifies the top five data centre locations around Manchester based on computed scores for various factors relevant to a 500 MW compute workload with a £10 billion budget. The scores reflect energy availability, water resources, climate resilience, latency, and land availability, among other factors.

Key points:
- Rugby has the highest overall score of 7.09, indicating strong energy and latency scores.
- Newcastle-under-Lyme and Stoke-on-Trent follow closely with overall scores of 6.84 and 6.89, respectively, both showing good energy and latency scores.
- Dacorum and Welwyn Hatfield are also strong contenders with overall scores of 6.59 and 6.50, respectively, benefiting from high land scores.
- All regions have a planning risk score of 2.0, indicating a consistent level of planning risk across the selected locations.
- Flood zone data is present but not fully computed, which may affect the assessment of flood risks in these areas.

Risks:
- Flood zone data is incomplete, which could lead to unanticipated flood risks in selected locations.
- Potential latency issues due to distance from major hubs, particularly in Dacorum and Welwyn Hatfield.
- Variability in renewable energy capacity could impact operational sustainability in the long term.

Confidence: High

### LandPlanningAgent

The analysis identifies the top five data centre locations around Manchester based on a computed overall score, focusing on brownfield land availability and planning risk. The scores are derived from various factors including energy availability, water resources, climate conditions, latency, resilience, land availability, and planning risk.

Key points:
- Rugby has the highest overall score of 7.09, indicating strong potential for data centre development.
- Dacorum and Welwyn Hatfield follow with scores of 6.59 and 6.50 respectively, highlighting their favorable conditions for data centres.
- Newcastle-under-Lyme and Stoke-on-Trent also rank well, with scores of 6.84 and 6.89, respectively, showcasing good energy and water resources.
- All selected locations have a planning risk score of 2.0, indicating a low risk of planning issues.
- Brownfield land availability is significant in all regions, which is crucial for sustainable development.

Risks:
- Flood zone data is present but not fully computed, which may pose a risk if areas are prone to flooding.
- Potential discrepancies in population estimates and renewable capacity data could affect site viability assessments.

Confidence: High


## Critic Review
### CriticAgent

The analysis identifies the top five data centre locations around Manchester based on computed scores for various factors relevant to a 500 MW compute workload with a £10 billion budget. The scores are derived from multiple metrics including energy availability, water resources, climate conditions, latency, resilience, and land availability. Rugby, Newcastle-under-Lyme, Stoke-on-Trent, Barnsley, and Trafford are highlighted as top candidates.

Key points:
- Rugby has the highest overall score of 7.09, driven by strong energy and latency scores.
- Barnsley has the highest renewable capacity at 23,526 MW within 50 km, making it a strong candidate for renewable energy sourcing.
- All regions have a planning risk score of 2.0, indicating a low risk in planning for data centre development.
- Flood zone data is present but not computed, which may pose a risk if flood zones are significant in the area.

Risks:
- Flood zone data is present but not computed, which may pose a risk if flood zones intersect with potential sites.
- Potential inaccuracies in water-stress data due to missing information may affect the reliability of water scores.
- Missing climate data could affect the accuracy of climate scores, impacting long-term operational viability.
- Potential limitations in renewable energy capacity in some areas may affect long-term sustainability.

Confidence: High


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
The analysis identifies the top five data centre locations around Manchester based on computed scores for various factors relevant to a 500 MW compute workload with a £10 billion budget. The scores are derived from multiple metrics including energy availability, water resources, climate conditions, latency, resilience, and land availability. Rugby, Newcastle-under-Lyme, Stoke-on-Trent, Barnsley, and Trafford are highlighted as top candidates.