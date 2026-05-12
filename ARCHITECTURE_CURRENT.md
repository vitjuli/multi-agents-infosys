# Current Architecture (what the code actually does)

This document captures what `multi-agents-infosys` does today. The proposed RL
layer in `RL\_OPTIMISATION\_ARCHITECTURE.md` is not in this codebase; per Cam, the
RL on planner outputs is being handled separately.

## TL;DR

The backend is a deterministic ranking pipeline with LLM agents bolted on for
post-hoc explanation, critique, and synthesis. A prompt and constraints flow
through feature loading, scoring, budgeting, and critics, all numeric and
reproducible. OpenAI models then label that ranking with key points, risks, and
a synthesis paragraph. Two Markdown reports and one CSV come out of the run.

The biggest functional bug found in this review: `policy.opportunities\_for\_region`
ignores its `region` and `country` arguments and returns the same five UK-wide
opportunities for every candidate, so the `political\_favour` axis does not
differentiate regions at all. See the Issues section.

## Entry point

`python -m data\_centre\_site\_selector.main` parses CLI arguments and calls
`orchestrator.run\_site\_selection(...)`. That is the only live entry point.

Legacy / orphan code still in the tree:

* top-level `main.py` (toy researcher/critic/writer demo over a single topic)
* `test\_openai.py` (one-shot API call)
* `src/openai\_client.py` (used by the top-level `main.py` only)
* `Lab1.ipynb`, `Lab2.ipynb` (lecturer agentic-systems examples)

`src/openai\_client.py` and `test\_openai.py` both reference `model="gpt-5.2"`,
which is not a real OpenAI model and will fail at runtime. The active
pipeline does not use these files. They should be deleted or moved under a
`legacy/` directory before submission.

## Flow

```text
CLI (data\_centre\_site\_selector/main.py)
  │
  ▼
orchestrator.run\_site\_selection
  │
  ├── load\_or\_build\_features            preprocess.build\_candidate\_features (or cache)
  │     ├── candidate\_frame             dynamic LAD-centroid candidates
  │     ├── add\_lad\_features            LAD code/name spatial join
  │     ├── add\_population\_features     ONS mid-2024 LAD populations
  │     ├── add\_renewable\_features      DESNZ REPD radius capacity (25/50 km)
  │     ├── add\_gsp\_features            NESO GSP region + nearest-GSP distance
  │     ├── add\_flood\_features          EA flood zones (opt-in, large file)
  │     └── add\_brownfield\_features     Brownfield site/land radius features
  │
  ├── prompt\_parser.parse\_user\_constraints
  │     workload, region (level + text), compute\_mw, budget,
  │     optimisation choices, missing fields, invalid (non-UK) regions
  │
  ├── planner.run\_planner
  │     ├── infer\_dynamic\_region        refines region scope from prompt
  │     ├── data\_analysis.nested\_search
  │     │     ├── add\_production\_scores (calls scoring.score\_for\_workload)
  │     │     │     score\_for\_workload  raw scores + workload-weighted overall\_score
  │     │     │     add\_production\_scores  production-tier scores + production\_score
  │     │     └── UK -> country -> city stage filtering
  │     ├── budget.allocate\_budget      centre count, capex, opex, materials
  │     ├── build\_recommendations       per-centre dataclasses with
  │     │     policy.policy\_points, policy.grant\_tax\_breaks,
  │     │     explainer.priority\_flag / centre\_summary / centre\_explanation
  │     ├── critics.run\_deterministic\_critics  Scope, Budget, DataQuality
  │     └── explainer.build\_overall\_explanation + feedback\_prompt
  │
  ├── agents.AgentRunner.run\_web\_research  (optional, --enable-web-policy)
  │     PolicyResearchAgent over OpenAI web\_search\_preview
  │
  ├── agents.run\_specialist\_agents      six LLM agents, one OpenAI call each
  │     EnergyAgent, WaterAgent, ClimateCoolingAgent,
  │     LatencyAgent, ResilienceAgent, LandPlanningAgent
  │
  ├── agents.run\_critic                 LLM CriticAgent (reasoning model)
  ├── agents.run\_synthesis              LLM SynthesisAgent (reasoning model)
  │
  └── report.build\_markdown\_report      technical .md with LLM blocks
      report.production\_markdown\_report production summary, no LLM content
      report.production\_terminal\_report stdout output
```

## File-to-stage map

