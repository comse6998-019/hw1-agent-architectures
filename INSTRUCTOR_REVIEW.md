# HW1 Instructor Review

Prepared by the TA for Rahul Krishna, 2026-09-22. **Remove this file from the
student template before release.** It contains no triage answers.

## 1. Summary

The baseline is the course site at commit `88d2941` (2026-09-22 20:30 UTC). It
was re-checked before this revision and has not changed. The handout quotes
the site's HW1 text, and the starter follows it.

The site says "the intake contract, budget policy, exhaustion outcome, and
evidence resolution must be your own." Each of those is a `TODO(student)` in
its own file. So are the planner, the tools, the loop, and the report. Staff
code fixes only the names that the scripted experiment and the grader read.

Decided so far:

- **D1:** out Friday Sep 25, due Friday Oct 16 before class (three weeks).
- **D6:** both Bandit and Semgrep, pinned.

The proposed target is Radicale v3.8.0. The open questions are in §7.

## 2. Sources inspected

| Source | Revision used | Notes |
|---|---|---|
| Course site, live (https://comse6998-019.github.io/) | identical to repo `88d2941` when re-checked | Baseline |
| `comse6998-019/comse6998-019.github.io` | `88d29415934cf015ccc91a4b7b5ec85dcb5c3207` (HW1 text last changed in `7db61cee`, 2026-09-22 20:20 UTC) | Baseline |
| `comse6998-019/demos` | `e06d58f25de3dd8485050edc4fa859c664deea3e` | `lec2_reactive_agent`, `lec2_planning_and_validation_agent`, `intake/` |
| `comse6998-019/lectures` | `4b8eb654d4513aaa7cdc97102329156ec25f4f52` | Lecture 1 and 2 slides, lecture 2 notes |
| `comse6998-019/.github` (org profile) | `998a3ebf03532132474555ebe755a69287494793` | Stale dates (see D1) |
| `comse6998-019/instructor-materials` (private) | `a4b867f1b5d37a843e8f395b6e9baa9d0f5c9231` | `course_structure.md`, `canvas_syllabus.html` |
| Meeting notes, 2026-09-22 (TA and instructor) | n/a | |
| Radicale, sqlite-utils, pypiserver, httpbin, vulpy | see §5 | Candidate targets |

No existing HW1 brief, template, or rubric file exists in these repositories.

## 3. How the package maps to the site's HW1 text

| Site text | Staff provide | Students build (`TODO(student)`) |
|---|---|---|
| "an intake stage that runs pinned Semgrep and Bandit" | Pinned versions, `scripts/scan_target.sh`, reference scans, ruleset sha256 checks | Running it before the normal run |
| "normalizes both outputs into one alert contract"; the intake contract "must be your own" | Only the attributes the grader reads (`AlertView`), and five scanner results named in scanner terms (`data/selected_alerts.json`) | `alert.Alert`, `normalize_bandit`, `normalize_semgrep` |
| "a planner" | none | `pipeline.plan` |
| "a sequential reactive investigation loop with local search/read tools" | Tool schemas, trace event shapes, `RunState` starting point | `agent.investigate`, `tools.search_repo`, `tools.read_file` |
| "structured TP/FP/Other findings with evidence references"; "evidence resolution must be your own" | Finding and evidence shapes | `evidence.resolve_evidence` |
| "a report across the selected alerts" | none | `pipeline.write_report` |
| "per-investigation token budget: pre-call admission with an output allowance, post-call reconciliation"; "budget policy ... must be your own" | `TokenBudget` interface, model boundary that carries `max_output_tokens`, usage shape | The policy inside `TokenBudget` |
| "an explicit exhaustion outcome"; it "must be your own" | The single fixed reason `budget_exhausted` | What an exhausted run returns |
| "one normal run over a small alert set and one scripted exhaustion run on a single investigation" | `run_normal.sh`, `run_exhaustion.sh`, scripted provider, boundary recorder, `summarize` | The runs and the report |
| "The lecture demo (V0–V4) is published as scaffolding" | The handout points to it | Optional reuse |

## 4. Decisions and disagreements

| # | Topic | Status | Detail | Needs |
|---|---|---|---|---|
| D1 | Dates | **Resolved** | Out Fri Sep 25, due Fri Oct 16 before class, three weeks, as on the site. | Stale elsewhere: the org profile says due Oct 9; `course_structure.md` and the Canvas syllabus say due Oct 2 with a late window to Oct 9. Update them. |
| D2 | Scope | Follows site | A small, sequential alert set with one budget per investigation. The meeting's "one selected alert per run" holds per investigation. No batch machinery beyond one loop in `run-set`. | Confirm the set size (3 to 5 proposed) and that there is no set-level budget. |
| D3 | Intake contract | Follows site | Student-owned. Staff fix only the `AlertView` attributes and name fixtures in scanner terms. The meeting notes had staff define the schema; the site overrides that. | `demos/intake` is a complete public normalizer, and the site calls the demo scaffolding. May students reuse it? |
| D4 | Planner | Decided (TA) | The site requires "a planner" but does not define it. The planner selects and orders alerts without a model: `plan()` receives no provider, so a model call could be neither budgeted nor recorded. | Object if you want a model-calling planner; it would need a provider, a trace, and a scripted test. |
| D5 | Target | Open | Radicale v3.8.0 (§5). `course_structure.md`, the Canvas syllabus, the demos, and the lecture notes use OWASP BenchmarkPython; the meeting preferred small real applications. | Approve, and choose a new grading alert A1. |
| D6 | Scanners | **Resolved** | Both, pinned: Bandit 1.9.4 and Semgrep 1.176.0 with the demo's two rulesets. | none |
| D7 | Report content | Follows site | Design-time versus model-deferred decisions, the state model, the architecture adopted and why. The meeting's architecture comparison is the "why" (ASSIGNMENT §7, question 8). | Confirm it fits in two pages. |
| D8 | Terminal statuses | Follows site | Student-owned vocabulary; only `budget_exhausted` is fixed. The lectures disagree with each other: lecture 2 uses five statuses, lectures 1 and 3 use `ok` and `error`. | Align the lectures. |
| D9 | Demo budget | Note | The demo stops after 40 model calls, not on tokens. The handout says a call count is not the budget, and the control condition tells them apart. | Consider a note in the demo README. |
| D10 | Usage counters | Note | Demo code says `cache_write`; lecture text says `cache_create`. Students decide what counts. | Minor. |
| D11 | Fan-out wording | Note | Lecture 2 notes call "forty alerts fan out" part of HW1. HW1 is sequential. | Reword the notes. |
| D12 | Semgrep rulesets | Open | The demo vendors `p/python` and `p/owasp-top-ten` under the Semgrep Rules License v1.0. The scan script downloads them from `demos@e06d58f` and checks their sha256; they are not copied here. | Check that the license allows course use. |
| D13 | Grading detail | Open | The handout publishes only the site's four criteria. `course_structure.md` has a finer point breakdown. | Publish it or not? |
| D14 | Grader interface | Open | `course_structure.md` says students need not match instructor function names. The starter fixes entry-point names and the `AlertView` attributes so the acceptance tests and scripted experiment can run. | Accept, or make the acceptance tests advisory. |
| D15 | Late days for teams | Open | The site gives late days per student; homework is team work. | How they combine. |
| D16 | Budget requirements beyond the site | Open | The site says the budget policy is the students' own. The handout lists as course requirements two rules that come from `course_structure.md`, not the site: "missing usage is not zero" and "no automatic retries". My earlier proposed defaults (what counts, the charge for missing usage, overshoot handling) are now questions students must answer. | Confirm these two rules. |

## 5. Target selection

Bandit 1.9.4 ran on CPython 3.12.12 over application code only, with tests
excluded. Two runs of each target gave identical output once the timestamp was
removed. Semgrep 1.176.0 used the demo rulesets. No target code was installed
or executed.

| Candidate | Pinned commit (tag) | License | App size | Bandit (app code) | Semgrep | Assessment |
|---|---|---|---|---|---|---|
| **Radicale** (primary) | `eff8027f3dc4910be1659ee71f4b4a454ade5a8c` (v3.8.0, 2026-09-03) | GPL-3.0 | 75 files, 18,556 lines. Alerted files are 71 to 349 lines. | 77 alerts from 13 rules: B101 ×42, B405 ×8, B301 ×7, B403 ×5, B105 ×4, B311/B112/B107 ×2, B113/B324/B110/B404/B602 ×1. 0 errors. | 16 (14 are `python-logger-credential-disclosure`) | A real network server, so "who controls this input" has an answer. Varied rules. Many alerts need reading beyond the flagged line. |
| **sqlite-utils** (backup) | `28dc6278cc03a9245325d056e6986818544abc68` (4.2.1, 2026-08-13) | Apache-2.0 | 10 files, 11,248 lines | 52 alerts: B608 ×32, B101 ×10, B102 ×5, B324 ×3, B307 ×1, B110 ×1 | 3 (helper scan, `p/python` only) | Permissive license and clear data-flow puzzles. But it is dominated by B608, and as a library and CLI its threat model is ambiguous. |
| pypiserver | `c8e2c6b6` (v2.4.2) | zlib/libpng + MIT | 10 files, 2,839 lines (plus vendored bottle.py) | 11 (4 are B101) | 0 | Too few alerts. |
| httpbin (postmanlabs) | `f8ec666b` (HEAD, 2018) | ISC | 6 files, 2,435 lines | 15 from 5 rules | 5 | Unmaintained. |
| vulpy | `5249cc8b` (HEAD, 2020) | MIT | 18 files, 772 lines (`bad/`) | 22 | 8 | Deliberately vulnerable, so it is not a real application. |

Re-verified in this session: every Radicale figure, and the sqlite-utils
commit, Bandit counts, and file and line totals. The other figures come from a
scan run in this session by a helper agent and were not re-checked.

Radicale caveats:

- B101 (assert) is 42 of the 77 alerts. Students should expect to filter it in the planner (intake returns one alert per raw result).
- 13 alerts (B403 ×5 and B405 ×8) flag an import rather than a use.
- GPL-3.0 is fine for cloning and reading. Students fetch it from upstream.

`data/selected_alerts.json` names five scanner results, chosen for rule
variety only:

- Bandit B602 `lock.py:102` (the scripted-experiment alert)
- Bandit B301 `sync.py:79`
- Bandit B113 `oauth2.py:60`
- Bandit B405 `xmlutils.py:27`
- Semgrep logger-credential `auth/__init__.py:315`

No normalized alerts ship, because the contract is the students'. No verdicts
or rationales were written anywhere. Keep the grading alert A1 in
`instructor-materials`.

## 6. Staff design choices awaiting approval

1. **The fixed `AlertView` attributes:** `alert_id`, `scanner`, `rule_id`, `commit`, `path`, `start_line`, `end_line`.
2. **Fixtures named in scanner terms** (scanner, rule, path, line), matched to each team's alerts by `select_alert`.
3. **`budget_exhausted`** is the only fixed terminal reason.
4. **Tools are student-owned,** including path and symlink confinement. The acceptance tests cover escapes.
5. **Findings** need at least one evidence reference, and are accepted only when `resolve_evidence` returns no problems.
6. **Scripted exhaustion** reuses the course grading table (budget 100, allowance 20, charges 30 and 40, refusal at 35 > 30). It adds a control run at 1000 and a zero-budget run.
7. **Boundary recorder.** A staff wrapper writes `boundary.jsonl` independently of the student trace, and `triage summarize` compares the two.
8. **Live adapter:** LangChain `init_chat_model("<provider>:<model>", max_retries=0)`. No provider is fixed. Checked offline, the output cap becomes `max_tokens` for Anthropic, `max_completion_tokens` for OpenAI, and the `num_predict` option for Ollama.
9. **Acceptance tests check course requirements only.** A test stopped by a `StudentTODO` stub is reported as xfail; every other failure is real.
10. **Package name** `triage`, so that the same codebase can grow through HW2 and HW3.

## 7. Questions for Rahul

1. Team size, and how late days work for teams (D15).
2. Alert-set size, and whether there is a set-level budget (D2).
3. May students reuse `demos/intake` (D3)?
4. Is a model-free planner acceptable (D4)?
5. Radicale instead of BenchmarkPython, and a new grading alert A1 (D5).
6. The model and provider, and whether the course supplies credentials. Lecture 1 mentions "course-provided model credentials"; nothing is published.
7. The Semgrep ruleset license (D12).
8. Publish the grading breakdown (D13)? Are fixed entry-point names acceptable (D14)?
9. Keep "missing usage is not zero" and "no automatic retries" as requirements (D16)?
10. Do you have homework templates to align with? The meeting said you might.

## 8. Validation results

Run in this repository checkout on macOS (Darwin 25.6, arm64) with uv 0.9.18
and CPython 3.12.12. It was also run in a clean copy made from only the files
to be committed. No paid model calls were made and no API keys were used.

| Check | Command | Result |
|---|---|---|
| Install | `uv sync --group scan` | langgraph 1.2.12, langchain-core 1.6.4, pydantic 2.13.5, pytest 9.1.1, bandit 1.9.4, semgrep 1.176.0. langchain 1.4.2 needs `--extra live`. |
| Tests | `uv run pytest` | 19 passed, 36 xfailed. Every xfail names a `StudentTODO` stub, and only acceptance tests can xfail. A clean copy without the checkout gives 18 passed, 1 skipped, 36 xfailed. |
| Lint | `uvx ruff@latest check --select E,F,W,B,UP,I --line-length 130 src tests` | Clean |
| CLI help | `uv run triage <cmd> --help`, all 6 commands | Exit 0 (covered by the tests) |
| Target | `uv run triage fetch-target` | `radicale@eff8027f3dc4 (v3.8.0, GPL-3.0)` |
| Scans | `scripts/scan_target.sh` | Bandit 77 results and 0 errors; Semgrep 16 results and 0 errors. Both match `data/scans/` once the timestamps are removed, also under the stock macOS `/bin/bash` 3.2. The rule ids contain no machine paths. The backup target (`sqlite-utils`, empty exclude list) gives 52 and 3. |
| Fixtures | `uv run triage validate-fixtures` | 5 of 5 selections match exactly one raw result at lines that exist at the pinned commit |
| Experiment script | `scripts/run_exhaustion.sh` | Stops with `not implemented yet (student TODO): triage.application.intake.normalize_bandit`, as expected |
| Live adapter | offline payload inspection with fake keys | The output cap reaches the Anthropic (`max_tokens`), OpenAI (`max_completion_tokens`) and Ollama (`options.num_predict`) requests with the three tool schemas. The Ollama input estimate works without `transformers`. |

**Not validated:**

- **Acceptance tests against an implementation.** They have never been run against a working implementation, because no reference solution was written, by instruction. Before release, run them against the instructor reference.
- **Live model runs.**
- **Linux.**
- **Windows.** The helper scripts are bash, so the handout says to use WSL.
- **Token counting against a live endpoint.** The per-integration behaviour in `LangChainProvider` was read from the library sources (langchain-openai 1.6.4, langchain-anthropic 1.7.3, langchain-core 1.6.4) and probed offline, not exercised against a live model.

## 9. Release checklist

- [ ] Open items in §4 and the questions in §7 resolved; the handout's "Internal draft" banner removed.
- [ ] Acceptance tests pass against a private reference implementation.
- [ ] Model, provider, and credentials announced; the `configs/live.toml` comment updated.
- [ ] Grading alert A1 chosen and kept in `instructor-materials`; the grading guide updated from BenchmarkPython.
- [ ] Semgrep ruleset license confirmed.
- [ ] Full setup run on Linux, and on WSL if supported.
- [ ] Org profile, `course_structure.md`, and the Canvas syllabus updated to the Oct 16 due date.
- [ ] `INSTRUCTOR_REVIEW.md` removed; the repository marked as a template, or distributed by the chosen mechanism.
