# RL-Guided Report Optimisation Architecture

## 1. Purpose

This document describes the technical architecture of our multi-agent pipeline and explains where the reinforcement-learning component sits, what it optimises, and how we can implement it in the MVP.

The key idea is:

> We do not use RL to generate text directly. We use RL to optimise evidence selection for the final report.

The system first generates multiple candidate reports from specialist agent outputs. It then decomposes those reports into atomic claims, scores each claim, and uses a learned policy to decide which claims should appear in the executive summary, main report, risk section, appendix, or be discarded.

The policy is updated from critic feedback and human feedback, creating a lightweight reinforcement-learning/preference-learning loop.

---

## 2. High-Level Architecture

```text
User Query
   ↓
Planner Module
   ↓
Specialist Agents
   ↓
Raw Evidence Store
   ↓
Candidate Report Generator
   ├── Report A: Executive-first report
   └── Report B: Technical-first report
   ↓
Claim Extraction Layer
   ↓
Claim Scoring Layer
   ↓
RL / Preference Policy Layer
   ↓
Evidence Selection Module
   ↓
Final Report Composer
   ↓
Critic Module
   ↓
Human Feedback
   ↓
Policy Update
```

Final one-line summary:

```text
Multi-agent evidence generation → dual report candidates → atomic claim extraction → RL-guided claim selection → final decision-ready report → critic/user feedback → policy update.
```

---

## 3. Why We Need the RL Layer

A normal multi-agent pipeline often produces too much information:

```text
Planner output
Budget analysis
Land/data analysis
Climate analysis
Latency analysis
Resilience analysis
Regulation analysis
Critic findings
Raw scoring tables
Candidate site rankings
```

If we simply concatenate all outputs into one report, the final result becomes long, noisy, and hard to use for decision-making.

Therefore, the RL layer solves the following problem:

> From all generated information, select the most decision-relevant claims for the final report.

This is not random section selection. The system evaluates each atomic claim and decides whether it should be included, highlighted, moved to appendix, or discarded.

---

## 4. Full Technical Diagram

```text
┌──────────────────────────────────────┐
│ 1. USER INPUT                         │
│                                      │
│ Example:                             │
│ "Find the best site for an AI data   │
│ centre in Europe, optimising for     │
│ budget, low-carbon energy, and       │
│ latency."                            │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 2. PLANNER MODULE                     │
│                                      │
│ Input: user query                    │
│ Output: structured task plan         │
│                                      │
│ Produces:                            │
│ - project goal                       │
│ - assumptions                        │
│ - required specialist agents         │
│ - scoring dimensions                 │
│ - expected report structure          │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 3. SPECIALIST AGENTS                  │
│                                      │
│ Each agent returns structured output │
│ rather than free text only.          │
│                                      │
│ Possible agents:                     │
│ - BudgetAgent                        │
│ - LandDataAgent                      │
│ - ClimateEnergyAgent                 │
│ - LatencyAgent                       │
│ - ResilienceAgent                    │
│ - RegulationAgent                    │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 4. RAW EVIDENCE STORE                 │
│                                      │
│ Stores all agent outputs as JSON:    │
│ - facts                              │
│ - risks                              │
│ - assumptions                        │
│ - uncertainties                      │
│ - candidate site scores              │
│ - data gaps                          │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 5. CANDIDATE REPORT GENERATOR         │
│                                      │
│ Generates two candidate reports:     │
│                                      │
│ Report A: Executive-first report     │
│ - concise                            │
│ - decision-focused                   │
│ - clear recommendation first         │
│                                      │
│ Report B: Technical-first report     │
│ - more detailed                      │
│ - more methodology                   │
│ - more uncertainty/data discussion   │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 6. CLAIM EXTRACTION LAYER             │
│                                      │
│ Input: Report A + Report B           │
│ Output: atomic claims                │
│                                      │
│ Instead of selecting whole sections, │
│ we decompose both reports into small │
│ decision-relevant claims.            │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 7. CLAIM SCORING LAYER                │
│                                      │
│ Each claim receives scores:          │
│ - decision_relevance                 │
│ - risk_severity                      │
│ - evidence_strength                  │
│ - uncertainty_importance             │
│ - novelty                            │
│ - user_preference_alignment          │
│ - redundancy_score                   │
│ - conflict_flag                      │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 8. RL / PREFERENCE POLICY LAYER       │
│                                      │
│ THIS IS THE RL COMPONENT.            │
│                                      │
│ State:                               │
│ - user query                         │
│ - user priorities                    │
│ - candidate claims                   │
│ - critic feedback                    │
│ - previous user preferences          │
│                                      │
│ Action:                              │
│ For each claim choose:               │
│ - include_main_report                │
│ - include_executive_summary          │
│ - highlight_as_risk                  │
│ - move_to_appendix                   │
│ - discard                            │
│ - ask_for_more_data                  │
│                                      │
│ Reward:                              │
│ - user accepts final report          │
│ - user prefers this version          │
│ - critic score improves              │
│ - fewer missing critical risks       │
│ - concise but complete report        │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 9. EVIDENCE SELECTION MODULE          │
│                                      │
│ Uses policy weights to select claims │
│ for:                                 │
│ - Executive Summary                  │
│ - Main Report                        │
│ - Risk Section                       │
│ - Technical Appendix                 │
│ - Discarded Information              │
│                                      │
│ Also performs:                       │
│ - deduplication                      │
│ - conflict detection                 │
│ - merging overlapping claims         │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 10. FINAL REPORT COMPOSER             │
│                                      │
│ Input: selected claims               │
│ Output: final optimised report       │
│                                      │
│ The final report is not Report A or  │
│ Report B. It is Report C:            │
│                                      │
│ Report C = best decision-relevant    │
│ claims from both A and B, selected   │
│ by RL-guided evidence policy.        │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 11. CRITIC MODULE                     │
│                                      │
│ Evaluates final report:              │
│ - Are critical risks included?       │
│ - Are unsupported claims removed?    │
│ - Is uncertainty visible?            │
│ - Is recommendation clear?           │
│ - Is report concise?                 │
│                                      │
│ Output: critic_score + feedback      │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 12. HUMAN FEEDBACK                    │
│                                      │
│ User can answer:                     │
│ - accept report                      │
│ - reject report                      │
│ - prefer more technical detail       │
│ - prefer more concise summary        │
│ - ask to highlight risks             │
│ - ask for more uncertainty           │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│ 13. POLICY UPDATE                     │
│                                      │
│ Updates claim selection weights:     │
│ - decision_relevance                 │
│ - risk_severity                      │
│ - evidence_strength                  │
│ - uncertainty_importance             │
│ - novelty                            │
│                                      │
│ This closes the learning loop.       │
└──────────────────────────────────────┘
```