|Stage|File|
|-|-|
|CLI / args|`data\_centre\_site\_selector/main.py`|
|Orchestration|`data\_centre\_site\_selector/orchestrator.py`|
|Prompt parsing|`data\_centre\_site\_selector/prompt\_parser.py`|
|Feature build (data ingestion)|`data\_centre\_site\_selector/preprocess.py`|
|Geo helpers (distances, CRS, WKT)|`data\_centre\_site\_selector/geo\_utils.py`|
|Data paths|`data\_centre\_site\_selector/data\_paths.py`|
|Raw scoring (per workload)|`data\_centre\_site\_selector/scoring.py`|
|Production scoring + region scope|`data\_centre\_site\_selector/data\_analysis.py`|
|Workload weights, model config|`data\_centre\_site\_selector/config.py`|
|UK gov. policy lookups|`data\_centre\_site\_selector/policy.py`|
|Budget allocation, materials|`data\_centre\_site\_selector/budget.py`|
|Deterministic critics|`data\_centre\_site\_selector/critics.py`|
|Per-centre explanations|`data\_centre\_site\_selector/explainer.py`|
|LLM agent runner \& specialists|`data\_centre\_site\_selector/agents.py`|
|Planner / recommendation assembly|`data\_centre\_site\_selector/planner.py`|
|Markdown / terminal reports|`data\_centre\_site\_selector/report.py`|
|Dataclasses|`data\_centre\_site\_selector/schemas.py`|
|Logging|`data\_centre\_site\_selector/logging\_utils.py`|

Helper scripts (not on the hot path):

* `scripts/build\_features.py` rebuilds the feature cache
* `scripts/inspect\_datasets.py` inspects raw inputs
* `scripts/check\_openai\_setup.py` smoke-tests the API key
* `scripts/load\_geo.py` previews LAD boundaries (calls `plt.show()`; do not run headless)

Inputs (`data/raw/`) and outputs (`data/processed/`, `reports/`) are pinned in
`data\_paths.py`.

## Outputs

|Artefact|Path|Contents|
|-|-|-|
|Ranked candidates|`data/processed/latest\_rankings.csv`|every LAD with all raw and production scores|
|Technical report|`reports/latest\_report.md`|dataset notes, ranked table, per-agent LLM blocks, critic, synthesis, uncertainties|
|Production summary|`reports/latest\_summary.md`|structured `SiteSelectionResult` only; no LLM specialist or synthesis output|
|Terminal / JSON|stdout|`production\_terminal\_report` or `--json`|

The production summary is the more polished user-facing artefact but contains no
LLM content. The technical report is the only place the specialist agents and
synthesis show up. If the team intends the summary to be the deliverable,
decide whether to merge the LLM-derived prose into it.

## Cam's comments, answered

### `main.py` (CLI)

The argparse block is the entire user-facing surface of the backend. Every flag
has a default; only `--prompt` / `--query` is effectively required. There is no
other entry point. The CLI exists so a frontend or other client can call the
backend as a subprocess and parse `--json` from stdout. Nothing here is "just a
helper".

### `orchestrator.py`

All in-flight tables are pandas DataFrames (candidate features, ranked
candidates). Structured outputs (`SiteSelectionResult` and friends) are
dataclasses converted to dicts on the way out. `run\_site\_selection` takes 13
keyword arguments mirroring the CLI flags; only `query` is positional in
practice. The flow is: load/build features, parse constraints, run planner,
optional web-policy research, specialist agents, critic agent, synthesis agent,
write reports.

### `config.py`

The comment is stale. There are no hardcoded candidate regions or `HUBS`
constants in the current file; both were removed when candidate generation
moved to ONS LAD centroids in `preprocess.candidate\_frame`. What lives in
`config.py` now is OpenAI model names and `WORKLOAD\_WEIGHTS`.

`WORKLOAD\_WEIGHTS` defines, per workload, the relative importance of each raw-
score dimension. Higher weight on `latency` for `financial\_low\_latency`, higher
weight on `resilience` for `backup\_disaster\_recovery`, and so on. Weights are
hand-picked and undocumented. They sum to roughly 1.0 per workload (used as a
denominator in `scoring.score\_for\_workload`).

### `schemas.py`

Six dataclasses cover the current flow: `UserConstraints`, `SearchStage`,
`BudgetPlan`, `CentreRecommendation`, `CriticResult`, `SiteSelectionResult`.
Adequate for the existing pipeline. Per-agent LLM outputs and policy-research
results are still `dict\[str, Any]`. If the RL extension adds a `Claim` or
`Evidence` type those would be new dataclasses.

