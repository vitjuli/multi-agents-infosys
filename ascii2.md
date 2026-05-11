                         ┌────────────────────────────────────┐
                         │ orchestrator.run_site_selection()  │
                         └─────────────────┬──────────────────┘
                                           │
                                           │ creates
                                           ▼
                         ┌────────────────────────────────────┐
                         │ AgentRunner                         │
                         │                                    │
                         │ enabled = not --no-agents           │
                         │ enable_web = --enable-web-policy    │
                         │ fast_model = OPENAI_MODEL_FAST      │
                         │ reasoning_model = OPENAI_MODEL_...  │
                         │ web_model = OPENAI_MODEL_WEB        │
                         └─────────────────┬──────────────────┘
                                           │
                 ┌─────────────────────────┼─────────────────────────┐
                 │                         │                         │
                 ▼                         ▼                         ▼
┌────────────────────────────┐ ┌────────────────────────────┐ ┌────────────────────────────┐
│ Optional PolicyResearchAgent│ │ Specialist Agents           │ │ Critic + Synthesis Agents  │
│ web-enabled                 │ │ explanation agents          │ │ reasoning agents           │
└──────────────┬─────────────┘ └──────────────┬─────────────┘ └──────────────┬─────────────┘
               │                              │                              │
               │ only runs if:                │ always called, but           │ always called, but
               │ --enable-web-policy          │ falls back if --no-agents    │ falls back if --no-agents
               │ and policy constraints exist │ or no API key                │ or no API key
               │                              │                              │
               ▼                              ▼                              ▼
┌────────────────────────────┐ ┌────────────────────────────┐ ┌────────────────────────────┐
│ runner.run_web_research()  │ │ run_specialist_agents()    │ │ run_critic()               │
│                            │ │                            │ │                            │
│ Agent:                     │ │ Agents:                    │ │ Agent:                     │
│ PolicyResearchAgent        │ │ EnergyAgent                │ │ CriticAgent                │
│                            │ │ WaterAgent                 │ │                            │
│ Model route:               │ │ ClimateCoolingAgent        │ │ Model route:               │
│ web_model                  │ │ LatencyAgent               │ │ reasoning_model            │
│                            │ │ ResilienceAgent            │ │                            │
│ Tool use:                  │ │ LandPlanningAgent          │ │ Input:                     │
│ OpenAI web search          │ │                            │ │ ranked table               │
│                            │ │ Model route:               │ │ specialist summaries       │
│ Input:                     │ │ fast_model                 │ │ instruction to identify    │
│ prompt                     │ │                            │ │ weaknesses/missing data    │
│ structured planner result  │ │ Input:                     │ │                            │
│                            │ │ top ranked rows            │ │ Output:                    │
│ Output stored at:          │ │ query                      │ │ critic JSON                │
│ SiteSelectionResult.       │ │ workload                   │ └──────────────┬─────────────┘
│ policy_research            │ │ focus payload              │                │
└────────────────────────────┘ │                            │                │ feeds into
                               │ Output:                    │                ▼
                               │ list[agent summary JSON]   │ ┌────────────────────────────┐
                               └──────────────┬─────────────┘ │ run_synthesis()             │
                                              │               │                            │
                                              │               │ Agent:                     │
                                              │               │ SynthesisAgent             │
                                              │               │                            │
                                              │               │ Model route:               │
                                              │               │ reasoning_model            │
                                              │               │                            │
                                              │               │ Input:                     │
                                              │               │ ranked table               │
                                              │               │ specialist summaries       │
                                              │               │ critic output              │
                                              │               │                            │
                                              │               │ Output:                    │
                                              │               │ final recommendation JSON  │
                                              │               └──────────────┬─────────────┘
                                              │                              │
                                              └──────────────┬───────────────┘
                                                             ▼
                                          ┌──────────────────────────────────┐
                                          │ report.build_markdown_report()   │
                                          │                                  │
                                          │ Uses:                            │
                                          │ specialist summaries             │
                                          │ CriticAgent output               │
                                          │ SynthesisAgent output            │
                                          │                                  │
                                          │ Writes:                          │
                                          │ reports/latest_report.md         │
                                          └──────────────────────────────────┘


