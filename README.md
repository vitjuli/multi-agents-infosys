# AI Infrastructure Site Selection Baseline

Hackathon baseline for recommending UK data-centre locations under energy, water, climate, latency, resilience, and land/planning constraints.

The numeric ranking is deterministic and inspectable. OpenAI calls are used only for explanation, critique, and synthesis. If `OPENAI_API_KEY` is missing or a model call fails, the pipeline still runs with fallback agent messages.

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
  --query "Find the best UK location for a 100 MW AI training data centre" \
  --workload ai_training \
  --top-k 5
```

Other supported workloads:

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
```

## Candidate Regions

- Slough / West London
- Manchester
- Birmingham / West Midlands
- Teesside / North East England
- Edinburgh / Central Scotland
- Cardiff / South Wales
- Bristol / South West England
- Leeds / Yorkshire

## Important Limitations

Water and climate are placeholders. Water uses a simple regional stress heuristic. Climate uses latitude as a crude cooling proxy. Existing data-centre capacity, live grid headroom, connection queues, water abstraction licences, and commercial fibre latency are not yet modelled.

Prototype disclaimer: This is a hackathon prototype using public datasets and heuristic scoring. It is not an investment-grade site-selection tool. Some scores, especially water and climate, are placeholders until appropriate datasets are added.