---

## 5. Where Exactly Is RL?

RL sits here:

```text
Claim Scoring Layer
   ↓
RL / Preference Policy Layer
   ↓
Evidence Selection Module
```

The RL layer does not generate prose directly. It decides what evidence is important enough to include.

Specifically, it answers:

```text
For this user query and this decision context, which claims should appear in the final report?
```

---

## 6. RL Formulation

### 6.1 State

The state contains the context available before selecting evidence.

```python
state = {
    "user_query": "...",
    "user_priorities": ["budget", "low-carbon", "latency"],
    "audience": "executive",
    "claims": candidate_claims,
    "critic_feedback": previous_critic_feedback,
    "previous_preferences": user_preference_history,
}
```

### 6.2 Actions

For each claim, the policy selects one action:

```python
actions = [
    "include_executive_summary",
    "include_main_report",
    "highlight_as_risk",
    "move_to_appendix",
    "discard",
    "ask_for_more_data",
]
```

### 6.3 Reward

A simple reward function for the MVP:

```python
reward = (
    0.40 * user_acceptance
    + 0.25 * critic_score
    + 0.20 * report_completeness
    + 0.15 * conciseness_score
)
```

Where:

```text
user_acceptance:
1 if the user accepts the final report, 0 otherwise.

critic_score:
LLM critic score for coverage, uncertainty, unsupported claims, clarity, and risk handling.

report_completeness:
Whether all high-priority dimensions are covered.

conciseness_score:
Penalises irrelevant or redundant information.
```

---

## 7. Atomic Claim Format

Both candidate reports should be decomposed into atomic claims.

Example claim:

```json
{
  "claim_id": "c001",
  "text": "Stockholm has strong low-carbon electricity access.",
  "source_report": "A",
  "category": "climate_energy",
  "site": "Stockholm",
  "decision_relevance": 0.92,
  "risk_severity": 0.10,
  "evidence_strength": 0.80,
  "uncertainty_importance": 0.20,
  "novelty": 0.75,
  "redundancy_score": 0.15,
  "conflict_flag": false
}
```

Another example:

```json
{
  "claim_id": "c002",
  "text": "Stockholm may have latency disadvantages for Southern European users.",
  "source_report": "B",
  "category": "latency",
  "site": "Stockholm",
  "decision_relevance": 0.88,
  "risk_severity": 0.70,
  "evidence_strength": 0.65,
  "uncertainty_importance": 0.45,
  "novelty": 0.80,
  "redundancy_score": 0.10,
  "conflict_flag": false
}
```