USER / CLI
│
│  python -m data_centre_site_selector.main
│  --prompt ...
│  --budget ...
│  --compute-mw ...
│  --top-k ...
│  --json
│  --no-agents / agents enabled
│  --enable-web-policy
│  --debug-logs
│
▼
┌──────────────────────────────────────────────────────────────┐
│ data_centre_site_selector/main.py                            │
│ CLI ENTRYPOINT                                                │
├──────────────────────────────────────────────────────────────┤
│ 1. parse_args()                                               │
│ 2. configure_logging(debug/log_file)                          │
│ 3. parse_budget_gbp()                                         │
│ 4. call run_site_selection(...)                               │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ orchestrator.py :: run_site_selection                         │
│ TOP-LEVEL BACKEND COORDINATOR                                 │
└──────────────────────────────────────────────────────────────┘
│
├───────────────────────────────────────────────────────────────┐
│ FEATURE LOADING / BUILDING                                    │
│                                                               │
│ load_or_build_features()                                      │
│ │                                                             │
│ ├─ if cached dynamic table exists:                            │
│ │    data/processed/candidate_region_features.csv             │
│ │    └─ load it                                               │
│ │                                                             │
│ └─ else build_candidate_features()                            │
│      │                                                        │
│      ▼                                                        │
│   preprocess.py                                               │
│   ├─ generate candidates from ONS LAD boundaries              │
│   ├─ join LAD identity                                        │
│   ├─ join ONS population                                      │
│   ├─ compute DESNZ renewable radius features                  │
│   ├─ join NESO GSP regions / nearest GSP distance             │
│   ├─ optionally compute EA flood-zone intersections           │
│   └─ compute brownfield land/site radius features             │
└───────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ prompt_parser.py                                              │
│ USER INTENT STRUCTURING                                       │
├──────────────────────────────────────────────────────────────┤
│ parse_user_constraints()                                      │
│ ├─ workload                                                   │
│ ├─ compute_mw                                                 │
│ ├─ region scope                                               │
│ ├─ budget_gbp                                                 │
│ ├─ optimisation choices                                       │
│ ├─ policy constraints                                         │
│ └─ missing/unspecified fields                                 │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ planner.py :: run_planner                                     │
│ DETERMINISTIC PLANNING CORE                                   │
└──────────────────────────────────────────────────────────────┘
│
├───────────────────────────────────────────────────────────────┐
│ REGION INFERENCE                                              │
│                                                               │
│ infer_dynamic_region()                                        │
│ └─ if prompt mentions a known LAD name, narrow to that LAD     │
└───────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ data_analysis.py :: nested_search                             │
│ SEARCH + FEATURE SCORING                                      │
└──────────────────────────────────────────────────────────────┘
│
├─ Stage 1: UK-wide screening
│
├─ Stage 2: country screening
│          England / Scotland / Wales / Northern Ireland
│
└─ Stage 3: local-authority screening
           if a specific LAD/city is inferred or requested