### `prompt\_parser.py`

`WORKLOAD\_KEYWORDS` and `OPTIMISATION\_KEYWORDS` are hand-curated word matches.
Five workloads with around five phrases each, seven optimisation buckets with
around five phrases each. Easy to extend, easy to miss edge cases.

`NON\_UK\_HINTS` is a blacklist of common non-UK terms used only to set
`invalid\_region` for the critic and to override the inferred region back to
UK-wide. The default region is already `("uk", "UK-wide")` when no UK alias
matches, so the blacklist's only real function is the warning. A whitelist
(UK names only) plus a `did\_user\_name\_any\_known\_region` flag would replace it
more cleanly.

`SUGGESTED\_CONSTRAINTS` is a five-item static reminder echoed back when fields
are missing.

### `preprocess.py`

Data sources are hardcoded in `data\_download.sh`, which must be run manually
before the first feature build. The module is large (around 660 lines, eight
stages) and each stage joins one external dataset.

Lazy imports of `geopandas`, `shapely`, and `pyproj` exist so the module
imports cleanly without geospatial dependencies. Hiding them inside try/except
is workable; a single `if not has\_geopandas(): diagnostics.append(...); return df`
at the top of each affected stage would be cleaner.

Column detection uses `detect\_column` (substring and normalised-name match) so
the pipeline survives small column renames but not large schema changes.

Specific feature notes:

* Population: joins one number per LAD (mid-2024 "All ages"), used as a proxy
for water/cooling demand and to pick "data hubs" (see scoring notes).
* Renewables: aggregates DESNZ REPD generator capacity within 25 km and 50 km
of each candidate centroid, split by operational and pipeline status. The
25/50 km radii are magic numbers; if the team wants them tunable, move them
to `config.py` with a comment explaining the choice.
* Brownfield: parses WKT `POINT(x y)` and counts sites and hectares within
25/50 km. England-only caveat applies (Scotland/Wales have separate registers).
* GSP: spatial join plus nearest-centroid distance to NESO grid supply points.
* Flood: opt-in via `--include-flood`; otherwise leaves placeholder columns and
a "not computed" warning.

### `scoring.py`

Raw scores per candidate are in `\[0, 10]` via `\_linear` and `clamp`:
`energy\_score\_raw`, `water\_score\_raw` (placeholder population proxy),
`climate\_score\_raw` (placeholder latitude proxy), `latency\_score\_raw`,
`resilience\_score\_raw`, `land\_score\_raw`, `planning\_risk\_score\_raw`.

`data\_derived\_hubs(df, top\_n=3)` picks the **top three LADs by population** and
then computes `nearest\_major\_hub\_distance\_km` to those. The function is named
"data hubs" but it is really "population hubs". For a `financial\_low\_latency`
workload that should care about fibre interchanges, this is the wrong signal.

`score\_for\_workload` does a weighted sum of raw scores using
`WORKLOAD\_WEIGHTS\[workload]`, subtracts a planning-risk penalty, divides by the
sum of positive weights, and clamps.

### `data\_analysis.py`

Adds production-tier scores on top of raw scores: `co2\_score\_raw`,
`population\_strain\_score\_raw`, `political\_favour\_score\_raw`,
`infrastructure\_score\_raw`, `land\_use\_score\_raw`, `cost\_score\_raw`, plus an
`emissions\_intensity\_proxy\_kgco2e\_per\_mwh` that is currently computed but never
referenced downstream.

The final `production\_score` is a weighted sum of those production-tier scores
plus `0.18 \* overall\_score`. Weights are hand-picked. When a user asks for an
`optimisation\_choice` (e.g. `cost`), that weight is multiplied by 1.35 and the
others by 0.80 before normalising. The multipliers are not derived from
anywhere.

`\_linear` is duplicated between `scoring.py` and `data\_analysis.py` with
slightly different signatures (`invert` flag in one, not the other). One copy
in `geo\_utils.py` or a shared helper module would be tidier.

`nested\_search` filters the scored table to UK -> country -> city in stages and
returns a `SearchStage` list and the final scoped frame.

### `policy.py`

This file is about **UK government policy** (AI Growth Zones, Freeport SDLT
relief, Investment Zone tax sites, etc.), not the RL "policy" from the
architecture doc. The name collision is unfortunate; renaming to `gov\_policy.py`
or `incentives.py` before any RL component lands would prevent confusion.

