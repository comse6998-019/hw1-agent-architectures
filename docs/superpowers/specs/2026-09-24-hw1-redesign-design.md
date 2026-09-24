# HW1 redesign: build a Bandit triage agent from scratch

Date: 2026-09-24 · Owner: Rahul Krishna · Status: approved in brainstorming, awaiting spec review

## 1. Goal

Replace the scaffolded Python starter with a specification-only handout. Teams
design and build every stage of the agent themselves. The rubric awards one
point for each stage, so the grade shows which mechanisms exist and work.

Out of scope for this change: HW2 and HW3, the course site, and the lecture
notes. They need matching edits (see §10), but this spec does not make them.

## 2. The task given to students

Build an agent that:

1. takes one pinned Python repository;
2. runs Bandit 1.9.4 at **MEDIUM or higher severity** over the scan scope that
   the config sets;
3. labels every alert **1** (potential vulnerability) or **0** (not a
   vulnerability), with a rationale and line evidence;
4. writes a `report.json` file with one row per alert, and a trace.

Teams write all of the code. The handout gives no starter code, stubs, or
tests. Any language and framework is allowed; LangGraph is suggested. Bandit
needs Python 3.12. The target code is read only. It is never installed or run.

## 3. Submission structure

One submission with two graded parts, the design report and the
implementation, due together. There is no separate design checkpoint. The
handout says that teams can consult the instructors as often as they want.

Dates stay as decided: released Friday, September 25, 2026, and due Friday,
October 16, 2026, before 2:10 p.m.

## 4. Fixed contracts

### 4.1 CLI

```
./their-agent --input <target checkout root> --output <out dir> --config config.toml
```

The agent writes `<out dir>/report.json` and `<out dir>/trace.jsonl`. The name
`their-agent` is the team's choice. The README states it.

### 4.2 Targets

Teams clone each target at its pinned commit. `--input` is the root of that
clone. The agent must run on all three targets.

| Target | Repository | Commit | Answer key (staff only) |
|---|---|---|---|
| Radicale v3.8.0 | https://github.com/Kozea/Radicale | `eff8027f3dc4910be1659ee71f4b4a454ade5a8c` | none |
| SGLang v0.5.9 | https://github.com/sgl-project/sglang | `bbe9c7eeb520b0a67e92d133dfc137a3688dc7f2` | CVE-2026-3059, -3060 and -3989, fixed in v0.5.10 |
| OWASP BenchmarkPython | https://github.com/OWASP-Benchmark/BenchmarkPython | `f1291485808b66e20ddb6b01b10dc71b3df8c8ba` | the benchmark's `expectedresults` labels |

### 4.3 Required scan scope

The handout gives this its own section, titled **Required scan scope for each
target**, and shows each `[scan]` block in full. Teams must use these values
unchanged. Graders run every submission with these blocks.

`paths` and `exclude` are globs relative to `--input`. The team's Bandit
wrapper expands them.

```toml
# Radicale — 10 alerts
[scan]
paths = ["radicale"]
exclude = ["radicale/tests"]
min_severity = "MEDIUM"
bandit_version = "1.9.4"
```

```toml
# SGLang — 20 alerts
[scan]
paths = ["python/sglang/multimodal_gen/runtime",
         "scripts/playground/replay_request_dump.py"]
exclude = []
min_severity = "MEDIUM"
bandit_version = "1.9.4"
```

```toml
# OWASP BenchmarkPython — 18 alerts (test cases 00001–00099)
[scan]
paths = ["testcode/BenchmarkTest000*.py"]
exclude = []
min_severity = "MEDIUM"
bandit_version = "1.9.4"
```

The alert counts come from Bandit 1.9.4 on CPython 3.12. They are counts of
MEDIUM+ severity results at any confidence. They were measured on the staff
scans (Radicale) and on local copies (SGLang, OWASP). Section 9 re-checks them
on fresh clones.

For reference, without these scopes the counts are 10, 198 and 297, and a
HIGH-only filter gives 2, 13 and 85. The SGLang scope was chosen because it
contains the Bandit B301 alerts at the CVE sites (for example,
`scripts/playground/replay_request_dump.py:57`). A HIGH-only filter would drop
those alerts.

### 4.4 `config.example.toml`

Staff ship this file. The team's agent must read it. It is commented and uses
the Radicale values.

