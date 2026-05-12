# Production Data-Centre Site Selection Report

## Input Interpretation
Prompt: Find the best UK location for a data centre

Workload: `ai_training`

Compute: 50.0 MW

Region: uk-wide

Budget: unspecified

## Suggested Constraints
- Target compute capacity in MW or an expected rack/GPU footprint.
- Region scope: UK-wide, England, Scotland, Wales, Northern Ireland, or a specific UK city/cluster.
- Budget in GBP, ideally separating build capex and annual operating spend.
- Optimisation priorities: CO2, water strain, energy strain, latency, resilience, land reuse, policy support, cost.
- Hard constraints: flood exclusion, brownfield-only, renewable PPA preference, maximum distance to a major hub.

## Nested Search
- UK-wide screening: 361 candidates. Top regions: Hertsmere, Dacorum, Welwyn Hatfield, St Albans, Newcastle-under-Lyme.

## Budget And Materials
Recommended centres: 1

Estimated total capex: GBP 407.6m

Estimated annual opex: GBP 57.5m

- estimated_total_capex_gbp: 407591312.29
- estimated_steel_tonnes: 4750.0
- estimated_concrete_tonnes: 21000.0
- estimated_copper_tonnes: 600.0
- estimated_cooling_plant_mw_thermal: 62.5

Assumptions:
- Costs are class-5 planning estimates, not supplier quotes.
- Capex includes shell, MEP, grid interconnect, fit-out, security, design, and 18% contingency.
- Material quantities are first-order planning proxies for embodied-carbon and procurement discussion.

## Centre Recommendations
### Hertsmere
- Coordinates: 51.68017, -0.26899; altitude 0.0 m
- Priority: priority; feasible: True
- Compute allocation: 50.0 MW
- Estimated capex: GBP 407.6m; annual opex: GBP 57.5m
- Summary: Hertsmere scores 7.85/10 on the production objective, with strongest support from CO2=7.19, population strain=7.74, policy=7.20, infrastructure=8.18.
- Problem: None
- Policy points:
  - AI Growth Zones: UK programme for AI-enabled data centres that can improve access to power and planning support; applications are open-ended and eligibility is site-specific.
  - AI Growth Zone delivery reforms: Policy package includes grid-connection acceleration, planning support, and targeted operating-cost support for qualifying AI Growth Zones.
  - Investment Zone tax sites: Designated Investment Zone tax sites can offer business tax reliefs; candidate-specific eligibility needs GIS validation against official tax-site maps.
  - Freeport and Investment Zone employer NIC relief: Employer Class 1 National Insurance relief may apply in designated Freeport or Investment Zone special tax sites.
  - Freeport SDLT relief: Stamp Duty Land Tax relief may apply for qualifying land purchases in English Freeport tax sites until 30 September 2026.
- Explanation: The planner ranked Hertsmere by combining deterministic workload scoring with production criteria for carbon, population water/energy strain, political favour, infrastructure, land reuse, resilience, latency, and cost. The weighted profile favours candidates with high renewable capacity, lower community strain, practical grid/GSP access, brownfield availability, and plausible UK policy support. AI Growth Zones: UK programme for AI-enabled data centres that can improve access to power and planning support; applications are open-ended and eligibility is site-specific. AI Growth Zone delivery reforms: Policy package includes grid-connection acceleration, planning support, and targeted operating-cost support for qualifying AI Growth Zones.

## Critic Review
- ScopeCritic: passed; Region scope is UK-constrained and internally consistent.
- BudgetCritic: passed; Budget was unspecified; feasibility is based on cost estimates without a funding cap.
- DataQualityCritic: passed; Compute capacity was unspecified; defaulted to a 50 MW planning scenario.; Water, climate, grid headroom, fibre latency, grants, and tax-site eligibility require stronger site-level datasets before investment decisions.

## Web Policy Research
Not requested.

## Explanation
Planner interpreted the request as workload=ai_training, compute=50.00 MW, scope=uk-wide, budget=unspecified. It ran a nested UK-to-local search, asked the budget manager to allocate 1 centre(s), and selected Hertsmere as the leading option. Critics: ScopeCritic: pass; BudgetCritic: pass; DataQualityCritic: pass.

## Feedback Request
Please confirm or update these missing fields before final investment analysis: compute_mw, budget_gbp.

## Important Caveats
This is a hackathon prototype using public datasets and heuristic scoring. It is not an investment-grade site-selection tool. Some scores, especially water and climate, are placeholders until appropriate datasets are added.