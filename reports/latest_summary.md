# Production Data-Centre Site Selection Report

## Input Interpretation
Prompt: Find the best 5 data centre locations around Manchester for 500 MW compute with a £10bn budget

Workload: `ai_inference`

Compute: 10.0 MW

Region: England

Budget: GBP 10.00bn

## Suggested Constraints
- Target compute capacity in MW or an expected rack/GPU footprint.
- Region scope: UK-wide, England, Scotland, Wales, Northern Ireland, or a specific UK city/cluster.
- Budget in GBP, ideally separating build capex and annual operating spend.
- Optimisation priorities: CO2, water strain, energy strain, latency, resilience, land reuse, policy support, cost.
- Hard constraints: flood exclusion, brownfield-only, renewable PPA preference, maximum distance to a major hub.

## Nested Search
- UK-wide screening: 361 candidates. Top regions: Rugby, Dacorum, Welwyn Hatfield, Newcastle-under-Lyme, Stoke-on-Trent.
- England screening: 296 candidates. Top regions: Rugby, Dacorum, Welwyn Hatfield, Newcastle-under-Lyme, Stoke-on-Trent.

## Budget And Materials
Recommended centres: 1

Estimated total capex: GBP 87.0m

Estimated annual opex: GBP 11.5m

- estimated_total_capex_gbp: 86950238.27
- estimated_steel_tonnes: 950.0
- estimated_concrete_tonnes: 4200.0
- estimated_copper_tonnes: 120.0
- estimated_cooling_plant_mw_thermal: 12.5

Assumptions:
- Costs are class-5 planning estimates, not supplier quotes.
- Capex includes shell, MEP, grid interconnect, fit-out, security, design, and 18% contingency.
- Material quantities are first-order planning proxies for embodied-carbon and procurement discussion.

## Centre Recommendations
### Rugby
- Coordinates: 52.38228, -1.31828; altitude 0.0 m
- Priority: priority; feasible: True
- Compute allocation: 10.0 MW
- Estimated capex: GBP 87.0m; annual opex: GBP 11.5m
- Summary: Rugby scores 7.74/10 on the production objective, with strongest support from CO2=7.54, population strain=7.70, policy=7.20, infrastructure=8.12.
- Problem: None
- Policy points:
  - AI Growth Zones: UK programme for AI-enabled data centres that can improve access to power and planning support; applications are open-ended and eligibility is site-specific.
  - AI Growth Zone delivery reforms: Policy package includes grid-connection acceleration, planning support, and targeted operating-cost support for qualifying AI Growth Zones.
  - Investment Zone tax sites: Designated Investment Zone tax sites can offer business tax reliefs; candidate-specific eligibility needs GIS validation against official tax-site maps.
  - Freeport and Investment Zone employer NIC relief: Employer Class 1 National Insurance relief may apply in designated Freeport or Investment Zone special tax sites.
  - Freeport SDLT relief: Stamp Duty Land Tax relief may apply for qualifying land purchases in English Freeport tax sites until 30 September 2026.
- Explanation: The planner ranked Rugby by combining deterministic workload scoring with production criteria for carbon, population water/energy strain, political favour, infrastructure, land reuse, resilience, latency, and cost. The weighted profile favours candidates with high renewable capacity, lower community strain, practical grid/GSP access, brownfield availability, and plausible UK policy support. AI Growth Zones: UK programme for AI-enabled data centres that can improve access to power and planning support; applications are open-ended and eligibility is site-specific. AI Growth Zone delivery reforms: Policy package includes grid-connection acceleration, planning support, and targeted operating-cost support for qualifying AI Growth Zones.

## Critic Review
- ScopeCritic: passed; Region scope is UK-constrained and internally consistent.
- BudgetCritic: passed; Budget allocation is internally consistent.
- DataQualityCritic: passed; Water, climate, grid headroom, fibre latency, grants, and tax-site eligibility require stronger site-level datasets before investment decisions.