The final report should not simply copy both claims. It should synthesise them:

```text
Stockholm is attractive because of strong low-carbon electricity access, but it carries a latency trade-off for Southern European workloads.
```

---

## 8. Policy Design

We use two lightweight policies.

### 8.1 Claim Importance Policy

This policy decides which information is important.

```python
claim_policy = {
    "decision_relevance": 0.30,
    "risk_severity": 0.25,
    "evidence_strength": 0.20,
    "uncertainty_importance": 0.15,
    "novelty": 0.10,
}
```

Claim score:

```python
claim_score = (
    claim_policy["decision_relevance"] * claim["decision_relevance"]
    + claim_policy["risk_severity"] * claim["risk_severity"]
    + claim_policy["evidence_strength"] * claim["evidence_strength"]
    + claim_policy["uncertainty_importance"] * claim["uncertainty_importance"]
    + claim_policy["novelty"] * claim["novelty"]
)
```

Action rules:

```python
if claim_score >= 0.75:
    action = "include_main_report"
elif claim_score >= 0.55:
    action = "move_to_appendix"
else:
    action = "discard"

# Override rules
if claim["risk_severity"] >= 0.85:
    action = "highlight_as_risk"

if claim["conflict_flag"] is True:
    action = "ask_for_more_data"
```

### 8.2 Report Style Policy

This policy decides how to present the selected evidence.

```python
style_policy = {
    "executive_summary": 0.35,
    "technical_detail": 0.25,
    "risk_emphasis": 0.25,
    "appendix_detail": 0.15,
}
```

Interpretation:

```text
High executive_summary weight:
- recommendation first
- short paragraphs
- fewer technical derivations

High technical_detail weight:
- more methodology
- more data caveats
- more assumptions

High risk_emphasis weight:
- risk section appears earlier
- critical risks highlighted

High appendix_detail weight:
- more technical information moved to appendix instead of main report
```

---

## 9. MVP Implementation Plan

For the hackathon, we do not need full deep RL. We implement a lightweight RL-inspired contextual bandit / preference update loop.

MVP loop:

```text
1. Generate Report A and Report B.
2. Extract atomic claims from both reports.
3. Score claims using claim_policy.
4. Select top claims for the final report.
5. Generate Final Report C.
6. Critic evaluates Report C.
7. User gives feedback.
8. Update claim_policy and style_policy.
9. Regenerate improved Report C.
```

This is enough to demonstrate:

```text
state → action → reward → policy update
```

---

## 10. Suggested File Structure

```text
multi-agents/
  main.py
  .env
  .gitignore
  requirements.txt

  src/
    __init__.py
    openai_client.py

    modules/
      __init__.py
      planner.py
      budget.py
      land_data.py
      climate_energy.py
      latency.py
      resilience.py
      regulation.py

    reports/
      __init__.py
      candidate_report_generator.py
      claim_extractor.py
      claim_scorer.py
      evidence_selector.py
      final_report_composer.py
      critic.py

    rl/
      __init__.py
      policy.py
      reward.py
      policy_update.py
      memory.py
```

---

## 11. Module Responsibilities

### `planner.py`

Input:

```python
user_query: str
```

Output:

```python
plan: dict
```

Example:

```python
{
    "goal": "Select best AI data centre site",
    "priorities": ["budget", "low-carbon", "latency"],
    "agents_to_run": [
        "budget",
        "land_data",
        "climate_energy",
        "latency",
        "resilience",
        "regulation"
    ],
    "report_audience": "executive"
}
```

---

### Specialist Agents

Each specialist agent returns structured evidence.

Example from `budget.py`:

```python
{
    "agent": "budget",
    "findings": [
        {
            "site": "Stockholm",
            "claim": "Stockholm has higher land and labour costs than some Eastern European alternatives.",
            "evidence_strength": 0.70,
            "risk_severity": 0.45,
            "uncertainty": 0.30
        }
    ]
}
```

---

### `candidate_report_generator.py`

Generates:

```python
report_a = executive_report
report_b = technical_report
```

Report A is optimised for:

```text
clarity, conciseness, recommendation-first structure
```

Report B is optimised for:

```text
technical detail, assumptions, uncertainty, methodology
```

---

### `claim_extractor.py`

Input:

```python
report_a: str
report_b: str
```

Output:

```python
claims: list[dict]
```

It decomposes both reports into atomic claims.

---

### `claim_scorer.py`

