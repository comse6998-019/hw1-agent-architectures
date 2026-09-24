# HW1 redesign: build a Bandit triage agent from scratch

Date: 2026-09-24 · Owner: Rahul Krishna · Status: approved; implemented on branch hw1-redesign

## 1. Goal

Replace the scaffolded Python starter with a specification-only handout. The hand out will be written in latex. Teams design and build every stage of the agent themselves. The rubric awards one point for each stage, so the grade shows which mechanisms exist and work.

Out of scope for this change: HW2 and HW3, the course site, and the lecture notes. They need matching edits (see §10), but this spec does not make them.

## 2. The task given to students

Build an agent that:

1. takes one pinned Python repository;
2. Conducts a vulnerability discovery stage and a simple alert triage stage;
3. Discovery is quite simple, just run a tool called Bandit (v 1.9.4) at **MEDIUM or higher severity** over the scan scope that the config sets;
4. Triaging is also quite simple: it labels every alert **1** (potential vulnerability) or **0** (not a vulnerability), with a rationale and line evidence;
5. writes a `report.json` file with one row per alert, a trace, and a rationale block.

Teams write all of the code. The handout gives no starter code, stubs, or tests. Any language and framework is allowed. Bandit needs Python 3.12. The target code is read only. It is never installed or run. They can't use agents to generate or modify the target code. LLM usage guideline is strictly enforced. LLM use is for pedagogical purposes only. The goal is to learn, folks!

## 3. Submission structure

One submission with two graded parts, the design report and the implementation, due together. There is no separate design checkpoint. The handout says that teams can consult the instructors as often as they want.

Dates stay as decided: released Friday, September 25, 2026, and due Friday, October 16, 2026, before 11:59 p.m.

## 4. Fixed contracts

### 4.1 CLI

In this version, the students will build a simple CLI based agent. The agent takes an input directory containing the target repository, an output directory for the results, and a configuration file specifying the scan parameters.

```
./their-agent --input <target checkout root> --output <out dir> --config config.toml
```

The agent writes `<out dir>/report.json` and `<out dir>/trace.jsonl`. The name `their-agent` is the team's choice. The README states it.

### 4.2 Targets

Teams clone each target at its pinned commit. `--input` is the root of that clone. The agent must run on all three targets.

| Target                | Repository                                         | Commit                                     | Role                  | Answer key                                                                |
| --------------------- | -------------------------------------------------- | ------------------------------------------ | --------------------- | ------------------------------------------------------------------------- |
| OWASP BenchmarkPython | https://github.com/OWASP-Benchmark/BenchmarkPython | `f1291485808b66e20ddb6b01b10dc71b3df8c8ba` | development           | **Open to teams:** the benchmark's own `expectedresults` labels           |
| Radicale v3.8.0       | https://github.com/Kozea/Radicale                  | `eff8027f3dc4910be1659ee71f4b4a454ade5a8c` | held out              | Hidden: staff labels, kept in `instructor-materials`                      |
| SGLang v0.5.9         | https://github.com/sgl-project/sglang              | `bbe9c7eeb520b0a67e92d133dfc137a3688dc7f2` | held out              | Hidden: CVE-2026-3059, -3060 and -3989 (fixed in v0.5.10), kept by staff |

OWASP is the development set. Teams may read its answer key themselves to
measure and refine their agent: its prompts, tools and stopping rules.
Radicale and SGLang are held out. The handout does not name their answer keys
or the SGLang CVEs, and staff score them after submission.

Teams may read the OWASP answer key, **but their agent may not**. At run time
the key is withheld from the agent's workspace (§4.6). An agent that reads it
is measuring nothing.

### 4.3 Required scan scope

The handout gives this its own section, titled **Required scan scope for each target**, and shows each `[scan]` block in full. Teams must use these values unchanged. Graders run every submission with these blocks.

`paths` and `exclude` are globs relative to `--input`. The team's Bandit wrapper expands them.

```toml
# Radicale — 10 alerts
[scan]
paths = ["radicale"]
exclude = ["radicale/tests"]
min_severity = "MEDIUM"
bandit_version = "1.9.4"
```