The critical issue: `opportunities\_for\_region(region, country)` accepts both
arguments and uses neither; the function body is `return POLICY\_OPPORTUNITIES`.
That means `policy\_score` returns `clamp(5.0 + 1.2 + 1.0 + 0 + 0 + 0) = 7.2`
for every UK candidate, and `political\_favour\_score\_raw` is therefore identical
across all regions. The `political\_favour` axis contributes a constant offset
to every candidate's `production\_score`, which means it currently does not
differentiate candidates at all.

### `budget.py`

Hardcoded constants: `DEFAULT\_COMPUTE\_MW=50`, `MIN\_VIABLE\_CENTRE\_MW=10`,
`TARGET\_MAX\_CENTRE\_MW=80`, `OPEX\_PER\_MW\_GBP=1\_150\_000`, `CONTINGENCY\_RATE=0.18`.

`constraints.compute\_mw` is the total requested MW; `per\_centre\_compute = requested / centre\_count`. Capex per centre is `per\_centre\_compute \* estimated\_capex\_per\_mw\_gbp \* 1.18`. The 18% contingency is the planning-grade
buffer often used in class-5 estimates.

The materials summary uses one ratio per material per MW of compute (95 t
steel/MW, 420 t concrete/MW, 12 t copper/MW, 1.25 MW thermal cooling per MW IT).
First-order procurement proxies, not supplier quantities.

### `critics.py`

Three deterministic critics, all run unconditionally:

* `ScopeCritic`: flags non-UK region hints and Northern Ireland absence from
the cached candidate table.
* `BudgetCritic`: passes iff `BudgetPlan.budget\_feasible`.
* `DataQualityCritic`: passes iff at least one recommendation; always appends a
placeholder-data caveat.

These are quantitative pass/fail with explanatory text. The qualitative LLM
critique is a separate path in `agents.run\_critic` and only feeds into the
technical report's `## Critic Review` block and the synthesis prompt. The two
critic systems are not combined or cross-referenced anywhere.

### `agents.py`

`AgentRunner` wraps `OpenAI()` with per-agent model selection: fast model for
specialists, reasoning model for critic/synthesis/explainer, web model for the
optional policy researcher.

`parse\_agent\_json` slices from the first `{` to the last `}` and `json.loads`
the result. It survives some leading prose but breaks on markdown code fences,
multiple JSON blobs, or any content with stray braces. Switching to
`response\_format={"type": "json\_object"}` on the API call (or a Pydantic
schema) would be more reliable.

Specialist prompts are very generic. Each agent receives the same `top\_rows`
payload with one `focus` field; the system prompt is identical except for the
agent name. Room for prompt improvement is real.

### `geo\_utils.py`

Internal target CRS is WGS84 (lat/lon). Inputs vary: CSV with WKT POINT
(`parse\_point\_wkt`), Excel with OS National Grid eastings/northings
(`osgb\_to\_wgs84`), GeoJSON in 4326, zipped shapefile in 27700.

`haversine\_km` is the great-circle distance, used for every radius feature.
`osgb\_to\_wgs84` prefers `pyproj`; the coarse fallback (around plus or minus
5 km in the UK) is for environments without `pyproj` installed and is not safe
for site-level work.

### `data\_paths.py`

Every raw input and processed output is pinned to a fixed filename under
`data/raw/` and `data/processed/`. There is no environment-variable override.
This makes the pipeline reproducible but every dataset has to be downloaded at
exactly the expected name; `data\_download.sh` enforces that.

### `logging\_utils.py`

One central logger configured by `configure\_logging` with stderr plus an
optional file handler. All modules use `get\_logger("component")` so debug logs
are scoped per stage.

### `report.py`

Two Markdown renderers: `build\_markdown\_report` (the technical report that
interleaves LLM agent output) and `production\_markdown\_report` (the production
summary derived from `SiteSelectionResult` only, no LLM content). They are not
consolidated.

Uncertainties and "next data sources" sections are hardcoded lists. A single
source of truth in `config.py` referenced from both reports would prevent drift.

## Differences from `RL\_OPTIMISATION\_ARCHITECTURE.md`