Input:

```python
claims: list[dict]
claim_policy: dict
```

Output:

```python
scored_claims: list[dict]
```

Adds:

```python
claim["final_score"]
```

---

### `evidence_selector.py`

Input:

```python
scored_claims
```

Output:

```python
selected_evidence = {
    "executive_summary_claims": [],
    "main_report_claims": [],
    "risk_claims": [],
    "appendix_claims": [],
    "discarded_claims": []
}
```

---

### `final_report_composer.py`

Input:

```python
selected_evidence
style_policy
```

Output:

```python
final_report: str
```

---

### `critic.py`

Input:

```python
final_report
user_query
selected_evidence
```

Output:

```python
critic_result = {
    "critic_score": 0.82,
    "missing_risks": [],
    "unsupported_claims": [],
    "clarity_score": 0.80,
    "completeness_score": 0.85,
    "conciseness_score": 0.78,
    "feedback": "The report is clear but should highlight grid capacity uncertainty earlier."
}
```

---

### `policy_update.py`

Input:

```python
claim_policy
style_policy
critic_result
user_feedback
reward
```

Output:

```python
updated_claim_policy
updated_style_policy
```

---

## 12. Minimal Code-Level Flow

```python
def run_pipeline(user_query: str):
    # 1. Plan
    plan = planner_module(user_query)

    # 2. Run specialist agents
    budget = budget_agent(user_query, plan)
    land = land_data_agent(user_query, plan)
    climate = climate_energy_agent(user_query, plan)
    latency = latency_agent(user_query, plan)
    resilience = resilience_agent(user_query, plan)
    regulation = regulation_agent(user_query, plan)

    agent_outputs = {
        "budget": budget,
        "land": land,
        "climate": climate,
        "latency": latency,
        "resilience": resilience,
        "regulation": regulation,
    }

    # 3. Generate two candidate reports
    report_a = generate_executive_report(user_query, agent_outputs)
    report_b = generate_technical_report(user_query, agent_outputs)

    # 4. Extract atomic claims
    claims = extract_claims(report_a, report_b)

    # 5. Load current policies
    claim_policy = load_claim_policy()
    style_policy = load_style_policy()

    # 6. Score claims using policy
    scored_claims = score_claims(claims, claim_policy)

    # 7. Select evidence
    selected_evidence = select_evidence(scored_claims)

    # 8. Compose final report
    final_report = compose_final_report(
        selected_evidence=selected_evidence,
        style_policy=style_policy,
        user_query=user_query,
    )

    # 9. Critic evaluation
    critic_result = critic_evaluate(
        final_report=final_report,
        user_query=user_query,
        selected_evidence=selected_evidence,
    )

    # 10. Human feedback
    user_feedback = input(
        "Feedback? accept / too technical / too vague / more risk / more uncertainty: "
    )

    # 11. Reward + policy update
    reward = compute_reward(critic_result, user_feedback)

    updated_claim_policy, updated_style_policy = update_policy(
        claim_policy=claim_policy,
        style_policy=style_policy,
        critic_result=critic_result,
        user_feedback=user_feedback,
        reward=reward,
    )

    save_policy(updated_claim_policy, updated_style_policy)

    return {
        "report_a": report_a,
        "report_b": report_b,
        "claims": claims,
        "selected_evidence": selected_evidence,
        "final_report": final_report,
        "critic_result": critic_result,
        "reward": reward,
        "updated_claim_policy": updated_claim_policy,
        "updated_style_policy": updated_style_policy,
    }
```

---

## 13. Policy Update Logic for MVP

Initial policy:

```python
claim_policy = {
    "decision_relevance": 0.30,
    "risk_severity": 0.25,
    "evidence_strength": 0.20,
    "uncertainty_importance": 0.15,
    "novelty": 0.10,
}

style_policy = {
    "executive_summary": 0.35,
    "technical_detail": 0.25,
    "risk_emphasis": 0.25,
    "appendix_detail": 0.15,
}
```

Example policy update:

