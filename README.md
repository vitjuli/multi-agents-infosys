# AI Infrastructure Site Selection Backend

Backend for recommending UK data-centre locations under compute, region, budget, policy, energy, water, climate, latency, resilience, land-use, and cost constraints.

The numeric ranking is deterministic and inspectable. OpenAI calls are used only for specialist explanation, critique, and synthesis. If `OPENAI_API_KEY` is missing or a model call fails, the pipeline still runs with fallback agent messages.

## Setup

```bash
conda env create -f environment.yml
conda activate InfoHack
```

If the `InfoHack` environment already exists, update it instead:

```bash
conda env update -f environment.yml --prune
conda activate InfoHack
```

OpenAI calls read `OPENAI_API_KEY` from a repo-local `.env` file by default:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
OPENAI_MODEL_FAST=gpt-4o-mini
OPENAI_MODEL_REASONING=gpt-4o
OPENAI_MODEL_WEB=gpt-4o
```

The current prototype expects raw files under `data/raw/` and writes cached outputs to `data/processed/`.

## Inspect Data

```bash
python scripts/inspect_datasets.py
```

The inspector prints file existence, size, detected format, Excel sheet names, columns, sample rows, and geospatial CRS/geometry metadata when geospatial dependencies are installed.

## Build Features

```bash
python scripts/build_features.py
```

Flood-zone processing is skipped by default because the EA ZIP is large. To attempt it and cache the result:

```bash
python scripts/build_features.py --include-flood
```

This creates:

```text
data/processed/candidate_region_features.csv
```

## Run Site Selection

```bash
python -m data_centre_site_selector.main \
  --prompt "Find UK locations for a 100 MW AI training platform, optimise for CO2, water strain, political support and cost" \
  --budget "£1.2bn" \
  --region England \
  --top-k 5
```

Structured JSON output:

```bash
python -m data_centre_site_selector.main \
  --prompt "Find UK-wide options for a 60 MW inference platform with low carbon and policy support" \
  --budget "900m GBP" \
  --json \
  --no-agents
```

Debug logging:

```bash
python -m data_centre_site_selector.main \
  --prompt "Find the best 5 data centre locations around London for 100 MW compute with a £400m budget" \
  --compute-mw 100 \
  --budget "£400m" \
  --top-k 5 \
  --json \
  --no-agents \
  --debug-logs \
  --log-file reports/debug.log
```

Logs are written to stderr so JSON stdout remains parseable. `--debug-logs` includes parsed constraints, feature-cache decisions, data-derived hubs, score ranges, scoped candidate counts, budget allocation, critic outcomes, and selected recommendations.

The prompt parser recognises four main input features:

- target compute capacity, usually in MW
- UK region scope: UK-wide, England, Scotland, Wales, Northern Ireland, or a supported city/cluster
- explicit target location, for example `--target-location Manchester`
- optional radius targeting, for example `--target-location London --target-radius-miles 50`
- budget in GBP
- optimisation choices such as CO2, water/energy strain on population, political support, land use, resilience, latency, and cost

You can override parsed fields explicitly:

```bash
python -m data_centre_site_selector.main \
  --prompt "Plan a resilient backup estate in Scotland" \
  --compute-mw 40 \
  --budget "500m GBP" \
  --optimise resilience \
  --optimise co2

python -m data_centre_site_selector.main \
  --prompt "Find options within 50 miles of London" \
  --target-location London \
  --target-radius-miles 50 \
  --compute-mw 80 \
  --budget "1.5bn GBP"
```

Supported workloads:

```bash
python -m data_centre_site_selector.main --workload financial_low_latency
python -m data_centre_site_selector.main --workload backup_disaster_recovery
python -m data_centre_site_selector.main --workload ai_inference
python -m data_centre_site_selector.main --workload enterprise_colocation
```

Outputs:

```text
data/processed/latest_rankings.csv
reports/latest_report.md
reports/latest_summary.md
```

The structured backend result includes candidate centre locations, latitude, longitude, altitude, summaries, priority flags, cost and materials estimates, feasibility booleans, feasibility problem text when blocked, policy/grant/tax-break notes, nested search stages, critic results, and a final explanation/feedback prompt.

Candidate regions are generated dynamically from ONS local authority boundary centroids during feature builds. The backend now requires the boundary file and geospatial dependencies.

Policy-heavy requests can opt into web search through the OpenAI web-search tool:

```bash
python -m data_centre_site_selector.main \
  --prompt "Find 80 MW AI training options in the North East with policy support and low CO2" \
  --budget "900m GBP" \
  --enable-web-policy
```

Use this only when current policy data matters; deterministic runs remain preferable for reproducible testing.

## Frontend

Run the Streamlit frontend against the same backend pipeline:

```bash
conda activate InfoHack
streamlit run streamlit_app.py
```

The frontend can run blueprint startup non-interactively, display inferred preferences and blueprint structure, and then execute the standard planner/orchestrator flow.

## Backend Flow

1. Prompt parser extracts compute, region, budget, workload, optimisation choices, missing fields, and suggested constraints.
2. Optional blueprint startup runs as a LangGraph flow that infers preferences, loads RL policy weights, and generates a blueprint used to seed the main run.
3. Planner coordinates the run and restricts all recommendations to UK candidate regions.
4. Data analysis module performs nested UK-to-country-to-local-authority screening and scores CO2 proxy, population strain, policy favour, infrastructure, land use, cost, and resilience.
5. Budget manager estimates the number of centres, compute allocation, capex, opex, and materials.
6. Optional web policy research refreshes policy/grant/tax context for policy-constrained requests.
7. Critics check scope, budget feasibility, and data quality.
8. Explainer produces the structured recommendation, technical explanation, and feedback prompt.

## Important Limitations

Water and climate are placeholders. Water uses a simple regional stress heuristic. Climate uses latitude as a crude cooling proxy. Existing data-centre capacity, live grid headroom, connection queues, water abstraction licences, and commercial fibre latency are not yet modelled.

Policy incentives, grants, tax breaks, and AI Growth Zone eligibility are treated as planning signals only. Site-level legal/tax eligibility requires validation against the latest official maps, programme criteria, and professional advice.
