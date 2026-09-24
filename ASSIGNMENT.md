# HW1: Bounded Agent Execution for Security-Alert Triage

COMS E6998 Section 019, Fall 2026 · Design of Production Agentic Systems
Instructor: Rahul Krishna · TA: In Keun Kim

> **Internal draft.** Unresolved policies are tracked in `INSTRUCTOR_REVIEW.md`.

| | |
|---|---|
| Released | Friday, September 25, 2026 |
| Due | Friday, October 16, 2026, before 2:10 p.m. |
| Weight | 20% of the course grade, marked out of 20 |
| Teams | Team assignment |
| Late days | 6 per student per semester, at most 3 on one assignment; each extends the deadline by 24 hours |

## 1. What you build

From the course site: "Build a bounded triage application over a pinned
repository: an intake stage that runs pinned Semgrep and Bandit and normalizes
both outputs into one alert contract, a planner, a sequential reactive
investigation loop with local search/read tools, structured TP/FP/Other
findings with evidence references, and a report across the selected alerts. Add
a configurable per-investigation token budget: pre-call admission with an output
allowance, post-call reconciliation of reported usage, and an explicit
exhaustion outcome." "The lecture demo (V0–V4) is published as scaffolding; the
intake contract, budget policy, exhaustion outcome, and evidence resolution must
be your own."

Scope:

- One sequential investigation handles one alert and has its own budget.
- Do not make concurrent model or tool calls.

### Target