Within each scoring pass:
│
▼
┌──────────────────────────────────────────────────────────────┐
│ scoring.py                                                    │
│ BASE SCORE GENERATION                                         │
├──────────────────────────────────────────────────────────────┤
│ add_raw_scores()                                              │
│ ├─ energy_score_raw                                           │
│ │   └─ renewables + operational/pipeline capacity + GSP bonus │
│ │                                                            │
│ ├─ water_score_raw                                            │
│ │   └─ placeholder population-pressure heuristic              │
│ │                                                            │
│ ├─ climate_score_raw                                          │
│ │   └─ latitude cooling proxy                                 │
│ │                                                            │
│ ├─ nearest_major_hub_distance_km                              │
│ │   ├─ select top population LADs as data-derived hubs        │
│ │   ├─ compute haversine distance to each hub                 │
│ │   └─ take minimum distance                                  │
│ │                                                            │
│ ├─ latency_score_raw                                          │
│ │   └─ clamp(10 - nearest_major_hub_distance_km / 45)         │
│ │                                                            │
│ ├─ resilience_score_raw                                       │
│ │   └─ flood-zone penalties / missing flood penalty           │
│ │                                                            │
│ ├─ land_score_raw                                             │
│ │   └─ brownfield hectares + brownfield site count            │
│ │                                                            │
│ └─ planning_risk_score_raw                                    │
│     └─ flood/data-quality risk proxy                          │
│                                                               │
│ score_for_workload()                                          │
│ └─ combines raw scores using WORKLOAD_WEIGHTS                 │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ data_analysis.py                                              │
│ PRODUCTION SCORE AUGMENTATION                                 │
├──────────────────────────────────────────────────────────────┤
│ add_production_scores()                                       │
│ ├─ co2_score_raw                                              │
│ ├─ population_strain_score_raw                                │
│ ├─ political_favour_score_raw                                 │
│ ├─ infrastructure_score_raw                                   │
│ ├─ land_use_score_raw                                         │
│ ├─ estimated_capex_per_mw_gbp                                 │
│ ├─ cost_score_raw                                             │
│ └─ production_score                                           │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ budget.py :: allocate_budget                                  │
│ BUDGET MANAGER                                                │
├──────────────────────────────────────────────────────────────┤
│ Inputs: scoped ranked candidates + constraints                │
│                                                               │
│ ├─ requested_compute_mw                                       │
│ ├─ available_budget_gbp                                       │
│ ├─ estimated capex per MW                                     │
│ ├─ recommended centre count                                   │
│ ├─ per-centre compute allocation                              │
│ ├─ total estimated capex                                      │
│ ├─ annual opex estimate                                       │
│ ├─ material estimates                                         │
│ └─ budget_feasible boolean                                    │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ planner.py :: build_recommendations                           │
│ STRUCTURED CENTRE OUTPUTS                                     │
├──────────────────────────────────────────────────────────────┤
│ For each selected centre:                                     │
│ ├─ location                                                   │
│ ├─ latitude / longitude / altitude                            │
│ ├─ priority_flag                                              │
│ ├─ feasibility boolean                                        │
│ ├─ problem_summary if infeasible                              │
│ ├─ capex / opex                                               │
│ ├─ compute_mw allocation                                      │
│ ├─ score_breakdown                                            │
│ ├─ policy_points                                              │
│ ├─ grants_tax_breaks                                          │
│ └─ explanation                                                │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ critics.py                                                    │
│ DETERMINISTIC CRITIC CHECKS                                   │
├──────────────────────────────────────────────────────────────┤
│ ScopeCritic                                                   │
│ └─ checks UK-only scope / invalid region hints                │
│                                                               │
│ BudgetCritic                                                  │
│ └─ checks whether estimated capex fits budget                 │
│                                                               │
│ DataQualityCritic                                             │
│ └─ flags missing compute/budget and weak datasets             │
│                                                               │
│ These critics affect:                                         │
│ ├─ feasibility                                                │
│ ├─ needs_human_input                                          │
│ └─ human_input_prompt                                         │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ explainer.py                                                  │
│ FINAL STRUCTURED EXPLANATION                                  │
├──────────────────────────────────────────────────────────────┤
│ ├─ overall explanation                                        │
│ ├─ centre-level explanation                                   │
│ ├─ feedback prompt                                            │
│ └─ public summary helpers                                     │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ SiteSelectionResult                                           │
│ MAIN STRUCTURED BACKEND OBJECT                                │
├──────────────────────────────────────────────────────────────┤
│ ├─ constraints                                                │
│ ├─ feasibility                                                │
│ ├─ needs_human_input                                          │
│ ├─ human_input_prompt                                         │
│ ├─ nested_search                                              │
│ ├─ recommendations                                            │
│ ├─ budget_plan                                                │
│ ├─ critic_results                                             │
│ ├─ explanation                                                │
│ ├─ feedback_prompt                                            │
│ └─ optional policy_research                                   │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ BACK TO orchestrator.py                                       │
│ ARTIFACTS + OPTIONAL AGENTS                                   │
└──────────────────────────────────────────────────────────────┘
│
├───────────────────────────────────────────────────────────────┐
│ FULL RANKING OUTPUT                                           │
│                                                               │
│ add_production_scores(features, constraints)                  │
│ └─ writes data/processed/latest_rankings.csv                  │
└───────────────────────────────────────────────────────────────┘
│
├───────────────────────────────────────────────────────────────┐
│ OPTIONAL WEB POLICY AGENT                                     │
│ only if --enable-web-policy and policy constraints exist      │
│                                                               │
│ agents.py :: AgentRunner.run_web_research()                   │
│ └─ PolicyResearchAgent                                        │
│    ├─ may use OpenAI web search                               │
│    ├─ searches current policy/grants/tax/planning context     │
│    └─ writes result into SiteSelectionResult.policy_research  │
└───────────────────────────────────────────────────────────────┘
│
├───────────────────────────────────────────────────────────────┐
│ SPECIALIST AGENTS                                             │
│ skipped as model calls if --no-agents                         │
│                                                               │
│ run_specialist_agents()                                       │
│ ├─ EnergyAgent                                                │
│ ├─ WaterAgent                                                 │
│ ├─ ClimateCoolingAgent                                        │
│ ├─ LatencyAgent                                               │
│ ├─ ResilienceAgent                                            │
│ └─ LandPlanningAgent                                          │
│                                                               │
│ Each receives:                                                │
│ ├─ prompt/query                                               │
│ ├─ workload                                                   │
│ └─ top ranked rows                                            │
│                                                               │
│ Each returns JSON-ish:                                        │
│ ├─ agent                                                      │
│ ├─ summary                                                    │
│ ├─ key_points                                                 │
│ ├─ risks                                                      │
│ └─ confidence                                                 │
└───────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ LLM CriticAgent                                               │
│ MODEL-BASED REVIEW                                            │
├──────────────────────────────────────────────────────────────┤
│ Inputs:                                                       │
│ ├─ ranked table                                               │
│ ├─ specialist agent summaries                                 │
│ └─ instruction to find weaknesses / missing datasets          │
│                                                               │
│ Output:                                                       │
│ ├─ summary                                                    │
│ ├─ key_points                                                 │
│ ├─ risks                                                      │
│ └─ confidence                                                 │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ SynthesisAgent                                                │
│ MODEL-BASED FINAL NARRATIVE                                   │
├──────────────────────────────────────────────────────────────┤
│ Inputs:                                                       │
│ ├─ ranked table                                               │
│ ├─ specialist agent summaries                                 │
│ ├─ CriticAgent output                                         │
│ └─ instruction to produce grounded final recommendation       │
│                                                               │
│ Output: final narrative summary                               │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ report.py                                                     │
│ REPORT GENERATION                                             │
├──────────────────────────────────────────────────────────────┤
│ build_markdown_report()                                       │
│ └─ reports/latest_report.md                                   │
│    legacy/specialist-agent style report                       │
│                                                               │
│ production_markdown_report()                                  │
│ └─ reports/latest_summary.md                                  │
│    structured production recommendation report                │
│                                                               │
│ production_terminal_report()                                  │
│ └─ terminal summary if --json is not used                     │
└──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────┐
│ OUTPUTS                                                       │
├──────────────────────────────────────────────────────────────┤
│ stdout                                                        │
│ └─ JSON if --json                                             │
│                                                               │
│ stderr                                                        │
│ ├─ logs                                                       │
│ └─ saved-file messages in JSON mode                           │
│                                                               │
│ files                                                         │
│ ├─ data/processed/latest_rankings.csv                         │
│ ├─ reports/latest_report.md                                   │
│ ├─ reports/latest_summary.md                                  │
│ └─ optional reports/debug.log                                 │
└──────────────────────────────────────────────────────────────┘
