# HW1 Report: <team name>

Two pages maximum, excluding the contribution statement. One main results
table or figure. Every number cites the run directory it came from and is
labelled **live** or **synthetic**.

Team: <names, UNIs> · Code commit: `<sha>` · Target: `radicale@eff8027f3dc4`

## 1. Claim (3 to 5 sentences)

State what your runtime guarantees and under which assumptions. Example:
"Our runtime never issues a model call unless charged-so-far + input estimate +
output allowance fits the budget. With declared input bounds and a
provider-enforced output cap, this is a hard ceiling. With live-provider
estimates, it is an admission policy whose error we measured as ...".

## 2. Architecture and state

- A diagram of your graph: nodes, edges, and who chooses each transition (model or runtime).
- Your run state: each field, who writes it, and whether the model sees it.
- Tool contracts: arguments, limits, refusal cases, and how a refusal reaches the model.
- Pipeline: your intake contract and how it separates scanner claims from facts you established (and where facts that need the checkout come from); what your planner decides; which decisions are fixed at design time and which are deferred to the model.
- Evidence resolution: what your resolve_evidence requires before a finding is accepted.

## 3. Budget mechanism

- Where admission happens relative to the provider call (cite file and line).
- Your budget policy: what counts, how input is estimated, the output allowance and how it reaches the provider, and your invariant.
- How reported usage is reconciled, how missing usage is handled, and what happens on overshoot.
- Your terminal reasons and how each is triggered (a budget refusal is `budget_exhausted`). Keep them separate from verdicts.
- Your exhaustion outcome: what an exhausted run returns, and why.

## 4. Experimental design

- Inputs: target commit, alerts (ids), config files, model and provider (live), script (synthetic).
- Conditions: the normal run over the alert set; exhaustion, control, and zero-budget on one investigation.
- What you measured and from which file: trace, boundary log, result.
- Controls and confounders: why the control run rules out a fixed call count; what live-model variability means for the normal run.

## 5. Results

**Main results table or figure** (required). If you use the table, fill it in; add rows and keep the columns:

| Run (dir) | Live or synthetic | Alert | Budget / allowance | Calls requested | Admitted | Rejected | Issued (boundary) | Tokens charged | Terminal reason | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| normal: ... | live | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| exhaustion | synthetic | ... | 100 / 20 | ... | ... | ... | ... | ... | ... | ... |
| control | synthetic | ... | 1000 / 20 | ... | ... | ... | ... | ... | ... | ... |
| zero-budget | synthetic | ... | 0 / 20 | ... | ... | ... | ... | ... | ... | ... |

For the exhaustion run, show the two charged ledger entries before the
refusal and the decisive `ModelCallRejected` values (`required`, `remaining`).
For the live run, show the input estimate versus reported input for each call.

For each live finding: verdict, evidence references, and what remains uncertain.

## 6. Interpretation and limitations

- What the model chose versus what the runtime enforced, with one example from a trace.
- Whether the scripted test establishes a hard bound, and why the live run does not.
- What this small experiment does not establish (e.g. verdict quality, behavior on other targets, cost at scale).
- Any hypothesis that failed, and what you learned from it.

## 7. Alternative architectures (analysis only)

Compare your design with at least two of: a fixed workflow, plan-and-execute,
parallel investigation of alerts, a hierarchical supervisor/worker design.
Discuss cost, latency, coordination, and failure behavior for this task.

## 8. Reproduction

Exact commands, in order, from a fresh clone to every number in §5.

## Contribution statement (outside the page limit)

Who did what.