Read [Radicale v3.8.0](https://github.com/Kozea/Radicale) at commit
`eff8027f3dc4910be1659ee71f4b4a454ade5a8c`. Do not install or execute it or run
its tests. Treat scanner alerts as claims, not confirmed vulnerabilities.

## 2. What you implement

Implement the six parts below. Keep every supplied entry-point name and
signature; the acceptance tests and grader call them. Justify the policy choices
left open in your report.

### Part 1. Read-only tools (`application/tools.py`)

`TOOL_SPECS` are fixed; implement `search_repo` and `read_file` without changing
their schemas.

`search_repo(root, pattern, path_glob=None, max_results=50) -> ToolResult`
searches text files under `root` for a Python regular expression.

- Every regular file under `root` in the working tree is searched, tracked or not; `.git/`, binary files, and symlinks that resolve outside `root` are skipped.
- `path_glob`, when set, filters repository-relative POSIX paths.
- Each match is one line, `relative/path.py:LINE: text`, ordered by path, then line.
- Return at most `min(max_results, MAX_SEARCH_RESULTS)` matches (50); if more exist, say so in `content`.
- An invalid regular expression returns `ok=False` with the compile error.

`read_file(root, path, start_line, end_line) -> ToolResult` returns lines
`start_line` to `end_line`, 1-based and inclusive.

- `path` is repository-relative. Refuse absolute paths, any path that resolves outside `root` (through `..` or a symlink), and directories.
- Refuse `start_line < 1`, `end_line < start_line`, and a requested range (`end_line - start_line + 1`) longer than `MAX_READ_LINES` (200), checked before clipping.
- Clip a request within the limit that runs past the end of the file.
- Prefix each line with its number and `|`, for example `  42| text`.

Both functions return `ToolResult(ok=False, error=...)`, not exceptions, for
invalid requests or missing files. Refusals must not disclose contents from
outside `root`. `root` is supplied by the runtime and absent from the model
schemas. Expose no shell, code-execution, or write tool.

### Part 2. Intake (`domain/alert.py`, `application/intake.py`)

`Alert` is your pydantic intake contract (the CLI stores it with
`model_dump_json`). It must:

- expose the attributes in `triage.domain.model.AlertView`: `alert_id`, `scanner`, `rule_id`, `commit`, `path`, `start_line`, `end_line`;
- record scanner provenance (scanner, version, command, ruleset hashes);
- separate scanner claims (rule, message, severity, location) from facts your code establishes. Normalizers may record only facts derivable from the raw JSON, snapshot, and provenance; checkout-dependent facts belong to investigation or evidence resolution;
- give the same claim and commit the same `alert_id` regardless of raw-result order, give distinct claims distinct ids, and restrict ids to `[A-Za-z0-9._-]+` (the CLI uses them as file names).

`normalize_bandit(raw, snapshot, scanner)` and
`normalize_semgrep(raw, snapshot, scanner)` return exactly one alert per raw
result, in deterministic order. Do not filter or de-duplicate during
normalization; do that in `plan()`. Every selector in `data/selected_alerts.json`
must resolve to exactly one normalized alert.

### Part 3. Token budget (`domain/budget.py`)

`TokenBudget(budget_tokens, output_allowance)` owns one investigation's
`ledger`. The interface is fixed; the policy is yours.

- `remaining`: `budget_tokens` minus all charges.
- `admit(call_index, input_estimate) -> Admission`: decide affordability without charging.
- `reconcile(admission, usage: Usage | None) -> LedgerEntry`: charge one completed admitted call, append it, and return it; raise `ValueError` for a refused admission.

Requirements:

- Admit a call only if its input estimate plus the output allowance fits what remains.
- A refused call never reaches the provider and charges nothing.
- The output allowance is sent as `max_output_tokens` on every admitted call.
- Reconciliation charges the usage the provider reported, not the estimate.
- Missing usage is not zero.
- No automatic retries: each call that reaches the provider is one ledger entry.

Decide and justify in your report:

| Item | Requirement or decision |
|---|---|
| Charge | Charge reported `Usage.input_tokens + Usage.output_tokens`. `input_tokens` already includes cache use; the interface exposes no separate reasoning-token field. |
| Input estimate | Pass the complete request (messages, including the system prompt and observations, and tools) to `provider.count_input_tokens`. Use a `bound` count unchanged; apply any safety margin only to an `estimate`. |
| Missing usage | Choose and justify a positive fallback charge, and whether the run continues. |
| Overshoot | State what happens when reported usage exceeds the estimate or the budget, and how it is recorded. |
| Invariant | State what admission guarantees for `bound` and for `estimate` counts. |

`ScriptedProvider` labels its fixture counts `bound`; `LangChainProvider`
labels live counts `estimate`. OpenAI estimates omit tool schemas, and Ollama
uses characters / 4. Only a true input bound plus a provider-enforced output cap
supports a hard-bound claim. State which kind each experiment tested.

### Part 4. Evidence resolution (`application/evidence.py`)

`resolve_evidence(finding, repo_root, commit) -> list[str]` returns the reasons a
finding's evidence does not resolve; `[]` means it resolves.

- Every reference must use the pinned commit, a repository-relative regular file inside the checkout, and a line range that exists at that commit; symlinks and paths resolving outside the checkout fail.
- Put optional run-history checks, such as requiring that the agent read the cited lines, in `investigate()`; `resolve_evidence` receives only the finding, checkout, and commit.
- Do not call the staff `triage.infrastructure.target.check_location`.

`Finding` requires a `TP`, `FP`, or `Other` verdict, a nonempty rationale and
uncertainty (what static inspection did not establish), and at least one
evidence reference containing commit, relative path, ordered line range, and
note. `budget_exhausted` is a terminal reason, never a verdict.

### Part 5. Investigation loop (`application/agent.py`)

`investigate(alert, repo_root, config, provider, trace) -> InvestigationResult`
handles one alert. Reach the model only through `provider`, emit events only
through `trace` (both ports are in `application/ports.py`), and set
`InvestigationResult.run_id = trace.run_id`.

- The model chooses one action at a time: a read-only tool call or `submit_finding`.
- Do not add planner or validator model calls inside `investigate()`: scripted step i must answer controller call i.
- The runtime validates and executes each request and adds its observation to the state sent on the next model call. The model never writes observations.
- Before every model call, including the first call of a zero-budget run, estimate the input (`provider.count_input_tokens`), ask your `TokenBudget`, and emit `ModelCallRequested`, then `ModelCallAdmitted` or `ModelCallRejected`.
- On rejection, do not invoke the provider or make a closing model call. Return `finding=None`, `terminal_reason="budget_exhausted"`, and any partial outcome in added `InvestigationResult` fields.
- After every admitted call, reconcile the usage and emit `ModelCallCompleted`.
- Set `Finding.alert_id` from `alert.alert_id` and stamp `alert.commit` on every evidence reference; the model supplies neither. Accept the finding only when `resolve_evidence(...) == []` and any run-history check passes.
- `max_model_calls` is a failsafe and must end the run with a reason other than `budget_exhausted`. Names for other terminal reasons are yours.

State and events:

- Define your run state explicitly; `RunState` is a starting point.
- Emit the events in `domain/events.py`: `RunStarted`, `ModelCallRequested`, `ModelCallAdmitted`, `ModelCallRejected`, `ModelCallCompleted`, `ToolCallCompleted`, `FindingSubmitted`, `RunTerminated`. `RunStarted` comes first and `RunTerminated` last, exactly once each.
- `search_repo`, `read_file`, and every unknown tool request each emit exactly one `ToolCallCompleted`, including refusals. A `submit_finding` whose arguments form a `Finding` emits `FindingSubmitted`, not `ToolCallCompleted`; if its arguments cannot form a `Finding`, emit a failed `ToolCallCompleted(tool="submit_finding")` and return the error as an observation.
- The event set is closed: `read_trace` rejects other types. Put extra data in `InvestigationResult` fields or `RunTerminated.detail`.

LangGraph is supported but optional; grading is behavior-based.

### Part 6. Planner and report (`application/pipeline.py`)

- `plan(alerts, config)` returns a duplicate-free proper subset of the input alerts; for the provided target it contains 3 to 5 alerts. Its order is deterministic and fixed at design time. It makes no model call (it receives no provider). Explain the selection rules in your report; filter or de-duplicate here, not during intake.
- `write_report(results, alerts, path)` writes one human-readable report across the investigated alerts, with verdicts and terminal reasons in separate columns.

## 3. Experiments

1. **Normal (live).** Run `scripts/scan_target.sh`, then `scripts/run_normal.sh`. The scan uses Bandit 1.9.4 and Semgrep 1.176.0 with sha256-checked rulesets. The run uses the fresh scans, your intake and planner, one budget per sequential investigation, and your cross-alert report.
2. **Scripted exhaustion (synthetic).** Run `scripts/run_exhaustion.sh`. It investigates `bandit-B602-lock` under three conditions with the same fixture, `data/provider_scripts/radicale-exhaustion.json`. Only the model is replaced.

| Condition | Budget | Expected |
|---|---|---|
| exhaustion | 100 | Call 1 admitted (20 + 20), charged 30. Call 2 admitted (25 + 20), charged 40. Call 3 needs 15 + 20 = 35 with 30 left: refused before the provider. Two calls in the boundary log. `budget_exhausted`. |
| control | 1000 | The same script, so call 3 is admitted. This shows the stop came from the budget, not from a fixed call count. |
| zero-budget | 0 | The first call is requested and refused before the provider. Zero calls in the boundary log. `budget_exhausted`. |

Each investigation directory contains `trace.jsonl` (your events),
`boundary.jsonl` (written independently by the staff recorder), `result.json`,
`config.json`, `alert.json`, and `meta.json`.
`uv run triage summarize PATH_TO_RUN_DIR` reconciles `trace.jsonl` with
`boundary.jsonl` and reads the measurement label from `meta.json`.

Label reported results `live` or `synthetic`; scripted counts are fixtures, not
measurements. Do not edit logs or invent data; report failed runs.

## 4. Deliverables

- [ ] Code and `uv.lock`; `uv run pytest` passes with no xfails.
- [ ] The config files for each experiment; no API keys in the repository.
- [ ] The raw scanner JSON used and the normalized alerts from `triage intake`.
- [ ] Unedited run directories for the normal run and all three scripted conditions.
- [ ] `REPORT.md` or PDF, at most two pages excluding the contribution statement, based on `REPORT_TEMPLATE.md`, with one main results table or figure.
- [ ] Exact commands that reproduce every reported result.
- [ ] A contribution statement naming who did what.

## 5. Out of scope

Target modification, patches or exploits, parallel or multi-agent execution,
MCP/CLDK, deployment or checkpointing, benchmark campaigns, and UIs.

## 6. Grading

Each homework is marked out of 20 on four criteria worth 5 points each:

| Criterion | Points |
|---|---|
| Systems design and claim | 5 |
| Experimental design | 5 |
| Evidence and reproducibility | 5 |
| Interpretation and limitations | 5 |

A sound experiment can earn full credit without an improvement or a confirmed
hypothesis; a missing required mechanism cannot. Verdict accuracy is not graded;
an evidence-backed `Other` is valid.

## 7. Report questions

1. What is the agent graph, who selects each transition, and which decisions are fixed at design time versus deferred to the model?
2. What is the runtime state, who writes and sees each field, and what is sent on every model call?
3. How does intake separate scanner claims from established facts, and where are checkout-dependent facts established?
4. What are the tools' contracts, limits, refusal cases, and observation path?
5. What is the budget policy and its invariant? Show the two charged ledger entries before exhaustion and the decisive `ModelCallRejected` values.
6. What does the exhaustion outcome contain, and why?
7. What evidence supports each finding, how was it resolved, and what remains uncertain?
8. Why did you choose this architecture? Compare it with at least two of a fixed workflow, plan-and-execute, a parallel design, and a supervisor/worker design on cost, latency, coordination, and failure behavior; analyze them, do not build them.

## 8. Academic integrity and AI tools

AI assistants may be used to learn, debug your own code, review a design, or
provide scoped autocomplete. Do not hand the assignment to an agent and submit
the result. You remain responsible for every line you submit. Every team member
must be able to explain the entire submission; the individual exams test this.