```toml
# SGLang — 21 alerts
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

The alert counts come from Bandit 1.9.4 on CPython 3.12. They are counts of MEDIUM+ severity results at any confidence. Section 9 check 1 confirmed them on fresh clones: Radicale and OWASP matched the informal counts, and SGLang moved from an informal 20 to 21 alerts, which is the value above and in `contract.py` (see `instructor-materials/hw1/release/RESULTS.md`).

For reference, without these scopes the counts are 10, 198 and 297, and a HIGH-only filter gives 2, 13 and 85. The SGLang scope was chosen because it contains the Bandit B301 alerts at the CVE sites (for example, `scripts/playground/replay_request_dump.py:57`). A HIGH-only filter would drop those alerts.

### 4.4 `config.example.toml`

Staff ship this file. The team's agent must read it. It is commented and uses the Radicale values.

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

The budget covers the whole run, not each alert. When it runs out, every alert that is not yet classified still gets a row, with `status: "budget_exhausted"`.

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

- There is exactly one row for each in-scope Bandit result. Rows are never dropped or merged. `len(alerts) == scan.alert_count`.
- Rows are ordered by `path`, then `line`, then `test_id`.
- `status` is one of `classified`, `budget_exhausted` or `error`.
- `label` is `1` or `0` when `status` is `classified`. Otherwise it is `null`.
- `used_tokens` is the sum of the usage the provider reported.

### 4.6 Workspace and withholding

Teams build this themselves. There is no config deny list. The handout points to cyberbird's pattern as the reference: `cyberbird/reactive/workspace.py` (`resolve`, `AgentWorkspace` and `WITHHELD_GLOBS`) in `github.com/comse6998-019/cyberbird`, at a pinned commit.

Discovery (the Bandit run) scans the whole required `[scan]` scope. The
withholding rules apply to what the model can read through the triage tools:
read, search, and any other tool the model can call.

Requirements:

- The agent works in a disposable copy of `--input`. The tools the model can call reach only that copy.
- Every tool path goes through one path check. That check refuses `..` paths, absolute paths, and symlinks that resolve outside the copy.
- `.git/` is withheld on every target. A full SGLang clone holds the later v0.5.10 fix commits in its history.
- On OWASP, the answer key (`expectedresults*.csv`) is withheld from the agent, and so is every `BenchmarkTest*` file except the case under investigation, because each case has a safe twin. Teams may still read the key themselves (§4.2); only the agent's view is restricted.

### 4.7 README contract

The team's `README.md` is read by a grading skill and by TAs. It must follow
this contract exactly, so that every submission can be graded the same way.
The handout reproduces this section in full and ships it as `README.template.md`
(headings and instructions only, no content).

#### Format rules

- The file is `README.md` at the repository root, in GitHub-flavoured Markdown.
- The level-2 headings (`##`) below appear **in this order and with exactly this
  text**. Teams may add other headings only as level-3 (`###`)
  headings, inside any required section except `## Run`, whose four `###`
  subsections are fixed.
- Every command is in a fenced code block tagged `sh`. One command per line.
  No prompts (`$`), and no output mixed into the block.
- Commands run from the repository root, on macOS or Linux, in a fresh clone.
- Commands contain no placeholders (`<...>`, `YOUR_KEY`, `...`). The only
  exception is secrets, which are read from environment variables named in
  `## Requirements`.
- No command is interactive. No command needs a secret written into a file in
  the repository.
- Paths are relative to the repository root.

#### Required sections

| # | Heading | Must contain |
|---|---|---|
| 1 | `## Team` | Each member's name and UNI. The full commit SHA of the submitted code. |
| 2 | `## Requirements` | The operating system(s) tested. Language and runtime versions. The Python 3.12 and Bandit 1.9.4 install. The model provider and exact model name. A table of every environment variable the agent reads (name and purpose, never the value). |
| 3 | `## Setup` | One `sh` block that takes a fresh clone to a ready state: dependencies installed, Bandit 1.9.4 on the path. The last line prints the Bandit version (for example `bandit --version`). |
| 4 | `## Fetch targets` | One `sh` block that clones all three targets into `targets/radicale`, `targets/sglang` and `targets/owasp-benchmark-python`, checks out the pinned commits from §4.2, and prints `git rev-parse HEAD` for each. |
| 5 | `## Configs` | A table with columns `Target`, `Config file`. One row per target, plus one row for the cutoff run. Each config file is committed. Its `[scan]` block is identical to §4.3. |
| 6 | `## Run` | Exactly four `###` subsections, in this order: `### Radicale`, `### SGLang`, `### OWASP BenchmarkPython`, `### Budget cutoff`. Each holds one `sh` block with **one** agent command in the §4.1 form, writing to `runs/radicale`, `runs/sglang`, `runs/owasp-benchmark-python` and `runs/radicale-cutoff` respectively. Under each block: the observed wall-clock time and `used_tokens`. The cutoff run uses the Radicale target with a config whose `max_tokens` is small enough that at least one row is `budget_exhausted`. |
| 7 | `## Outputs` | A table with columns `Run`, `Directory`, `alert_count`, `label_1`, `label_0`, `null`, `used_tokens`, `exhausted`. One row per run in `## Run`. The values must equal the committed `report.json` in each directory. |
| 8 | `## Validate` | One `sh` block that validates every committed `report.json` against `report.schema.json` and exits non-zero if any fails. |
| 9 | `## Trajectory` | One `sh` block with one command that renders the trajectory of one alert from `runs/radicale/trace.jsonl` as a Mermaid `sequenceDiagram` (§4.8), then the rendered diagram in a fenced block tagged `mermaid`. |
| 10 | `## Rubric map` | A table with columns `Item`, `Where`. One row for each of the 20 rubric items (A1 to C3), in rubric order. `Where` is a `path:line` or `path:start-end` into the code for Part B items, and a section heading of the report for Part A and C items. |
| 11 | `## Known issues` | Anything that does not work, failed runs, and deviations from the handout. Write `None.` if there are none. |