|Architecture-doc stage|In code?|Notes|
|-|-|-|
|Planner module|partial|`planner.run\_planner` exists but orchestrates scoring/budget/critic rather than the priority decomposition shown in section 11 of the architecture doc.|
|Specialist agents (Budget, Land, Climate, etc.)|inverted|The agents in `agents.py` are **post-hoc explainers of the deterministic ranking**, not evidence generators. Evidence is produced by `preprocess.py`, `scoring.py`, `data\_analysis.py`, `policy.py`, `budget.py`.|
|Raw evidence store|implicit|The ranked DataFrame plus the JSON dicts agents emit. No structured `Evidence` object.|
|Candidate report generator (Report A + Report B)|no|One pipeline; two Markdown renderers happen to produce different views but are not A/B candidates.|
|Claim extraction layer|no|Not present.|
|Claim scoring layer|no, at region only|Present at region level (`production\_score`), not at claim level.|
|RL / preference policy layer|no|Not in this codebase (handled separately per Cam).|
|Evidence selection module|no|Not present.|
|Final report composer|partial|`production\_markdown\_report` composes deterministically from `SiteSelectionResult`.|
|Critic module|yes, dual|Deterministic critics in `critics.py` + LLM CriticAgent in `agents.py`. Not combined.|
|Human feedback|partial|`--interactive` lets the user reply once when fields are missing. Reruns the whole pipeline. Not fed into any persistent policy.|
|Policy update|no|Not present.|

The proposed file layout in section 10 of the architecture doc
(`src/modules/`, `src/reports/`, `src/rl/`) does not match the actual
`data\_centre\_site\_selector/` package. The proposed module APIs in section 11 do
not match the implemented signatures either. If the doc is kept as a forward
plan, update those sections to dock the proposed RL layer into the real package
layout so the team can see where new files would sit.

## Issues worth fixing, rough priority order

1. **`policy.opportunities\_for\_region` ignores its arguments.** Every UK
candidate gets the same political-favour score (around 7.2 after clamping).
The `political\_favour` axis currently does nothing. Either return
region-specific opportunities (lookup by LAD code or country) or drop the
weighting until real differentiation exists.
2. **`data\_derived\_hubs` selects on population but is named "data hubs".**
Rename, or compute distance to actual fibre / colocation hubs. Matters for
`financial\_low\_latency` and `ai\_inference` in particular.
3. **Production summary contains no LLM content.** Decide whether
`reports/latest\_summary.md` should stay deterministic-only (and the
technical report is the LLM one) or whether the team's deliverable should
merge them.
4. **Legacy entry points still ship.** `main.py` (top level), `test\_openai.py`,
and `src/openai\_client.py` reference a hallucinated `gpt-5.2` model.
Delete, move under `legacy/`, or correct the model name. The Lab1/Lab2
notebooks are lecturer examples and can be kept or moved.
5. **`infer\_dynamic\_region` cannot resolve cluster names** like "London" that
are not a single LAD. The matcher iterates LAD names from the feature table;
London is split into boroughs. Map common cluster names to a lat/lon and a
candidate-subset filter, or add a region classifier.
6. **`parse\_agent\_json` is fragile.** Switch to
`response\_format={"type": "json\_object"}` (or a Pydantic schema) and drop
the slice-by-brace fallback for the happy path.
7. **`\_linear` is duplicated** in `scoring.py` and `data\_analysis.py`. Move to
`geo\_utils.py` or a new `scoring\_utils.py`.
8. **Magic numbers spread across modules.** Radii (25/50/15 km), weight bumps
(1.35/0.80), priority thresholds (4.5/6.5/8.0), capex base (8.5M/MW),
materials ratios. Centralise in `config.py` with a one-line comment per
constant explaining what it represents and where it came from.
9. **`emissions\_intensity\_proxy\_kgco2e\_per\_mwh`** is computed and discarded.
Either surface it in the report or remove.
10. **`scripts/load\_geo.py` blocks on `plt.show()`.** Add a `--save` flag or
switch to a non-interactive backend.
11. **No tests.** Hard to refactor with confidence. At minimum a smoke test
that asserts `run\_site\_selection(query="...", use\_agents=False)` returns
one feasible recommendation against a frozen feature CSV would catch
regressions.

## Notes on the two critic systems

Deterministic critics in `critics.py` feed `feasibility`, which gates
recommendations. LLM `CriticAgent` in `agents.py` feeds the technical report's
`## Critic Review` block and the synthesis prompt. They never see each other.
Cam's question "Which hardcoded checks do we really want?" applies to
`critics.py`; the LLM critic is open-ended by design.