## Web Policy Research
[{"id": "ws_05700a666b1fa3e9006a0204f9c9b4819390d5fda96ab30171", "action": {"query": "UK government policy grants tax reliefs planning support AI Growth Zones Investment Zones Freeport incentives data centre site selection 2023", "type": "search", "queries": ["UK government policy grants tax reliefs planning support AI Growth Zones Investment Zones Freeport incentives data centre site selection 2023"]}, "status": "completed", "type": "web_search_call"}, {"type": "text", "text": "```json\n{\n  \"agent\": \"PolicyResearchAgent\",\n  \"summary\": \"The UK government has introduced several initiatives to attract investment in data centres, particularly those supporting AI workloads. Key programs include AI Growth Zones, Investment Zones, and Freeports, each offering various incentives such as tax reliefs, planning support, and infrastructure development to facilitate data centre establishment and operation.\",\n  \"key_points\": [\n    {\n      \"title\": \"AI Growth Zones\",\n      \"details\": [\n        \"Launched in November 2025 to support AI-enabled data centres by improving access to power and providing planning assistance.\",\n        \"Offer pricing support mechanisms, including potential reductions in electricity costs for data centres located in specific regions (e.g., up to \u00a324/MWh in Scotland).\",\n        \"Provide planning support through updated national policy guidance, additional planning capacity, and land protection measures to expedite development.\"\n      ],\n      \"source\": \"https://www.gov.uk/government/collections/ai-growth-zones\"\n    },\n    {\n      \"title\": \"Investment Zones\",\n      \"details\": [\n        \"Designated areas offering up to \u00a3160 million over 10 years to attract investment, boost innovation, and create jobs.\",\n        \"Provide tax reliefs, including full business rates relief for eligible new businesses within designated tax sites, and enhanced capital allowances.\",\n        \"Support sectors such as advanced manufacturing, life sciences, and clean energy, with tailored interventions based on local needs.\"\n      ],\n      \"source\": \"https://www.gov.uk/guidance/investment-zones-in-england\"\n    },\n    {\n      \"title\": \"Freeports\",\n      \"details\": [\n        \"Special economic zones offering customs and tax benefits, planning support, and infrastructure development to stimulate trade and investment.\",\n        \"Provide incentives such as Stamp Duty Land Tax relief, business rates relief, and employer National Insurance contributions relief.\",\n        \"Aim to create hubs for global trade, investment, and innovation, fostering collaboration between industry, government, and educational institutions.\"\n      ],\n      \"source\": \"https://www.business.gov.uk/invest-in-uk/investment/freeports-in-the-uk/\"\n    }\n  ],\n  \"risks\": [\n    {\n      \"title\": \"Policy Uncertainty\",\n      \"description\": \"Changes in government policies or political priorities may affect the availability and terms of incentives offered through these programs.\"\n    },\n    {\n      \"title\": \"Regulatory Compliance\",\n      \"description\": \"Navigating the specific requirements and compliance obligations associated with each program can be complex and may require significant administrative effort.\"\n    },\n    {\n      \"title\": \"Infrastructure Limitations\",\n      \"description\": \"Despite incentives, certain regions may face challenges related to existing infrastructure capacity, which could impact the feasibility of establishing large-scale data centres.\"\n    }\n  ],\n  \"confidence\": \"High\",\n  \"sources\": [\n    \"https://www.gov.uk/government/collections/ai-growth-zones\",\n    \"https://www.gov.uk/guidance/investment-zones-in-england\",\n    \"https://www.business.gov.uk/invest-in-uk/investment/freeports-in-the-uk/\"\n  ]\n}\n``` ", "annotations": [], "id": "msg_05700a666b1fa3e9006a0204fafde081939f8e168ea039a9f9"}]
Key points:

Sources:
- None returned

## Explanation
Planner interpreted the request as workload=ai_inference, compute=10.00 MW, scope=England, budget=10000000000.0. It ran a nested UK-to-local search, asked the budget manager to allocate 1 centre(s), and selected Rugby as the leading option. Critics: ScopeCritic: pass; BudgetCritic: pass; DataQualityCritic: pass.

## Feedback Request
Please confirm whether the weighting of CO2, community strain, political support, cost, latency, resilience, and land use matches your decision priorities.

## Important Caveats
This is a hackathon prototype using public datasets and heuristic scoring. It is not an investment-grade site-selection tool. Some scores, especially water and climate, are placeholders until appropriate datasets are added.