#### Checks the grading skill applies

Each check passes or fails. The skill reports every failure with the check id
and the line in `README.md`.

| Id | Check |
|---|---|
| R1 | All eleven `##` headings are present, in order, with the exact text. |
| R2 | `## Run` has the four `###` subsections, in order, each with exactly one `sh` block containing one command. |
| R3 | Every `sh` block follows the format rules: no placeholders, no `$` prompts, no interactive commands. |
| R4 | Each run command uses `--input`, `--output` and `--config`, with the target directory, output directory and config file named in rows 4 to 6. |
| R5 | Each config file listed in `## Configs` exists, and its `[scan]` block equals §4.3 for that target. |
| R6 | Each output directory in `## Outputs` exists and contains `report.json` and `trace.jsonl`. |
| R7 | The numbers in `## Outputs` equal the counts computed from each committed `report.json`. |
| R8 | The cutoff run's `report.json` has `budget.exhausted = true` and at least one `budget_exhausted` row. |
| R9 | `## Rubric map` has 20 rows, A1 to C3 in order. Each `path:line` exists in the repository, and each report heading exists in the report. |
| R10 | No file in the repository contains an API key (the skill scans for common key patterns). |
| R11 | Each `trace.jsonl` in the four run directories meets the invariants in §4.8. |

How the checks are used:

- **C1** is earned only if R1 to R8 all pass.
- R9 does not earn a point, but graders look for each rubric item at the place
  the map points to first. If a row is missing or wrong, the grader searches
  the submission and notes it.
- R11 does not earn a point by itself. Graders use it as evidence for B5.
- R10 failing is reported to the instructor. It is not a rubric deduction.
- The skill checks the README and the committed outputs. It does not run the
  agent. TAs may run the `## Setup`, `## Fetch targets` and `## Run` commands
  to confirm B10.

### 4.8 Trace and trajectory

The trace is the agent's trajectory: the complete, ordered record of what one
run did and who decided each step. Graders read it to check B3 to B8, so its
format is fixed. Teams build it themselves. The handout points to cyberbird's
implementation as the reference:
`cyberbird/plan_and_validation/trace.py` (`Trace`, `EventKind`,
`TerminalStatus`, `Usage`) and `cyberbird/plan_and_validation/trajectory.py`
(trace to Mermaid sequence diagram), in `github.com/comse6998-019/cyberbird`
at commit `cf7e96c8bd9e74470b99b7b754bb72392427cfc6`.

Format:

- `<out dir>/trace.jsonl`: one JSON object per line, append-only, flushed after
  every event so that a crashed run leaves the trace that explains the crash.
- Every event has `step` (an integer from 1, increasing by 1), `ts` (Unix time,
  float), `run_id`, `alert_id` (the alert the event belongs to, or `null` for
  run-level events) and `kind`.
- `kind` is one of a closed set. Other fields may be added to any event.