```toml
[scan]
paths = ["radicale"]
exclude = ["radicale/tests"]
min_severity = "MEDIUM"      # required; do not lower
bandit_version = "1.9.4"

[model]
provider = "anthropic"       # your choice
name = "..."

[budget]
max_tokens = 200000          # whole run, across all alerts
output_allowance = 1024      # max output tokens for each model call
max_steps = 200              # failsafe, separate from the token budget
```

The budget covers the whole run, not each alert. When it runs out, every alert
that is not yet classified still gets a row, with `status: "budget_exhausted"`.

### 4.5 `report.json`

Staff ship `report.schema.json` (JSON Schema).

```json
{
  "target": {"input": "...", "commit": "..."},
  "scan":   {"bandit_version": "1.9.4", "min_severity": "MEDIUM", "alert_count": 10},
  "budget": {"max_tokens": 200000, "used_tokens": 48213, "exhausted": false},
  "alerts": [
    {
      "alert_id": "...",
      "test_id": "B602",
      "path": "radicale/storage/multifilesystem/lock.py",
      "line": 102,
      "severity": "HIGH",
      "confidence": "HIGH",
      "label": 1,
      "status": "classified",
      "rationale": "...",
      "evidence": [{"path": "...", "start_line": 95, "end_line": 110}]
    }
  ]
}
```

Rules:

- There is exactly one row for each in-scope Bandit result. Rows are never
  dropped or merged. `len(alerts) == scan.alert_count`.
- Rows are ordered by `path`, then `line`, then `test_id`.
- `status` is one of `classified`, `budget_exhausted` or `error`.
- `label` is `1` or `0` when `status` is `classified`. Otherwise it is `null`.
- `used_tokens` is the sum of the usage the provider reported.

### 4.6 Workspace and withholding

Teams build this themselves. There is no config deny list. The handout points
to cyberbird's pattern as the reference: `cyberbird/reactive/workspace.py`
(`resolve`, `AgentWorkspace` and `WITHHELD_GLOBS`) in
`github.com/comse6998-019/cyberbird`, at a pinned commit.

Requirements:

- The agent works in a disposable copy of `--input`. The tools can reach only
  that copy.
- Every tool path goes through one path check. That check refuses `..` paths,
  absolute paths, and symlinks that resolve outside the copy.
- `.git/` is withheld on every target. A full SGLang clone holds the later
  v0.5.10 fix commits in its history.
- On OWASP, the answer key (`expectedresults*.csv`) is withheld, and so is
  every `BenchmarkTest*` file except the case under investigation, because
  each case has a safe twin.

## 5. Rubric (20 points, one point per item)

### Part A: design report (7)

| # | Item |
|---|---|
| A1 | **Behaviours.** What the agent does for each alert, and what it must never do: run target code, write to the target, invent observations. |
| A2 | **State machine.** A diagram of the states and the transitions between them. |
| A3 | **Nodes and edges.** Each node, each edge marked as conditional or fixed, and who decides each transition (the model or the runtime). |
| A4 | **Agent state.** Each field with its reducer, its lifetime, who writes it, and whether the model sees it. |
| A5 | **Tools.** Contracts for at least 3 tools, with arguments, limits and refusal cases. |
| A6 | **Start, stop and termination.** A closed, mutually exclusive set of terminal statuses and what triggers each one. This includes the budget policy: what counts toward the budget, when it is checked, and what happens at the cutoff. |
| A7 | **Workspace and withholding.** Which files the agent must not see for each target and why, how they are withheld, and how they are restored. |

### Part B: implementation (10)

| # | Item |
|---|---|
| B1 | **Bandit tool.** Reads `[scan]`, uses MEDIUM+ severity, uses Bandit 1.9.4, and parses the JSON output. |
| B2 | **Workspace, read and search tools.** Meets every requirement in §4.6. |
| B3 | **Dispatcher.** The runtime validates and runs every request. Unknown tools and bad arguments come back as refusal observations, not crashes. Only the runtime writes observations. |
| B4 | **Graph.** Implemented as the design in Part A describes. |
| B5 | **Tracer.** Writes `trace.jsonl` with one event per step, each flushed immediately. Routing events record who decided. There is exactly one terminal event, even after a crash. |
| B6 | **Budget capture.** Charges the usage the provider reports, not an estimate. |
| B7 | **Budget cutoff.** Checked before each model call. Alerts that are not yet classified get `budget_exhausted`. |
| B8 | **Failsafes.** `max_steps` and a no-progress detector, each ending the run with its own terminal status. |
| B9 | **`report.json`.** Validates against `report.schema.json` with one row per alert, and is still written when the run crashes. |
| B10 | **All three targets.** Runs end to end with the staff `[scan]` blocks. |

