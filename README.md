# Data Centers Infrastructure Site Selection for the Government 
### 

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Research Background and Motivation](#2-research-background-and-motivation)
   - 2.1 [The Data Heterogeneity Problem](#21-the-data-heterogeneity-problem)
   - 2.2 [Multi-Criteria Optimisation Under Stakeholder Variability](#22-multi-criteria-optimisation-under-stakeholder-variability)
   - 2.3 [The Alignment Problem in Agentic Research Systems](#23-the-alignment-problem-in-agentic-research-systems)
   - 2.4 [Absence of Ground Truth and the Validation Problem](#24-absence-of-ground-truth-and-the-validation-problem)
3. [Pipeline Roadmap](#3-pipeline-roadmap)
4. [Methodology](#4-methodology)
   - 4.1 [Preference Elicitation and Blueprint Construction](#41-preference-elicitation-and-blueprint-construction)
   - 4.2 [RL-Inspired Policy Optimisation for Blueprint Orchestration](#42-rl-inspired-policy-optimisation-for-blueprint-orchestration)
   - 4.3 [Selective Agent Dispatch via Blueprint Task Mapping](#43-selective-agent-dispatch-via-blueprint-task-mapping)
   - 4.4 [Deterministic Auditable Scoring](#44-deterministic-auditable-scoring)
   - 4.5 [Evaluation Architecture: Blueprint Critic and Coherence Evaluator](#45-evaluation-architecture-blueprint-critic-and-coherence-evaluator)
5. [Multi-Agent System Design](#5-multi-agent-system-design)
6. [Data Sources and Feature Engineering](#6-data-sources-and-feature-engineering)
7. [Evaluation Framework](#7-evaluation-framework)
8. [Relation to Existing Work](#8-relation-to-existing-work)
9. [Setup](#9-setup)
10. [Running the Pipeline](#10-running-the-pipeline)
11. [Project Structure](#11-project-structure)
12. [Known Limitations and Future Directions](#12-known-limitations-and-future-directions)

---

## 1. Introduction

The physical placement of AI compute infrastructure represents one of the most consequential and least formalised decision problems in contemporary technology policy. Where data centres are built determines the operational carbon footprint of AI training workloads, the latency characteristics of deployed models, the resilience of digital services under climate-related hazards, and the geographic distribution of economic benefit from AI investment. In the United Kingdom, this problem has achieved explicit policy urgency: the [National AI Infrastructure Review](https://www.gov.uk/government/publications/ai-infrastructure-review) (2023) identified compute infrastructure as a strategic national priority, and the 2024 Autumn Budget established AI Growth Zones as designated planning and grid-access acceleration areas.

Despite this urgency, the decision-making tools available to practitioners remain inadequate. General-purpose AI assistants can generate plausible narrative assessments, but they cannot ingest and integrate the heterogeneous public datasets required for a defensible quantitative recommendation, they cannot reproduce the same numerical output from the same data across independent runs, and they have no mechanism for learning which aspects of a report a particular stakeholder will find decision-relevant. The gap between what is required for credible infrastructure siting advice and what current AI-augmented tools provide is the motivating problem of this work.

This project presents a **Preference-Guided Multi-Agent Research Blueprint System**: a pipeline that combines deterministic geospatial scoring over authoritative public datasets with a preference interview module, an RL-inspired orchestration policy, a human-in-the-loop approval gate, and a systematic validation framework. The central research question is: *Can a multi-agent pipeline, governed by a preference-guided blueprint and an adaptive orchestration policy, produce infrastructure placement recommendations that are simultaneously reproducible, stakeholder-aware, explainable, and empirically validated?*

The system is structured around the following design commitments:

- **Reproducibility as a hard constraint.** The quantitative ranking of candidate sites must be identical given identical inputs. LLM agents are used exclusively for explanation and synthesis, never for score computation.
- **Stakeholder alignment before execution.** Report structure, section depth, and agent selection are determined through a preference interview and approved by the user before any costly computation begins.
- **Adaptive orchestration.** A persistent policy vector, updated via a reward signal after each run, governs how future blueprints are constructed — implementing a lightweight form of reinforcement learning from human feedback.
- **Independent validation.** A deterministic, LLM-free coherence evaluator verifies agent output quality across four orthogonal checks, providing evidence that the system does what it claims.

---

## 2. Research Background and Motivation

### 2.1 The Data Heterogeneity Problem

Credible data centre site selection requires the integration of at least eight authoritative public datasets, each produced by a different government agency at a different spatial resolution and in a different file format:

| Dataset | Agency | Format | Spatial Coverage |
|---------|--------|--------|-----------------|
| Local Authority District boundaries (Dec 2024) | ONS | GeoJSON | UK-wide |
| Renewable Energy Planning Database (REPD) | DESNZ | XLSX | UK-wide |
| Grid Supply Point regions | NESO | Shapefile ZIP | UK-wide |
| Flood Risk Zones 2 & 3 | Environment Agency | GeoJSON ZIP | England |
| Population estimates mid-2024 | ONS | XLSX | England/Wales |
| Brownfield land register | DLUHC | CSV | England |
| Brownfield site register | DLUHC | CSV | England |
| AI Growth Zone / Investment Zone designations | MHCLG | Policy documents | UK-wide |

Fusing these datasets into a common analytical frame requires geospatial join operations — radius-based capacity aggregation, polygon intersection for flood zone assessment, centroid projection from boundary geometries — executed across 370 or more Local Authority Districts. This is not a task a conversational AI assistant can perform within a dialogue context; it requires a persistent, reproducible computational pipeline with explicit data provenance.

### 2.2 Multi-Criteria Optimisation Under Stakeholder Variability

Site selection is an inherently multi-criteria problem. The technically optimal location for a 200 MW AI training cluster — where cooling efficiency, renewable energy capacity, and grid connection headroom are paramount — is categorically different from the optimal location for a 20 MW financial trading platform, where sub-millisecond latency to London financial exchanges dominates the objective function. No single weighting of criteria is universally correct; the appropriate weights are a function of the workload profile, the investment mandate, and the stakeholder's risk tolerance.

This observation has two implications for system design. First, the scoring pipeline must support multiple workload profiles with distinct weight vectors, and those weights must be explicit, inspectable, and modifiable. Second, and more subtly, a system that cannot infer or elicit the stakeholder's weighting preferences before generating a recommendation will produce outputs systematically misaligned with the decision-maker's actual needs. The preference interview module described in §4.1 directly addresses this second implication.

### 2.3 The Alignment Problem in Agentic Research Systems

Multi-agent research systems face a structural alignment problem that is distinct from the alignment problem studied in the AI safety literature, though related to it. When a pipeline dispatches specialist agents immediately upon receiving a user query, the agents optimise for completing their assigned analytical task — they do not optimise for producing the report that the specific user, with their specific audience, depth requirement, and priority structure, would approve. The result is a report that may be technically comprehensive but is practically misaligned: too technical for an investor, insufficiently detailed for a site engineer, missing the policy section that a regulator requires.

The standard response to this problem — prompt engineering — is fragile and non-persistent. It requires the user to reformulate their requirements with each query and provides no mechanism for the system to learn, across sessions, what report structures a particular class of stakeholder accepts. This project proposes a structural solution: a pre-execution preference interview followed by a human-approved report blueprint that governs all downstream agent behaviour, combined with a persistent policy that adapts blueprint construction based on accumulated feedback.

### 2.4 Absence of Ground Truth and the Validation Problem

Infrastructure siting problems lack the labelled ground truth that makes evaluation straightforward in supervised learning settings. There is no canonical dataset of "correct" UK data centre locations against which a recommendation system can be benchmarked in the conventional sense. This creates a validation challenge that must be addressed through the construction of proxy evaluation criteria:

- **Internal consistency:** Does the scoring pipeline produce identical outputs from identical inputs? (Determinism verification)
- **Ordering validity:** Do workload-specific weight vectors produce rank orderings consistent with domain knowledge? (Ordering verification)
- **Proximity to documented deployments:** Do the system's top-ranked candidates overlap with publicly documented commercial data centre locations? (Ground truth approximation)
- **Agent output coherence:** Do specialist agents use domain-appropriate vocabulary, express calibrated confidence, and avoid sentiment contradictions with the quantitative scores they were given? (Anti-hallucination verification)

The evaluation framework described in §7 operationalises all four criteria independently of any LLM, providing a reproducible evidence base for system quality.

---

## 3. Pipeline Roadmap

The system executes in three sequential layers, each independently testable and each degrading gracefully when external API services are unavailable.

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1 — Preference Elicitation and Blueprint Construction    │
│                                                                 │
│  User Query                                                     │
│    → Preference Interview Module    (heuristic + LLM refine)   │
│    → UserPreferences object         (typed, inspectable)        │
│    → Blueprint Optimiser            (policy-weighted + LLM)    │
│    → ReportBlueprint object         (sections, agents, depth)  │
│    → Human Approval Gate            (natural language loop)    │
└────────────────────────────┬────────────────────────────────────┘
                             │ approved ReportBlueprint
┌────────────────────────────▼────────────────────────────────────┐
│  LAYER 2 — Deterministic Scoring and Selective Agent Execution  │
│                                                                 │
│  Feature Table (ONS + DESNZ + NESO + EA + DLUHC)               │
│    → Raw Score Computation          (closed-form, deterministic)│
│    → Workload-Weighted Ranking      (5 workload profiles)       │
│    → Planner + Budget Allocator     (CAPEX/OPEX estimation)    │
│    → Blueprint Task Dispatcher      (selective agent call)     │
│    → Specialist Agents × N          (blueprint-contextualised) │
│    → Critic Agent                   (identifies weaknesses)    │
│    → Synthesis Agent                (final narrative)          │
└────────────────────────────┬────────────────────────────────────┘
                             │ agent outputs + SiteSelectionResult
┌────────────────────────────▼────────────────────────────────────┐
│  LAYER 3 — Report Composition, Evaluation, and Policy Update   │
│                                                                 │
│  Blueprint Report Composer  → section-ordered Markdown report  │
│  Blueprint Critic (LLM)     → BlueprintCriticResult (0–10)    │
│  User Acceptance Gate       → acceptance or change request     │
│  Policy Update Module       → weight nudge + normalisation     │
│  Memory Module              → run_memory.json (persisted)      │
└─────────────────────────────────────────────────────────────────┘
```

**Graceful degradation.** If `OPENAI_API_KEY` is absent or a model call fails, Layer 1 falls back to keyword-heuristic preference inference and rule-based blueprint construction. Layer 2 falls back to deterministic agent summaries. Layer 3 falls back to substring-matching critic evaluation. The quantitative ranking in Layer 2 is unaffected in all cases.

---

## 4. Methodology

### 4.1 Preference Elicitation and Blueprint Construction

The preference elicitation module (`src/preferences/interview.py`) operationalises the insight from §2.3: before any specialist agent is called, the system must reach agreement with the user on what the report is for, who will read it, and what it must contain.

The module proceeds in two stages. In the first stage, keyword heuristics extract audience signals (investor, executive, technical, general), priority signals (energy, budget, latency, resilience, policy, land, carbon), and depth signals (short, medium, detailed) from the user's initial query without any API call. This produces a `UserPreferences` object populated with inferred defaults. In the second stage, an optional LLM refinement pass improves these defaults using a single structured prompt, and the user is shown the inferred values and asked to confirm or adjust at most five targeted questions.

The resulting `UserPreferences` object is passed to the **Blueprint Optimiser** (`src/planning/blueprint_optimizer.py`), which constructs a `ReportBlueprint`. The blueprint specifies:

- An ordered list of `ReportSection` objects, each with a name, purpose, depth, and list of required evidence items
- A list of agents selected for this query (`agents_to_run`) and agents explicitly skipped (`agents_to_skip`)
- A list of `AgentTask` objects mapping each selected agent to the report sections it must provide evidence for, the goal of its analysis, and the required output fields

Blueprint construction is governed by the current policy weights (§4.2): a high `risk_severity` weight causes risk-related sections to be placed earlier and given greater depth; a high `conciseness` weight reduces the number of sections and their depth. The LLM generates the blueprint as structured JSON; if the LLM is unavailable, a rule-based fallback constructs the blueprint from the preferences directly.

The blueprint is displayed to the user for approval. If the user requests modifications, their feedback is parsed by an LLM call that extracts preference updates, the preferences are revised, and the blueprint is regenerated. This loop continues until the user approves or a maximum iteration count is reached. No agent is called before approval is received.

### 4.2 RL-Inspired Policy Optimisation for Blueprint Orchestration

The policy module implements a lightweight form of reinforcement learning from human feedback (RLHF) applied to the blueprint generation process, drawing on the contextual bandit formulation in which an agent observes a context, selects an action, and receives a scalar reward.

**State representation.** The context is the `UserPreferences` object: a structured representation of audience type, report depth, primary priorities, risk tolerance, and must-include/avoid lists. This context is not explicitly encoded as a feature vector; rather, it is passed directly to the blueprint optimiser, which uses the policy weights to influence blueprint structure.

**Action space.** The action is the blueprint structure: section ordering, section depth, agent selection, and evidence requirements. The policy weights modulate this action by shifting the blueprint optimiser's LLM prompt and rule-based fallback toward higher or lower values of each policy dimension.

**Policy representation.** The policy is a five-dimensional weight vector persisted in `data/policy/blueprint_policy.json`:

| Dimension | Governs |
|-----------|---------|
| `decision_relevance` | Priority given to sections with direct decision implications |
| `risk_severity` | Depth and placement of risk and uncertainty sections |
| `evidence_strength` | Depth of evidence requirements per section |
| `uncertainty_importance` | Visibility of data gaps and placeholder scores |
| `conciseness` | Preference for shorter, sharper report structures |

The vector is maintained on the probability simplex (all weights sum to one) through L1 normalisation after each update.

**Reward function.** After each run, a scalar reward in [0, 1] is computed as:

```
reward = 0.40 × user_acceptance
       + 0.30 × (critic_score / 10)
       + 0.20 × blueprint_approved_first_try
       + 0.10 × efficiency_score
```

**Update rule.** Policy weights are nudged by additive increments derived from two sources: keyword signals extracted from the user's free-text feedback (e.g. "more risk detail" increases `risk_severity` by a fixed δ), and critic findings (e.g. low `risk_coverage_score` from the blueprint critic increases `risk_severity` independently of user feedback). A positive acceptance signal reinforces the currently dominant weight. All updates are followed by normalisation.

This update rule does not constitute gradient-based policy optimisation, but it respects the key structural properties of a bandit update: it adjusts the policy in the direction of the reward signal, it maintains a valid probability distribution, and it accumulates information across sessions through persistence. A history of up to fifty run summaries is maintained in `data/policy/run_memory.json`, enabling post-hoc analysis of policy evolution.

### 4.3 Selective Agent Dispatch via Blueprint Task Mapping

The task dispatcher (`src/planning/task_dispatcher.py`) converts the approved blueprint into a set of calls to the existing `AgentRunner` infrastructure without modifying that infrastructure. For each agent in `blueprint.agents_to_run`, the dispatcher:

1. Retrieves the corresponding `AgentTask` from the blueprint (or constructs a default task)
2. Builds an enriched payload comprising the standard geospatial feature rows, a blueprint task descriptor (goal, required outputs, section targets), and the overall blueprint context (report title, goal, section names)
3. Calls `AgentRunner.run(agent_name, query, workload, payload)` with the enriched payload
4. Parses the response into a typed `AgentOutput` object, routing claims, risks, uncertainties, and data gaps to their designated report sections

Agents in `blueprint.agents_to_skip` are not called. This selective dispatch is the mechanism by which the blueprint reduces unnecessary API calls: a disaster-recovery query that does not require climate analysis will not call `ClimateCoolingAgent`; a carbon-optimised query with no latency constraint will de-prioritise `LatencyAgent`.

The `AgentOutput` schema is standardised across all agents:

```json
{
  "agent_name": "...",
  "section_targets": ["Risk and Uncertainty", "Top Site Recommendations"],
  "claims": [{"text": "...", "decision_relevance": 0.0, "evidence_strength": 0.0}],
  "risks": [],
  "uncertainties": [],
  "data_gaps": [],
  "recommendation_impact": "..."
}
```

This structured output is consumed by the report composer in Layer 3 to populate sections according to the blueprint's ordering and depth specifications.

### 4.4 Deterministic Auditable Scoring

The quantitative ranking of candidate sites is computed by a fully deterministic, closed-form scoring pipeline that is invoked identically regardless of whether the system is running in blueprint mode or standard mode. The pipeline operates on a feature table of 370+ Local Authority Districts with 50+ computed columns, and produces eight raw dimension scores and a workload-weighted composite.

**Raw score computation** (`data_centre_site_selector/scoring.py`):

| Dimension | Formula | Notes |
|-----------|---------|-------|
| Energy | `0.55×cap_score + 0.25×op_score + 0.20×pipe_score + 0.8×gsp_bonus` | All sub-scores normalised to [0,10] |
| Water | `7.5 − 2.0 × pop_score` | Population-pressure heuristic (placeholder) |
| Climate | Linear on latitude | Cooling proxy (placeholder) |
| Latency | `max(0, 10 − hub_distance_km / 45)` | Data-derived demand hubs |
| Resilience | `8.0 − z2×1.5 − z3×3.5 − missing×0.8` | Flood zone flags |
| Land | `0.65×hectares_score + 0.35×site_count_score` | Brownfield only |
| Planning risk | `z2×1.5 + z3×3.0 + missing×1.0 + dq_flag×1.0` | Penalty term |

**Workload-weighted composite** (`data_centre_site_selector/config.py`):

Five workload profiles map the eight dimensions to distinct weight vectors. Excerpt:

```python
"ai_training":          {"energy": 0.28, "water": 0.14, "climate": 0.20, ...}
"financial_low_latency": {"energy": 0.14, "latency": 0.42, ...}
"backup_disaster_recovery": {"resilience": 0.34, "primary_hub_separation": 0.12, ...}
```

All formulas are open for inspection in the source files. LLM agents receive the computed scores as input and produce explanations; they do not modify the scores. This strict separation between computation and narration is what makes the system's outputs auditable and reproducible.

### 4.5 Evaluation Architecture: Blueprint Critic and Coherence Evaluator

Two independent evaluation components operate on different aspects of the system and serve different validation purposes.

**Blueprint Critic** (`src/reports/critic.py`) evaluates the *final report* against the *approved blueprint*. It is implemented as an LLM-based judge that receives the report text (truncated to bound token cost), the blueprint section specifications, and the user preferences, and returns a `BlueprintCriticResult` containing a score in [0, 10], a boolean blueprint coverage flag, lists of missing sections and missing evidence items, lists of unsupported claims, and a clarity and risk coverage score. A rule-based fallback using section-name substring matching is used when the LLM is unavailable. The critic's score feeds directly into the reward function (§4.2), creating a closed loop between report quality and policy adaptation.

**Coherence Evaluator** (`tests/eval/agent_coherence.py`) evaluates the *agent outputs* against verifiable domain-specific criteria, entirely without LLM involvement. Four checks are applied to each specialist agent's full output (concatenation of `summary`, `key_points`, and `risks` fields):

1. **Keyword relevance.** Each specialist agent is associated with a vocabulary of domain-specific terms (e.g. `EnergyAgent`: `renewable`, `capacity`, `grid`, `gsp`, `operational`). The check passes if at least 40% of expected terms appear across the agent's output. Checking all fields rather than only the `summary` is important because agents frequently place quantitative vocabulary in `key_points`.

2. **Score alignment.** The agent's overall sentiment (ratio of positive to negative indicator words) is compared against the numeric score of the top-ranked candidate. A contradiction is flagged only when negative words outnumber positive words by a factor of 1.5 or more — a threshold chosen to accommodate the epistemic hedging that agents appropriately apply when reporting placeholder scores.

3. **Confidence calibration.** An agent that claims high confidence while simultaneously using placeholder language (`"heuristic"`, `"proxy"`, `"not modelled"`) is flagged as overconfident. This check enforces consistency between the agent's epistemic claims and its epistemic language.

4. **Region mention.** An agent should reference at least one of the candidate regions it was asked to analyse. Deterministic fallback responses, which contain no region information, are exempted from this check.

The coherence evaluator is entirely independent of the LLM stack. It can be run without any API key and produces reproducible results, providing a validation layer that does not inherit the stochasticity of the system it evaluates.

---

## 5. Multi-Agent System Design

The system deploys nine distinct agent roles across Layers 1, 2, and 3. Agent specialisation is implemented through prompt differentiation and model tier assignment; the underlying `AgentRunner` infrastructure is shared.

### Specialist Agents (Layer 2)

Each specialist agent receives the same top-K ranked feature rows but a different focus directive, blueprint task descriptor, and required output schema.

| Agent | Domain | Primary sections targeted |
|-------|--------|--------------------------|
| `EnergyAgent` | Renewable capacity, operational vs pipeline energy, GSP proximity | Energy, Carbon, Site Recommendations |
| `WaterAgent` | Population-pressure water heuristic, cooling constraints, data gaps | Risk, Uncertainty |
| `ClimateCoolingAgent` | Latitude cooling proxy, climate suitability assessment | Energy, Carbon |
| `LatencyAgent` | Distance to demand hubs, workload-specific latency requirements | Site Recommendations, Latency |
| `ResilienceAgent` | Flood zone flags, missing data, resilience constraints | Risk, Uncertainty |
| `LandPlanningAgent` | Brownfield availability, planning risk, England-only data coverage | Site Recommendations, Land |

### Meta-Agents

| Agent | Role | Layer | Model tier |
|-------|------|-------|-----------|
| `CriticAgent` | Identifies weaknesses in specialist analyses, flags overconfident assumptions, recommends additional datasets | 2 | Reasoning |
| `SynthesisAgent` | Produces final narrative grounded strictly in the deterministic ranking; adjudicates between specialist assessments | 2 | Reasoning |
| `PolicyResearchAgent` | Web search for current UK policy, grants, AI Growth Zone eligibility, Freeport incentives | 2 (optional) | Web-enabled |

### Model Tier Routing

```
FAST_MODEL      (gpt-4o-mini) → EnergyAgent, WaterAgent, ClimateCoolingAgent,
                                 LatencyAgent, ResilienceAgent, LandPlanningAgent
REASONING_MODEL (gpt-4o)      → CriticAgent, SynthesisAgent, blueprint generation,
                                 preference refinement, blueprint critique
WEB_MODEL       (gpt-4o)      → PolicyResearchAgent (requires --enable-web-policy)
```

All agents return a structured JSON response with fields `agent`, `summary`, `key_points`, `risks`, and `confidence`. All agents degrade to a deterministic fallback if the model call fails or times out, ensuring the pipeline never blocks on API availability.

---

## 6. Data Sources and Feature Engineering

All datasets are sourced from official UK public bodies under Open Government Licence v3.0. Raw files are stored under `data/raw/` and are not committed to the repository.

| Source | Dataset | Used for | Join type |
|--------|---------|---------|-----------|
| ONS | LAD Boundaries Dec 2024 (BUC) | Candidate region generation (370+ LADs) | Centroid extraction |
| DESNZ | Renewable Energy Planning Database (REPD) | Renewable capacity features | 50 km radius aggregation |
| NESO | GSP Regions 2025-01-02 | Grid Supply Point proximity | Point-in-polygon |
| Environment Agency | Flood Map for Planning — Zones 2 & 3 | Resilience scoring | Polygon intersection |
| ONS | Population estimates mid-2024 | Water stress heuristic, population strain | LAD code join |
| DLUHC | Brownfield Land Register | Land availability scoring | 50 km radius aggregation |
| DLUHC | Brownfield Site Register | Site count per area | 50 km radius aggregation |

Feature engineering is implemented in `data_centre_site_selector/preprocess.py`. The principal operations are radius-based capacity aggregations (summing REPD renewable project capacity within 50 km of each LAD centroid), flood zone intersection (checking whether a LAD centroid falls within EA Flood Zones 2 or 3), and population joins using ONS LAD codes. The resulting feature table is cached at `data/processed/candidate_region_features.csv` and loaded without recomputation on subsequent runs.

---

## 7. Evaluation Framework

The evaluation framework (`tests/eval_runner.py`) provides structured evidence across four independent modules, each addressing a distinct validation criterion. The framework is designed so that Modules 1–3 require no API key and produce deterministic results; Module 4 (agent coherence) requires an active `OPENAI_API_KEY` and operates on live agent outputs.

**Module 1 — Benchmark Suite.**
Five fixed canonical queries are executed against the pipeline in `--no-agents` mode. Each query has verifiable expected properties: the correct workload type (inferred by the prompt parser), the correct regional scope (UK, country, or city level), a minimum number of feasible recommendations, the expected country of the top recommendation, and valid score ranges. The benchmark provides an end-to-end integration test of the constraint parsing, feature loading, scoring, planning, and budget allocation components.

**Module 2 — Score Stability.**
The deterministic scoring pipeline is executed multiple times against the same feature table and the same query. The maximum absolute deviation across all score columns and all candidate regions is computed. A pipeline that is truly deterministic must produce zero deviation. This module also verifies that workload weight vectors produce orderings consistent with domain knowledge: AI training queries should rank high-energy sites above low-energy sites; financial latency queries should rank low-hub-distance sites above high-hub-distance sites.

**Module 3 — Ground Truth Approximation.**
The system's national ranking (all candidates, standard AI training query) is compared against a set of seven publicly documented UK data centre clusters derived from commercial market reports (CBRE, JLL) and the Datacenter Map database. The evaluation measures precision@20 (the fraction of the system's top-20 candidates that correspond to known commercial data centre locations) and cluster coverage (the fraction of known clusters that appear anywhere in the top-50 ranked candidates).

**Module 4 — Agent Coherence.**
The four-check coherence evaluation described in §4.5 is applied to the outputs of all six specialist agents from a single live run. Results are reported per agent and in aggregate. A pass threshold of three out of four checks is applied at the individual agent level; a system-level pass requires at least 60% of agents to pass.

---

## 8. Relation to Existing Work

The system's design draws on and extends several distinct strands of prior work.

**Multi-agent systems for decision support.** The decomposition of complex analytical tasks across specialist agents with a meta-agent critique layer follows the multi-agent debate and reflection paradigm explored in recent work on LLM-based reasoning (e.g. Du et al., 2023; Liang et al., 2023). The key distinction of this system is the explicit pre-execution planning layer: rather than dispatching agents immediately and composing their outputs post-hoc, the system first constructs and approves a research blueprint that governs the agents' behaviour.

**Reinforcement learning from human feedback.** The policy update mechanism draws on the RLHF formalism (Christiano et al., 2017; Stiennon et al., 2020) but implements it at the level of report structure rather than model parameters. The analogy to the contextual bandit setting (Langford and Zhang, 2007) is explicit: the context is the user preferences, the action is the blueprint, and the reward combines user acceptance with an automated critic score. This formulation avoids the computational overhead of neural policy gradient methods while preserving the key adaptive property: the system improves over repeated use.

**Spatial multi-criteria decision analysis.** The scoring pipeline implements a weighted linear combination of normalised criteria scores, following the standard MCDA approach to site selection (Malczewski, 1999). The key contribution relative to standard GIS-based MCDA tools is the integration of LLM-based explanation and critique agents, which surface the uncertainty and data quality limitations of the quantitative scores in natural language accessible to non-specialist stakeholders.

**Reproducibility in AI-assisted research.** The strict separation between deterministic computation and LLM narration addresses the reproducibility problem identified by Gundersen and Kjensmo (2018) in the context of AI research. The system treats the quantitative pipeline as confirmatory analysis (requiring reproducibility) and the LLM agents as exploratory narration (permitted to vary within coherence bounds verified by the evaluator).

**Comparison to general-purpose AI tools.** General-purpose AI assistants (GPT-4, Claude Code) can generate plausible site selection narratives but are structurally unable to provide the properties this system guarantees:

| Property | General AI Assistant | This System |
|----------|---------------------|-------------|
| Processes authoritative geospatial datasets | No | Yes |
| Reproducible quantitative scores | No | Yes |
| Stakeholder-adapted report structure | Partially, via prompt | Yes, via typed preferences + approved blueprint |
| Persistent improvement across sessions | No | Yes, via RL policy |
| Independent coherence validation | No | Yes, via deterministic evaluator |
| Traceable score derivation | No | Yes, via open formula pipeline |

---

## 9. Setup

### Prerequisites

- Conda (recommended) or Python 3.12+
- OpenAI API key (optional — all deterministic features operate without it)

### Environment

```bash
git clone https://github.com/vitjuli/multi-agents-infosys.git
cd multi-agents-infosys

conda env create -f environment.yml
conda activate InfoHack
```

If the environment already exists:

```bash
conda env update -f environment.yml --prune
conda activate InfoHack
```

### API Key Configuration

Create a `.env` file in the repository root:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_MODEL_REASONING=gpt-4o
OPENAI_MODEL_WEB=gpt-4o
```

### Data Acquisition

```bash
bash data_download.sh
```

Raw datasets are placed under `data/raw/`. The Environment Agency Flood Zones file is approximately 2 GB; flood processing is optional and excluded from the default build.

### Feature Table Build

```bash
# Standard build (~2 minutes, no flood zones)
python scripts/build_features.py

# With flood zone processing (~15 minutes, requires ~4 GB RAM)
python scripts/build_features.py --include-flood
```

This produces `data/processed/candidate_region_features.csv` with 370+ LAD candidates and 50+ computed features. Subsequent runs load from cache immediately.

---

## 10. Running the Pipeline

### 10.1 Blueprint Mode (Full Pipeline — Recommended)

```bash
python blueprint_main.py
```

With a pre-specified query:

```bash
python blueprint_main.py \
  --prompt "Find the best UK locations for a 100 MW AI training data centre, optimise for low carbon and cost" \
  --budget "£900m"
```

Full option reference:

```bash
python blueprint_main.py \
  --prompt "..."          \   # research query (omit for interactive input)
  --budget "£1.2bn"       \   # budget string (£, GBP, bn, m all recognised)
  --region "Scotland"     \   # restrict scope: UK country or city name
  --compute-mw 100        \   # override compute capacity parsing
  --top-k 5               \   # number of ranked candidates
  --no-agents             \   # skip all OpenAI calls (deterministic only)
  --no-llm-prefs          \   # skip LLM preference refinement
  --json                  \   # also write JSON output to reports/
  --debug                     # verbose logging to stderr
```

Via the existing CLI entry point:

```bash
python -m data_centre_site_selector.main --blueprint-mode \
  --prompt "..." --budget "£900m"
```

**Interactive flow:**

```
1.  User enters research query (or pass --prompt)
2.  System infers preferences from query (audience, depth, priorities)
3.  User answers up to five clarifying questions (Enter to accept defaults)
4.  Blueprint Optimiser generates a structured report plan
5.  Blueprint is displayed; user types 'yes' to approve or describes changes
6.  Preference and blueprint update loop (maximum five iterations)
7.  Feature table loads from cache (instant after first build)
8.  Selected specialist agents run against top-K candidates
9.  Critic Agent and Synthesis Agent run
10. Report Composer assembles sections in blueprint order
11. Blueprint Critic evaluates the report (LLM-based, score 0–10)
12. User accepts the report or requests changes
13. Policy weights updated and persisted to data/policy/blueprint_policy.json
```

### 10.2 Standard Pipeline (Existing Baseline)

```bash
# Full run with OpenAI specialist agents
python -m data_centre_site_selector.main \
  --prompt "Find UK locations for 100 MW AI training, optimise for CO2 and cost" \
  --budget "£1.2bn" \
  --region England \
  --top-k 5

# Deterministic only (no API key required)
python -m data_centre_site_selector.main \
  --prompt "Find UK-wide options for a 60 MW inference platform" \
  --no-agents \
  --json

# With web-enabled policy research
python -m data_centre_site_selector.main \
  --prompt "80 MW AI training in North East with policy support and low CO2" \
  --budget "£900m" \
  --enable-web-policy

# Debug logging
python -m data_centre_site_selector.main \
  --prompt "..." \
  --debug-logs \
  --log-file reports/debug.log
```

Supported workload profiles (override automatic inference):

```bash
--workload ai_training
--workload ai_inference
--workload financial_low_latency
--workload enterprise_colocation
--workload backup_disaster_recovery
```

### 10.3 Systematic Evaluation

```bash
# Deterministic checks only (~30 seconds, no API key required)
python tests/eval_runner.py --fast

# Full evaluation including live agent coherence (~3 minutes, requires OPENAI_API_KEY)
python tests/eval_runner.py --fast --with-agents

# Full evaluation with three stability runs
python tests/eval_runner.py --with-agents
```

Results are written to `reports/evaluation_results.md` (human-readable) and `reports/evaluation_results.json` (machine-readable).

### 10.4 Utility Scripts

```bash
python scripts/inspect_datasets.py      # Inspect raw data files
python scripts/build_features.py        # Rebuild feature table
python scripts/check_openai_setup.py    # Verify API connectivity
```

### 10.5 Output Files

| Path | Contents |
|------|---------|
| `reports/latest_report.md` | Full technical report (standard pipeline) |
| `reports/latest_summary.md` | Executive summary (standard pipeline) |
| `reports/blueprint_report.md` | Report composed per approved blueprint |
| `reports/blueprint_output.json` | Full structured output including preferences, blueprint, critic result |
| `reports/evaluation_results.md` | Systematic evaluation report |
| `reports/evaluation_results.json` | Machine-readable evaluation results |
| `data/processed/latest_rankings.csv` | Full ranked candidate table with all scores |
| `data/policy/blueprint_policy.json` | Current RL policy weights |
| `data/policy/run_memory.json` | Session history (up to 50 runs) |

---

## 11. Project Structure

```
multi-agents/
│
├── data_centre_site_selector/        # Core pipeline package
│   ├── agents.py                     # AgentRunner + all 9 agent roles
│   ├── config.py                     # Workload weight profiles (5 × 8 dimensions)
│   ├── critics.py                    # Deterministic critics (scope, budget, data quality)
│   ├── data_analysis.py              # Production scoring + nested spatial search
│   ├── explainer.py                  # Explanation and feedback generation
│   ├── main.py                       # CLI entry point (--blueprint-mode delegates)
│   ├── orchestrator.py               # Standard pipeline orchestration
│   ├── planner.py                    # Constraint-based planning + recommendation builder
│   ├── preprocess.py                 # Feature engineering (8 data sources, 500+ lines)
│   ├── prompt_parser.py              # Natural language constraint extraction
│   ├── report.py                     # Markdown + terminal report generation
│   ├── schemas.py                    # Typed dataclasses (UserConstraints, SiteSelectionResult, …)
│   └── scoring.py                    # Deterministic raw score computation
│
├── src/                              # Blueprint system (new)
│   ├── llm_client.py                 # Thin OpenAI chat wrapper (chat_json, chat_text)
│   ├── preferences/
│   │   ├── schemas.py                # UserPreferences, ReportBlueprint, AgentOutput, …
│   │   └── interview.py              # Preference interview (heuristic + LLM refinement)
│   ├── planning/
│   │   ├── blueprint_optimizer.py    # Policy-weighted blueprint generation + rule fallback
│   │   ├── report_blueprint.py       # Blueprint display utilities
│   │   └── task_dispatcher.py        # Blueprint → AgentRunner call mapping
│   ├── rl/
│   │   ├── blueprint_policy.py       # Policy load/save, DEFAULT_POLICY
│   │   ├── policy_update.py          # Reward computation + additive weight update
│   │   └── memory.py                 # Run history (JSON, capped at 50 sessions)
│   └── reports/
│       ├── final_report_composer.py  # Section-ordered report assembly
│       └── critic.py                 # Blueprint critic (LLM + rule-based fallback)
│
├── tests/
│   ├── eval/
│   │   ├── benchmark_cases.py        # 5 canonical test queries with expected properties
│   │   ├── ground_truth.py           # Known UK DC cluster validation
│   │   ├── agent_coherence.py        # 4-check deterministic anti-hallucination evaluator
│   │   └── score_stability.py        # Determinism and ordering verification
│   └── eval_runner.py                # Main evaluation script → evaluation_results.md
│
├── scripts/
│   ├── build_features.py             # Feature table builder
│   ├── inspect_datasets.py           # Data file inspector
│   └── check_openai_setup.py         # API connectivity test
│
├── data/
│   ├── raw/                          # Source datasets (not committed)
│   ├── processed/                    # Feature cache + rankings (not committed)
│   └── policy/
│       ├── blueprint_policy.json     # Current RL policy weights
│       └── run_memory.json           # Session run history
│
├── reports/                          # Generated outputs (gitignored)
├── blueprint_main.py                 # Blueprint pipeline entry point
├── environment.yml                   # Conda environment specification
├── requirements.txt                  # pip dependency list
└── data_download.sh                  # Dataset acquisition script
```

---

## 12. Known Limitations and Future Directions

### Placeholder Scores

Two scoring dimensions are acknowledged placeholders pending integration of authoritative datasets:

- **Water score** (`scoring.py:51`) — currently a population-pressure heuristic (`7.5 − 2.0 × pop_score`). Should be replaced with Environment Agency water abstraction licence data and CAMS stress indices.
- **Climate score** (`scoring.py:55`) — currently a latitude cooling proxy. Should be replaced with HadUK-Grid 1 km climate normals and heatwave frequency projections.

These limitations are explicitly surfaced in every report through the `data_quality_notes` field and the uncertainty section.

### Data Coverage Gaps

- Flood zone data is excluded from the default feature build due to file size; sites lacking flood data receive a missingness penalty in the resilience score
- Northern Ireland has no candidates in the current feature table due to ONS boundary coverage
- Scotland has reduced accuracy in water and population scores due to England/Wales ONS workbook coverage
- Grid headroom, connection queue position, and existing data centre capacity are not currently modelled

### Architectural Limitations

- Specialist agents execute sequentially; parallel execution using `concurrent.futures.ThreadPoolExecutor` would reduce wall-clock time by approximately the number of agents
- Agent token costs are not tracked per run; a cost audit trail is planned
- The policy update rule is additive rather than gradient-based; a Gaussian process or Thompson sampling approach would provide better uncertainty quantification over the preference space

### Future Directions

- Integration of DNO/TO grid constraint and connection queue data from National Grid ESO
- `research_hpc` workload profile for HPC and AI research infrastructure placement
- Web interface for blueprint approval with map visualisation and radar chart score display
- Formal A/B evaluation comparing blueprint-mode and standard-mode report acceptance rates
- Extension of the ground truth validation to the full 374-LAD national candidate set

---

## Acknowledgements

Dataset sources: Office for National Statistics (ONS), Department for Energy Security and Net Zero (DESNZ), National Energy System Operator (NESO), Environment Agency (EA), Department for Levelling Up, Housing and Communities (DLUHC). All datasets used under Open Government Licence v3.0.

Built for the Cambridge AI & Information Systems Hackathon, 2026.

---

*This system is a research prototype. Scores are heuristic approximations of the underlying real-world quantities. Water and climate scores are explicitly placeholder values pending integration of authoritative datasets. Outputs must not be used as the sole basis for investment, planning, or regulatory decisions without independent professional validation.*