| `kind` | Written by | Required fields |
|---|---|---|
| `model_call` | the node that called the model | `role`, `model`, `usage` with `input` and `output` (integers, as the provider reported them; `cache_read` and `cache_write` too if the provider reports them; no summed total) |
| `tool_request` | the dispatcher | `tool`, `args` |
| `tool_result` | the dispatcher | `tool`, `ok` (boolean), and `error` when `ok` is false |
| `routing` | the edge function that chose the next node | `decision`, `by` (`model` or `runtime`) |
| `state_change` | any node, for updates not covered above | `node`; when an alert finishes, also `alert_status` and `label` as written to `report.json` |
| `terminal` | the runtime, once, last | `status` (one of the team's terminal statuses, §5 A6), `usage_total` |

Invariants (grading-skill check R11, §4.7):

1. The file parses line by line, and every event has the required fields for its `kind`.
2. `step` starts at 1 and increases by exactly 1.
3. There is exactly one `terminal` event, and it is the last line, including for a run that crashed.
4. Each counter in `usage_total` equals the sum of that counter over all `model_call` events, and the sum of `input + output` over them equals `report.json` `budget.used_tokens`.
5. For every alert in `report.json`, there is a `state_change` event whose `alert_status` and `label` equal that row's `status` and `label`.
6. Every `tool_request` is followed by exactly one `tool_result` for the same tool before the next `model_call`.

Trajectory: the team ships one command that reads a `trace.jsonl` and an
`alert_id` and prints a Mermaid `sequenceDiagram` of that alert's trajectory,
using the trace alone. The model and the runtime are separate participants.
Its output for one real run is the sequence diagram in C2.

## 5. Rubric (20 points, one point per item)

### Part A: design report (7)

| #   | Item                                                                                                                                                                                                                                   |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A1  | **Behaviours.** What the agent does for each alert, and what it must never do: run target code, write to the target, invent observations.                                                                                              |
| A2  | **State machine.** A diagram of the states and the transitions between them.                                                                                                                                                           |
| A3  | **Nodes and edges.** Each node, each edge marked as conditional or fixed, and who decides each transition (the model or the runtime).                                                                                                  |
| A4  | **Agent state.** Each field with its reducer, its lifetime, who writes it, and whether the model sees it.                                                                                                                              |
| A5  | **Tools.** Contracts for at least 3 tools, with arguments, limits and refusal cases.                                                                                                                                                   |
| A6  | **Start, stop and termination.** A closed, mutually exclusive set of terminal statuses and what triggers each one. This includes the budget policy: what counts toward the budget, when it is checked, and what happens at the cutoff. |
| A7  | **Workspace and withholding.** Which files the agent must not see for each target and why, how they are withheld, and how they are restored.                                                                                           |

### Part B: implementation (10)

| #   | Item                                                                                                                                                                                |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B1  | **Bandit tool.** Reads `[scan]`, uses MEDIUM+ severity, uses Bandit 1.9.4, and parses the JSON output.                                                                              |
| B2  | **Workspace, read and search tools.** Meets every requirement in §4.6.                                                                                                              |
| B3  | **Dispatcher.** The runtime validates and runs every request. Unknown tools and bad arguments come back as refusal observations, not crashes. Only the runtime writes observations. |
| B4  | **Graph.** Implemented as the design in Part A describes.                                                                                                                           |
| B5  | **Tracer and trajectory.** Writes `trace.jsonl` in the §4.8 format with every invariant holding (R11): one event per step, flushed immediately, routing events that record who decided, and exactly one terminal event, even after a crash. Ships the trajectory command of §4.8. |
| B6  | **Budget capture.** Charges the usage the provider reports, not an estimate.                                                                                                        |
| B7  | **Budget cutoff.** Checked before each model call. Alerts that are not yet classified get `budget_exhausted`.                                                                       |
| B8  | **Failsafes.** `max_steps` and a no-progress detector, each ending the run with its own terminal status.                                                                            |
| B9  | **`report.json`.** Validates against `report.schema.json` with one row per alert, and is still written when the run crashes.                                                        |
| B10 | **All three targets.** Runs end to end with the staff `[scan]` blocks.                                                                                                              |

### Part C: evidence and README (3)

| #   | Item                                                                                                                                                                                                                              |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C1  | **README.** Follows the README contract in §4.7: checks R1 to R8 pass. This covers an end-to-end run on each target and one run that shows the budget cutoff.                                                                    |
| C2  | **Results.** For each target, the counts of label 1, label 0 and `null`. On OWASP, precision and recall against the benchmark labels, and how the team used them to refine the agent (accuracy is reported, not graded). One sequence diagram of one alert's trajectory, produced by the §4.8 trajectory command from a committed trace. |
| C3  | **Limitations and alternatives.** A comparison with at least two other architectures (fixed workflow, plan-and-execute, supervisor/worker) on cost, latency, coordination and failure behaviour. Analyse them; do not build them. |

Grading notes for the handout:

- Classification accuracy is not graded.
- A missing mechanism cannot earn its point.
- Graders run B7 with a small `max_tokens`.

This rubric replaces the course site's four 5-point criteria for HW1.

## 6. Deliverables

- Source code, and a lockfile or equivalent that pins dependencies.
- `README.md` following the README contract in §4.7.
- The four run directories named in the README (`runs/radicale`, `runs/sglang`,
  `runs/owasp-benchmark-python`, `runs/radicale-cutoff`) and their configs.
- The design report (Part A plus C2 and C3), as `REPORT.md` or a PDF.
- For each target, one unedited output directory (`report.json` and `trace.jsonl`) and the config used. No API keys in the repository.
- A contribution statement that says who did what.

## 7. Repository changes

Delete:

- `configs/`, `data/`, `scripts/`, `src/`, `tests/`
- `pyproject.toml`, `uv.lock`, `.python-version`, `.env.example`
- `ASSIGNMENT.md`, `REPORT_TEMPLATE.md`, `INSTRUCTOR_REVIEW.md`

Keep or rewrite:

| File                  | Contents                                                                                                                                                                                                                                                                                                                                                               |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `briefs/hw1.tex` (and the built `briefs/hw1.pdf`) | The full handout, in LaTeX. Letter paper, `\usepackage[margins=tight]{savetrees}` for maximum text width. Contents: task (§2), submission structure and consultation policy (§3), targets (§4.2), the section **Required scan scope for each target** (§4.3), CLI and config (§4.1, §4.4), output (§4.5), workspace and withholding with the cyberbird pointer (§4.6), rubric (§5), deliverables (§6), dates, late days, and the AI-use policy from the current handout, the trace and trajectory contract with the cyberbird pointer (§4.8), and the full README contract (§4.7). |
| `config.example.toml` | §4.4, commented.                                                                                                                                                                                                                                                                                                                                                       |
| `report.schema.json`  | JSON Schema for §4.5, including the `label` and `status` rule.                                                                                                                                                                                                                                                                                                         |
| `README.template.md`  | The §4.7 headings in order, each with its instructions as an HTML comment and no content. |
| `README.md`           | A short pointer to `briefs/hw1.pdf` and a list of the repository's files.                                                                                                                                                                                                                                                                                               |
| `.gitignore`          | `runs/` and `targets/` only.                                                                                                                                                                                                                                                                                                                                           |

Writing: the handout's prose is drafted and revised with the `orwell:academic`
skill. Claims about the targets, alert counts and tools must stay within what
§4 and §9 establish.

The Radicale and SGLang answer keys stay in `instructor-materials`. They are
never committed here. The OWASP key is the benchmark's own file in the upstream
repository; this repository does not copy it.

## 8. Decisions and reasons

| Decision                                                    | Reason                                                                                               |
| ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| One submission, no design checkpoint                        | Simpler to run. Unlimited instructor consultation gives the feedback that a checkpoint would give.   |
| Bandit only; Semgrep dropped                                | A smaller task. One scanner is enough to exercise every rubric item.                                 |
| MEDIUM+ severity with staff scan scopes                     | About 20 alerts per target (10, 21 and 18). It keeps the SGLang CVE alerts, which a HIGH-only filter drops. |
| Scope set in the config, not trimmed copies of the fixtures | No modified copies of GPL code to distribute, and every team scans the same alerts.                  |
| Budget per run, not per alert                               | A simpler contract. The cutoff shows directly as `budget_exhausted` rows.                            |
| OWASP is open for development; Radicale and SGLang are held out | Teams get a labelled set to measure against while building. The held-out targets show whether the agent generalises or has only been tuned to the benchmark. |
| Teams build withholding themselves                          | It is a real design problem (answer keys, safe twins, git history). cyberbird is the worked example. |

## 9. Checks before release

1. Clone each target at its pinned commit. Run Bandit 1.9.4 with each `[scan]` block, and confirm the counts of 10, 21 and 18. Update §4.3 if they differ.
2. Find the path of the `expectedresults` CSV in BenchmarkPython at `f1291485`, and name it in the handout.
3. Confirm that the cyberbird commit linked in the handout is pushed and contains `reactive/workspace.py` as described.
4. Validate the example in §4.5 against `report.schema.json`.
5. Confirm that the OWASP glob `testcode/BenchmarkTest000*.py` matches only cases 00001 to 00099.
6. Staff label the 10 Radicale alerts (1 or 0, with a rationale) and store the labels in `instructor-materials`.
7. `briefs/hw1.tex` builds to PDF without errors, and the PDF is committed.

## 10. Follow-ups outside this repository

- The course site still says "runs pinned Semgrep and Bandit" and lists four 5-point grading criteria. Update both for HW1.
- `course_structure.md` and the Canvas syllabus have old due dates. This was already recorded in the old `INSTRUCTOR_REVIEW.md`, D1.