### Part C: evidence and README (3)

| # | Item |
|---|---|
| C1 | **README.** Exact commands for one end-to-end run on each target, and one run that shows the budget cutoff. |
| C2 | **Results.** For each target, the counts of label 1, label 0 and `null`. A comparison with the OWASP labels and the SGLang CVEs (accuracy is reported, not graded). One sequence diagram built from a real trace. |
| C3 | **Limitations and alternatives.** A comparison with at least two other architectures (fixed workflow, plan-and-execute, supervisor/worker) on cost, latency, coordination and failure behaviour. Analyse them; do not build them. |

Grading notes for the handout:

- Classification accuracy is not graded.
- A missing mechanism cannot earn its point.
- Graders run B7 with a small `max_tokens`.

This rubric replaces the course site's four 5-point criteria for HW1.

## 6. Deliverables

- Source code, and a lockfile or equivalent that pins dependencies.
- `README.md` meeting C1.
- The design report (Part A plus C2 and C3), as `REPORT.md` or a PDF.
- For each target, one unedited output directory (`report.json` and
  `trace.jsonl`) and the config used. No API keys in the repository.
- A contribution statement that says who did what.

## 7. Repository changes

Delete:

- `configs/`, `data/`, `scripts/`, `src/`, `tests/`
- `pyproject.toml`, `uv.lock`, `.python-version`, `.env.example`
- `REPORT_TEMPLATE.md`, `INSTRUCTOR_REVIEW.md`

Keep or rewrite:

| File | Contents |
|---|---|
| `ASSIGNMENT.md` | The full handout: task (§2), submission structure and consultation policy (§3), targets (§4.2), the section **Required scan scope for each target** (§4.3), CLI and config (§4.1, §4.4), output (§4.5), workspace and withholding with the cyberbird pointer (§4.6), rubric (§5), deliverables (§6), dates, late days, and the AI-use policy from the current handout. |
| `config.example.toml` | §4.4, commented. |
| `report.schema.json` | JSON Schema for §4.5, including the `label` and `status` rule. |
| `README.md` | A short pointer to `ASSIGNMENT.md` and a list of the repository's files. |
| `.gitignore` | `runs/` and `targets/` only. |

The answer keys stay in `instructor-materials`. They are never committed here.

## 8. Decisions and reasons

| Decision | Reason |
|---|---|
| One submission, no design checkpoint | Simpler to run. Unlimited instructor consultation gives the feedback that a checkpoint would give. |
| Bandit only; Semgrep dropped | A smaller task. One scanner is enough to exercise every rubric item. |
| MEDIUM+ severity with staff scan scopes | About 20 alerts or fewer per target. It keeps the SGLang CVE alerts, which a HIGH-only filter drops. |
| Scope set in the config, not trimmed copies of the fixtures | No modified copies of GPL code to distribute, and every team scans the same alerts. |
| Budget per run, not per alert | A simpler contract. The cutoff shows directly as `budget_exhausted` rows. |
| Teams build withholding themselves | It is a real design problem (answer keys, safe twins, git history). cyberbird is the worked example. |

## 9. Checks before release

1. Clone each target at its pinned commit. Run Bandit 1.9.4 with each `[scan]`
   block, and confirm the counts of 10, 20 and 18. Update §4.3 if they differ.
2. Find the path of the `expectedresults` CSV in BenchmarkPython at `f1291485`,
   and name it in the handout.
3. Confirm that the cyberbird commit linked in the handout is pushed and
   contains `reactive/workspace.py` as described.
4. Validate the example in §4.5 against `report.schema.json`.
5. Confirm that the OWASP glob `testcode/BenchmarkTest000*.py` matches only
   cases 00001 to 00099.

## 10. Follow-ups outside this repository

- The course site still says "runs pinned Semgrep and Bandit" and lists four
  5-point grading criteria. Update both for HW1.
- `course_structure.md` and the Canvas syllabus have old due dates. This was
  already recorded in the old `INSTRUCTOR_REVIEW.md`, D1.