```python
def normalise_policy(policy: dict) -> dict:
    total = sum(max(v, 0.0) for v in policy.values())
    if total == 0:
        n = len(policy)
        return {k: 1.0 / n for k in policy}
    return {k: max(v, 0.0) / total for k, v in policy.items()}


def update_policy(claim_policy, style_policy, critic_result, user_feedback, reward):
    claim_policy = claim_policy.copy()
    style_policy = style_policy.copy()

    feedback = user_feedback.lower()
    critic_text = critic_result.get("feedback", "").lower()

    if "risk" in feedback or "risk" in critic_text:
        claim_policy["risk_severity"] += 0.05 * reward
        style_policy["risk_emphasis"] += 0.05 * reward

    if "uncertainty" in feedback or "uncertainty" in critic_text or "missing data" in critic_text:
        claim_policy["uncertainty_importance"] += 0.05 * reward

    if "too vague" in feedback:
        claim_policy["evidence_strength"] += 0.05 * reward
        style_policy["technical_detail"] += 0.05 * reward

    if "too technical" in feedback:
        style_policy["executive_summary"] += 0.05 * reward
        style_policy["technical_detail"] -= 0.03 * reward

    if "too long" in feedback:
        style_policy["executive_summary"] += 0.05 * reward
        style_policy["appendix_detail"] += 0.03 * reward

    claim_policy = normalise_policy(claim_policy)
    style_policy = normalise_policy(style_policy)

    return claim_policy, style_policy
```

This is a lightweight RL-inspired loop:

```text
state → action → reward → policy update
```

It is not full deep RL, but it is practical, explainable, and suitable for a hackathon MVP.

---

## 14. Demo Plan

The demo should make the RL component visible.

### Demo screen 1: Candidate Reports

```text
Report A: Executive-first
Report B: Technical-first
```

### Demo screen 2: Extracted and Scored Claims

| Claim | Source | Decision relevance | Risk severity | Evidence strength | Final score | Action |
|---|---:|---:|---:|---:|---:|---|
| Stockholm has low-carbon electricity access | A/B | 0.92 | 0.10 | 0.80 | 0.74 | Main report |
| Stockholm may have latency risk for Southern Europe | B | 0.88 | 0.70 | 0.65 | 0.79 | Highlight risk |
| Permitting timeline is uncertain | B | 0.76 | 0.82 | 0.55 | 0.77 | Highlight risk |
| Minor branding advantage | A | 0.20 | 0.05 | 0.30 | 0.18 | Discard |

### Demo screen 3: Before/After Policy

Before feedback:

```python
claim_policy = {
    "decision_relevance": 0.30,
    "risk_severity": 0.25,
    "evidence_strength": 0.20,
    "uncertainty_importance": 0.15,
    "novelty": 0.10,
}
```

User feedback:

```text
"More risk and uncertainty, less generic summary."
```

After feedback:

```python
claim_policy = {
    "decision_relevance": 0.27,
    "risk_severity": 0.31,
    "evidence_strength": 0.18,
    "uncertainty_importance": 0.18,
    "novelty": 0.06,
}
```

Then the final report changes.

---

## 15. What to Say in the Presentation

Long version:

> Our RL component is not used to generate text directly. It is used to optimise evidence selection. The system generates multiple candidate reports, decomposes them into atomic claims, scores each claim by decision relevance, risk severity, evidence strength, uncertainty, and novelty, and then a learned policy decides whether each claim should be included in the executive summary, main report, risk section, appendix, or discarded. The policy is updated from critic scores and human feedback, so the report becomes more aligned with the user’s decision-making preferences over time.

Short version:

> We use RL as a report optimisation layer: it learns which pieces of information are most decision-relevant and uses that to build a better final report from multiple agent outputs.

---

## 16. Difference from Normal Summarisation

Normal summarisation:

```text
Report A + Report B → LLM summary
```

Our approach:

```text
Report A + Report B
   ↓
claim extraction
   ↓
claim scoring
   ↓
RL-guided evidence selection
   ↓
final report generation
   ↓
critic + user reward
   ↓
policy update
```

This is the main technical contribution.

---

## 17. MVP Definition

The MVP is complete when we can show:

1. A user query enters the system.
2. Specialist agents produce structured evidence.
3. Two candidate reports are generated.
4. Both reports are decomposed into atomic claims.
5. Claims are scored using a policy.
6. The system selects the most important claims for the final report.
7. A final report is generated from selected evidence.
8. A critic evaluates the final report.
9. Human feedback updates the policy.
10. A regenerated report visibly changes based on updated policy.

---

## 18. Implementation Priority

Recommended build order:

```text
1. Basic OpenAI client
2. Planner module
3. 2-3 specialist agents only for MVP
4. Candidate report generator
5. Claim extractor
6. Claim scorer
7. Evidence selector
8. Final report composer
9. Critic
10. Policy update logic
11. Simple Streamlit dashboard / CLI demo
```

For the first working version, we can implement only:

```text
Planner
BudgetAgent
LandDataAgent
ClimateEnergyAgent
Executive report
Technical report
Claim extraction
Claim scoring
Final report composer
Policy update
```

Then add more agents later.
