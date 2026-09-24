# HW1 Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the HW1 Python starter with a specification-only package: a LaTeX brief, a config example, a report schema, and a README template. Staff release checks keep these files consistent with one another.

**Architecture:** The student repo (`hw1-agent-architectures`) ships only static artefacts. All staff tooling and the tests that check the artefacts live in the private `instructor-materials` repo, under `../instructor-materials/`. One Python module there, `contract.py`, holds the canonical values: commits, `[scan]` blocks, README headings and rubric ids. Every test compares a shipped file against it. The brief pulls the `[scan]` blocks, the config and the report example in with `\lstinputlisting`, so each exists in exactly one file.

**Tech Stack:**
- LaTeX: `article` class, `savetrees`, `listings`, `tcolorbox`, built with `tectonic`.
- JSON Schema draft 2020-12.
- Python 3.12+ (`tomllib`), with `pytest` and `jsonschema` run through `uv run --with`.
- Bandit 1.9.4 through `uvx --python 3.12`.

**Spec:** `docs/superpowers/specs/2026-09-24-hw1-redesign-design.md`

## Global Constraints

- Target pins (spec §4.2):
  - Radicale `eff8027f3dc4910be1659ee71f4b4a454ade5a8c`
  - SGLang `bbe9c7eeb520b0a67e92d133dfc137a3688dc7f2`
  - OWASP BenchmarkPython `f1291485808b66e20ddb6b01b10dc71b3df8c8ba`
- Scanner: Bandit `1.9.4`, `min_severity = "MEDIUM"`, any confidence, on CPython 3.12.
- CLI: `./their-agent --input <target checkout root> --output <out dir> --config config.toml`
- `report.json` row `status` is one of `classified`, `budget_exhausted`, `error`. `label` is `0` or `1` only when the status is `classified`, and otherwise `null`.
- Brief: `briefs/hw1.tex` on letter paper, loading `\usepackage[margins=tight]{savetrees}`. The built `briefs/hw1.pdf` is committed.
- Brief prose is drafted and revised with the `orwell:academic` skill.
- The student repo never contains the held-out answer keys, the SGLang CVE ids, or the string `instructor-materials`.
- The cyberbird reference is `https://github.com/comse6998-019/cyberbird/blob/cf7e96c8bd9e74470b99b7b754bb72392427cfc6/cyberbird/reactive/workspace.py`. It was checked on 2026-09-24: `resolve` at line 50, `AgentWorkspace` at line 71, `WITHHELD_GLOBS` at line 45.
- Dates:
  - released Friday, September 25, 2026;
  - due Friday, October 16, 2026, before 11:59 p.m.
- Grading: 20 points, one per rubric item (A1 to A7, B1 to B10, C1 to C3).
- Commits in `hw1-agent-architectures` go on branch `hw1-redesign`. Commits in `instructor-materials` stage explicit paths only, because that repo has unrelated uncommitted edits in `canvas_syllabus.html` and `course_structure.md`.
- Every commit message ends with `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.

## Review Focus

- **The brief leaks held-out answers.** Someone copying spec §4.2 into the brief could include the CVE ids or "kept in instructor-materials". Expect the student-facing files to contain neither. The test is in Task 6.
- **A `[scan]` block drifts between the brief, `config.example.toml` and the grading configs.** Expect one source. The brief includes the files, and the tests compare them to `contract.py`. The tests are in Tasks 4 and 6.
- **A Bandit scan glob matches nothing.** For example, the OWASP glob on a checkout whose layout changed. Expect a hard error, not a silent count of zero. The test is in Task 2.
- **A team adds extra fields to `report.json` or to a row.** For example, `tokens_per_alert`. A team would expect this to validate, since the schema fixes only the required fields. The test is in Task 3.
- **The committed PDF is stale because `hw1.tex` changed after the last build.** Expect the release check to fail. The test is in Task 6.

---

## File map

Student repo (`/Users/rkrsn/COMSE6998-019/hw1-agent-architectures`), final state:

| File | Responsibility |
|---|---|
| `.gitignore` | `runs/` and `targets/` |
| `README.md` | A pointer to the brief, and a list of the files in the repo |
| `README.template.md` | The README contract (spec §4.7) as fixed headings with HTML-comment instructions |
| `config.example.toml` | The config contract (spec §4.4), with Radicale values |
| `report.schema.json` | JSON Schema for `report.json` (spec §4.5) |
| `briefs/hw1.tex`, `briefs/hw1.pdf` | The handout |
| `briefs/scan/radicale.toml`, `briefs/scan/sglang.toml`, `briefs/scan/owasp-benchmark-python.toml` | The three required `[scan]` blocks, included by the brief |
| `briefs/report.example.json` | A valid example `report.json`, included by the brief |
| `docs/superpowers/...` | The spec and this plan |

Staff repo (`/Users/rkrsn/COMSE6998-019/instructor-materials/hw1/release/`):

| File | Responsibility |
|---|---|
| `contract.py` | Canonical values and the path to the student repo |
| `count_alerts.py` | Fetches the targets at their pins, runs Bandit with each `[scan]` block, and reports the counts and the answer-key path |
| `test_layout.py` | The student repo contains only allowed files |
| `test_count_alerts.py` | Unit tests for how `count_alerts.py` builds the Bandit arguments |
| `test_schema.py` | Schema accepts and rejects the right documents; the example validates |
| `test_config.py` | The config example and the scan files match the contract |
| `test_readme_template.py` | The README template matches the contract |
| `test_brief.py` | The brief contains the required content, leaks nothing, and the PDF is fresh |
| `RESULTS.md` | Measured counts and the answer-key path from Task 2 |

Run all staff checks from `/Users/rkrsn/COMSE6998-019` with:

```sh
uv run --python 3.12 --with pytest --with jsonschema pytest instructor-materials/hw1/release -q
```

---

### Task 1: Contract module and removal of the Python starter

**Files:**
- Create: `instructor-materials/hw1/release/contract.py`
- Create: `instructor-materials/hw1/release/test_layout.py`
- Delete (student repo): `configs/`, `data/`, `scripts/`, `src/`, `tests/`, `pyproject.toml`, `uv.lock`, `.python-version`, `.env.example`, `ASSIGNMENT.md`, `REPORT_TEMPLATE.md`, `INSTRUCTOR_REVIEW.md`
- Modify (student repo): `.gitignore`

**Interfaces:**
- Produces:
  - `contract.HW1_REPO: Path`
  - `contract.TARGETS: dict[str, dict]`, keyed `radicale`, `sglang`, `owasp-benchmark-python`, each with `url: str`, `commit: str`, `title: str`, `scan_toml: str`, `expected_alerts: int`
  - `contract.README_H2: list[str]`
  - `contract.RUN_H3: list[str]`
  - `contract.RUBRIC_IDS: list[str]`
  - `contract.ALLOWED_FILES: set[str]`
  - `contract.ALLOWED_PREFIXES: tuple[str, ...]`
  - `contract.CYBERBIRD_URL: str`
  - `contract.FORBIDDEN_STRINGS: list[str]`

- [ ] **Step 1: Write `contract.py`**

```python
"""Canonical HW1 release values. Every release check compares a shipped file to these."""
from __future__ import annotations

import os
from pathlib import Path

# instructor-materials/hw1/release/contract.py -> parents[3] is the COMSE6998-019 folder.
HW1_REPO = Path(os.environ.get(
    "HW1_REPO", Path(__file__).resolve().parents[3] / "hw1-agent-architectures"))

TARGETS: dict[str, dict] = {
    "radicale": {
        "title": "Radicale",
        "url": "https://github.com/Kozea/Radicale",
        "commit": "eff8027f3dc4910be1659ee71f4b4a454ade5a8c",
        "expected_alerts": 10,
        "scan_toml": (
            '[scan]\n'
            'paths = ["radicale"]\n'
            'exclude = ["radicale/tests"]\n'
            'min_severity = "MEDIUM"\n'
            'bandit_version = "1.9.4"\n'
        ),
    },
    "sglang": {
        "title": "SGLang",
        "url": "https://github.com/sgl-project/sglang",
        "commit": "bbe9c7eeb520b0a67e92d133dfc137a3688dc7f2",
        "expected_alerts": 20,
        "scan_toml": (
            '[scan]\n'
            'paths = ["python/sglang/multimodal_gen/runtime",\n'
            '         "scripts/playground/replay_request_dump.py"]\n'
            'exclude = []\n'
            'min_severity = "MEDIUM"\n'
            'bandit_version = "1.9.4"\n'
        ),
    },
    "owasp-benchmark-python": {
        "title": "OWASP BenchmarkPython",
        "url": "https://github.com/OWASP-Benchmark/BenchmarkPython",
        "commit": "f1291485808b66e20ddb6b01b10dc71b3df8c8ba",
        "expected_alerts": 18,
        "scan_toml": (
            '[scan]\n'
            'paths = ["testcode/BenchmarkTest000*.py"]\n'
            'exclude = []\n'
            'min_severity = "MEDIUM"\n'
            'bandit_version = "1.9.4"\n'
        ),
    },
}

README_H2 = ["Team", "Requirements", "Setup", "Fetch targets", "Configs", "Run",
             "Outputs", "Validate", "Rubric map", "Known issues"]
RUN_H3 = ["Radicale", "SGLang", "OWASP BenchmarkPython", "Budget cutoff"]
RUBRIC_IDS = [f"A{i}" for i in range(1, 8)] + [f"B{i}" for i in range(1, 11)] + ["C1", "C2", "C3"]

ALLOWED_FILES = {
    ".gitignore", "README.md", "README.template.md", "config.example.toml",
    "report.schema.json", "briefs/hw1.tex", "briefs/hw1.pdf", "briefs/report.example.json",
    "briefs/scan/radicale.toml", "briefs/scan/sglang.toml",
    "briefs/scan/owasp-benchmark-python.toml",
}
ALLOWED_PREFIXES = ("docs/superpowers/",)

CYBERBIRD_URL = ("https://github.com/comse6998-019/cyberbird/blob/"
                 "cf7e96c8bd9e74470b99b7b754bb72392427cfc6/cyberbird/reactive/workspace.py")

# Held-out answers and staff-only locations. None may appear in a student-facing file.
FORBIDDEN_STRINGS = ["CVE-2026-3059", "CVE-2026-3060", "CVE-2026-3989", "GHSA-",
                     "instructor-materials", "TODO", "TBD", "XXX"]
```

- [ ] **Step 2: Write the failing layout test**

`instructor-materials/hw1/release/test_layout.py`:

```python
import subprocess

from contract import ALLOWED_FILES, ALLOWED_PREFIXES, HW1_REPO


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=HW1_REPO, check=True,
                         capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if line]


def test_only_allowed_files_are_tracked():
    extra = [f for f in tracked_files()
             if f not in ALLOWED_FILES and not f.startswith(ALLOWED_PREFIXES)]
    assert extra == [], f"unexpected tracked files: {extra}"


def test_gitignore_is_runs_and_targets_only():
    assert (HW1_REPO / ".gitignore").read_text() == "runs/\ntargets/\n"
```

Also create `instructor-materials/hw1/release/conftest.py`, so that tests can import `contract`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
```

- [ ] **Step 3: Run the test and confirm it fails**

Run: `cd /Users/rkrsn/COMSE6998-019 && uv run --python 3.12 --with pytest --with jsonschema pytest instructor-materials/hw1/release/test_layout.py -q`

Expected: 2 failures. The first lists `pyproject.toml`, `src/triage/...` and the other starter files. The second is a `.gitignore` mismatch.

- [ ] **Step 4: Delete the starter and rewrite `.gitignore`**

```sh
cd /Users/rkrsn/COMSE6998-019/hw1-agent-architectures
git rm -r -q configs data scripts src tests pyproject.toml uv.lock .python-version .env.example ASSIGNMENT.md REPORT_TEMPLATE.md INSTRUCTOR_REVIEW.md
printf 'runs/\ntargets/\n' > .gitignore
```

The old `README.md` stays for now; Task 7 rewrites it. It is on the allowlist, so the layout test passes.

- [ ] **Step 5: Run the test and confirm it passes**

Run: the command from Step 3. Expected: `2 passed`.

- [ ] **Step 6: Commit both repos**

```sh
cd /Users/rkrsn/COMSE6998-019/hw1-agent-architectures
git add .gitignore
git commit -m "Remove the Python starter; HW1 becomes specification-only

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
cd /Users/rkrsn/COMSE6998-019/instructor-materials
git add hw1/release/contract.py hw1/release/conftest.py hw1/release/test_layout.py
git commit -m "HW1 release checks: contract and repo layout

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Measure the alert counts and find the OWASP answer key

This task implements spec §9 checks 1, 2 and 5. Its numbers go into the brief, so it runs before Task 6.

**Files:**
- Create: `instructor-materials/hw1/release/count_alerts.py`
- Create: `instructor-materials/hw1/release/test_count_alerts.py`
- Create: `instructor-materials/hw1/release/RESULTS.md`
- Modify, only if the counts differ: `instructor-materials/hw1/release/contract.py` (`expected_alerts`) and `hw1-agent-architectures/docs/superpowers/specs/2026-09-24-hw1-redesign-design.md` §4.3

**Interfaces:**
- Consumes: `contract.TARGETS`
- Produces:
  - `count_alerts.expand_paths(root: Path, patterns: list[str]) -> list[str]`, which returns sorted repo-relative paths and raises `ValueError` when a pattern matches nothing;
  - `count_alerts.bandit_args(root: Path, scan: dict, out: Path) -> list[str]`;
  - a CLI, `python count_alerts.py --work DIR`.

- [ ] **Step 1: Write the failing tests**

`instructor-materials/hw1/release/test_count_alerts.py`:

```python
from pathlib import Path

import pytest

from count_alerts import bandit_args, expand_paths


def make(tmp_path: Path, *files: str) -> Path:
    for f in files:
        p = tmp_path / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x = 1\n")
    return tmp_path


def test_expand_paths_globs_and_sorts(tmp_path):
    root = make(tmp_path, "testcode/BenchmarkTest00002.py", "testcode/BenchmarkTest00001.py",
                "testcode/BenchmarkTest00100.py")
    assert expand_paths(root, ["testcode/BenchmarkTest000*.py"]) == [
        "testcode/BenchmarkTest00001.py", "testcode/BenchmarkTest00002.py"]


def test_expand_paths_keeps_plain_directories(tmp_path):
    root = make(tmp_path, "radicale/app.py")
    assert expand_paths(root, ["radicale"]) == ["radicale"]


def test_expand_paths_refuses_a_pattern_that_matches_nothing(tmp_path):
    root = make(tmp_path, "radicale/app.py")
    with pytest.raises(ValueError, match="matches nothing"):
        expand_paths(root, ["testcode/BenchmarkTest000*.py"])


def test_bandit_args_medium_severity_and_excludes(tmp_path):
    root = make(tmp_path, "radicale/app.py", "radicale/tests/t.py")
    scan = {"paths": ["radicale"], "exclude": ["radicale/tests"],
            "min_severity": "MEDIUM", "bandit_version": "1.9.4"}
    args = bandit_args(root, scan, tmp_path / "out.json")
    assert args[:4] == ["uvx", "--python", "3.12", "bandit==1.9.4"]
    assert "--severity-level" in args and args[args.index("--severity-level") + 1] == "medium"
    assert args[args.index("-x") + 1] == "radicale/tests"
    assert args[-1] == "radicale"


def test_bandit_args_without_excludes_has_no_x_flag(tmp_path):
    root = make(tmp_path, "a/b.py")
    scan = {"paths": ["a"], "exclude": [], "min_severity": "MEDIUM", "bandit_version": "1.9.4"}
    assert "-x" not in bandit_args(root, scan, tmp_path / "o.json")
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `cd /Users/rkrsn/COMSE6998-019 && uv run --python 3.12 --with pytest --with jsonschema pytest instructor-materials/hw1/release/test_count_alerts.py -q`

Expected: an import error, `No module named 'count_alerts'`.

- [ ] **Step 3: Write `count_alerts.py`**

```python
"""Fetch each HW1 target at its pinned commit, run Bandit with its [scan] block, report counts.

    python count_alerts.py --work /tmp/hw1-targets

Static analysis only: no target code is installed or run.
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
import tomllib
from pathlib import Path

from contract import TARGETS


def expand_paths(root: Path, patterns: list[str]) -> list[str]:
    """Expand repo-relative globs. A pattern that matches nothing is an error, not zero alerts."""
    found: list[str] = []
    for pattern in patterns:
        matches = sorted(p.relative_to(root).as_posix() for p in root.glob(pattern))
        if not matches:
            raise ValueError(f"scan path {pattern!r} matches nothing under {root}")
        found.extend(matches)
    return found


def bandit_args(root: Path, scan: dict, out: Path) -> list[str]:
    args = ["uvx", "--python", "3.12", f"bandit=={scan['bandit_version']}", "-q", "-r",
            "--severity-level", scan["min_severity"].lower(), "-f", "json", "-o", str(out)]
    if scan["exclude"]:
        args += ["-x", ",".join(scan["exclude"])]
    return args + expand_paths(root, scan["paths"])


def fetch(url: str, commit: str, dest: Path) -> None:
    """Shallow-fetch exactly one commit. No history, so later fix commits are absent."""
    if (dest / ".git").is_dir():
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=dest, capture_output=True,
                              text=True).stdout.strip()
        if head == commit:
            return
    dest.mkdir(parents=True, exist_ok=True)
    for cmd in (["git", "init", "-q"], ["git", "remote", "add", "origin", url],
                ["git", "fetch", "-q", "--depth", "1", "origin", commit],
                ["git", "checkout", "-q", "FETCH_HEAD"]):
        subprocess.run(cmd, cwd=dest, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    work = parser.parse_args().work.resolve()
    for name, target in TARGETS.items():
        root = work / name
        fetch(target["url"], target["commit"], root)
        scan = tomllib.loads(target["scan_toml"])["scan"]
        out = work / f"{name}.bandit.json"
        # Bandit exits 1 when it reports issues; that is expected.
        proc = subprocess.run(bandit_args(root, scan, out), cwd=root)
        if proc.returncode not in (0, 1):
            raise SystemExit(f"bandit failed on {name} (exit {proc.returncode})")
        report = json.loads(out.read_text())
        if report["errors"]:
            raise SystemExit(f"bandit parse errors on {name}: {report['errors'][:3]}")
        rules = collections.Counter(r["test_id"] for r in report["results"])
        print(f"{name}: {len(report['results'])} alerts (expected {target['expected_alerts']}) "
              f"by rule {dict(rules.most_common())}")
        if name == "owasp-benchmark-python":
            keys = sorted(p.relative_to(root).as_posix() for p in root.rglob("expectedresults*.csv"))
            cases = sorted({Path(r["filename"]).stem for r in report["results"]})
            print(f"  answer key files: {keys}")
            print(f"  cases with alerts: {cases[0]} .. {cases[-1]} ({len(cases)} files)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: the command from Step 2. Expected: `5 passed`.

- [ ] **Step 5: Run the measurement**

Run: `cd /Users/rkrsn/COMSE6998-019/instructor-materials/hw1/release && uv run --python 3.12 python count_alerts.py --work /tmp/hw1-targets`

The shallow fetch of SGLang downloads one tree, which is a few hundred MB. Allow up to 10 minutes.

Expected output shape:

```
radicale: 10 alerts (expected 10) by rule {...}
sglang: 20 alerts (expected 20) by rule {...}
owasp-benchmark-python: 18 alerts (expected 18) by rule {...}
  answer key files: ['expectedresults-0.1.csv']
  cases with alerts: BenchmarkTest00013 .. BenchmarkTest00099 (N files)
```

Check each of these:
1. Each count equals its expected value.
2. The OWASP case range lies inside `BenchmarkTest00001` to `BenchmarkTest00099` (spec §9 check 5).
3. At least one answer-key file is found (spec §9 check 2).

- [ ] **Step 6: Record the results, and reconcile if they differ**

Write `RESULTS.md` with the date, the exact command, and the output pasted verbatim.

If a count differs:
1. Update `expected_alerts` in `contract.py`.
2. Update the alert counts in spec §4.3 (the comment lines and the paragraph below them) to the measured values.
3. Note the change in `RESULTS.md`.

If no answer-key file is found, stop and report to the instructor. The withholding requirement in the brief depends on that path.

- [ ] **Step 7: Commit**

```sh
cd /Users/rkrsn/COMSE6998-019/instructor-materials
git add hw1/release/count_alerts.py hw1/release/test_count_alerts.py hw1/release/RESULTS.md hw1/release/contract.py
git commit -m "HW1 release checks: measure scan counts on fresh clones

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

If the spec changed, also commit it in `hw1-agent-architectures`, with the message `Spec: measured alert counts`.

---

### Task 3: `report.schema.json` and the example report

**Files:**
- Create: `hw1-agent-architectures/report.schema.json`
- Create: `hw1-agent-architectures/briefs/report.example.json`
- Create: `instructor-materials/hw1/release/test_schema.py`

**Interfaces:**
- Consumes: `contract.HW1_REPO`, `contract.TARGETS`
- Produces: `report.schema.json` (draft 2020-12) and `briefs/report.example.json`, both used by Task 6.

- [ ] **Step 1: Write the failing tests**

`instructor-materials/hw1/release/test_schema.py`:

```python
import copy
import json

import pytest
from jsonschema import Draft202012Validator

from contract import HW1_REPO


@pytest.fixture(scope="module")
def validator():
    schema = json.loads((HW1_REPO / "report.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture
def example():
    return json.loads((HW1_REPO / "briefs/report.example.json").read_text())


def errors(validator, doc):
    return [e.message for e in validator.iter_errors(doc)]


def test_example_is_valid(validator, example):
    assert errors(validator, example) == []


def test_example_has_one_row_per_alert_and_is_ordered(example):
    rows = example["alerts"]
    assert example["scan"]["alert_count"] == len(rows)
    assert rows == sorted(rows, key=lambda r: (r["path"], r["line"], r["test_id"]))


def test_example_shows_all_three_statuses(example):
    assert {r["status"] for r in example["alerts"]} == {"classified", "budget_exhausted", "error"}


@pytest.mark.parametrize("mutate", [
    lambda d: d["alerts"][0].update(label=None),                     # classified needs a label
    lambda d: d["alerts"][0].update(label=2),                        # label is 0 or 1
    lambda d: d["alerts"][0].update(evidence=[]),                    # classified needs evidence
    lambda d: d["alerts"][0].update(rationale=""),                   # classified needs a rationale
    lambda d: d["alerts"][0].update(alert_id="a/b"),                 # ids are file-name safe
    lambda d: d["alerts"][0].update(severity="LOW"),                 # MEDIUM+ only
    lambda d: d["alerts"][0].update(status="skipped"),               # closed status set
    lambda d: d["alerts"][0].pop("line"),                            # required field
    lambda d: d["alerts"][0]["evidence"][0].update(start_line=0),    # 1-based lines
    lambda d: d["alerts"][0]["evidence"][0].update(path="/etc/passwd"),  # repo-relative
    lambda d: d["scan"].update(min_severity="LOW"),
    lambda d: d["scan"].update(bandit_version="1.8.0"),
    lambda d: d["target"].update(commit="eff8027f"),                 # full 40-char SHA
    lambda d: d["budget"].update(exhausted="no"),
], ids=["classified-null-label", "label-2", "no-evidence", "empty-rationale", "bad-id",
        "low-severity", "unknown-status", "missing-line", "line-0", "absolute-evidence",
        "scan-low", "old-bandit", "short-sha", "exhausted-string"])
def test_invalid_documents_are_rejected(validator, example, mutate):
    doc = copy.deepcopy(example)
    mutate(doc)
    assert errors(validator, doc) != []


def test_non_classified_row_must_have_null_label(validator, example):
    doc = copy.deepcopy(example)
    row = next(r for r in doc["alerts"] if r["status"] == "budget_exhausted")
    row["label"] = 1
    assert errors(validator, doc) != []


def test_extra_fields_are_allowed(validator, example):
    doc = copy.deepcopy(example)
    doc["team_notes"] = "anything"
    doc["alerts"][0]["tokens_used"] = 812
    assert errors(validator, doc) == []
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `cd /Users/rkrsn/COMSE6998-019 && uv run --python 3.12 --with pytest --with jsonschema pytest instructor-materials/hw1/release/test_schema.py -q`

Expected: errors, with `FileNotFoundError: .../report.schema.json`.

- [ ] **Step 3: Write `report.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/comse6998-019/hw1-agent-architectures/report.schema.json",
  "title": "HW1 report.json",
  "description": "One row per in-scope Bandit alert. Rules the schema cannot express, and graders check: len(alerts) == scan.alert_count; rows ordered by path, then line, then test_id; used_tokens is the sum of provider-reported usage. Extra fields are allowed.",
  "type": "object",
  "required": ["target", "scan", "budget", "alerts"],
  "properties": {
    "target": {
      "type": "object",
      "required": ["input", "commit"],
      "properties": {
        "input": {"type": "string", "minLength": 1},
        "commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"}
      }
    },
    "scan": {
      "type": "object",
      "required": ["bandit_version", "min_severity", "alert_count"],
      "properties": {
        "bandit_version": {"const": "1.9.4"},
        "min_severity": {"const": "MEDIUM"},
        "alert_count": {"type": "integer", "minimum": 0}
      }
    },
    "budget": {
      "type": "object",
      "required": ["max_tokens", "used_tokens", "exhausted"],
      "properties": {
        "max_tokens": {"type": "integer", "minimum": 0},
        "used_tokens": {"type": "integer", "minimum": 0},
        "exhausted": {"type": "boolean"}
      }
    },
    "alerts": {"type": "array", "items": {"$ref": "#/$defs/alert"}}
  },
  "$defs": {
    "evidence": {
      "type": "object",
      "required": ["path", "start_line", "end_line"],
      "properties": {
        "path": {"type": "string", "minLength": 1, "pattern": "^[^/]"},
        "start_line": {"type": "integer", "minimum": 1},
        "end_line": {"type": "integer", "minimum": 1}
      }
    },
    "alert": {
      "type": "object",
      "required": ["alert_id", "test_id", "path", "line", "severity", "confidence",
                   "label", "status", "rationale", "evidence"],
      "properties": {
        "alert_id": {"type": "string", "pattern": "^[A-Za-z0-9._-]+$"},
        "test_id": {"type": "string", "pattern": "^B[0-9]{3}$"},
        "path": {"type": "string", "minLength": 1, "pattern": "^[^/]"},
        "line": {"type": "integer", "minimum": 1},
        "severity": {"enum": ["MEDIUM", "HIGH"]},
        "confidence": {"enum": ["LOW", "MEDIUM", "HIGH"]},
        "label": {"enum": [0, 1, null]},
        "status": {"enum": ["classified", "budget_exhausted", "error"]},
        "rationale": {"type": "string"},
        "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}}
      },
      "if": {"properties": {"status": {"const": "classified"}}},
      "then": {
        "properties": {
          "label": {"enum": [0, 1]},
          "rationale": {"minLength": 1},
          "evidence": {"minItems": 1}
        }
      },
      "else": {"properties": {"label": {"const": null}}}
    }
  }
}
```

- [ ] **Step 4: Write `briefs/report.example.json`**

This is an illustrative three-row Radicale report. The rows are real Bandit locations from the staff scan, but it is **not** an answer key: `rationale` describes the format, not a verdict, and the labels are arbitrary. The brief says so.

```json
{
  "target": {"input": "targets/radicale", "commit": "eff8027f3dc4910be1659ee71f4b4a454ade5a8c"},
  "scan": {"bandit_version": "1.9.4", "min_severity": "MEDIUM", "alert_count": 3},
  "budget": {"max_tokens": 20000, "used_tokens": 19480, "exhausted": true},
  "alerts": [
    {
      "alert_id": "radicale-auth-oauth2-py-60-B113",
      "test_id": "B113",
      "path": "radicale/auth/oauth2.py",
      "line": 60,
      "severity": "MEDIUM",
      "confidence": "LOW",
      "label": 0,
      "status": "classified",
      "rationale": "Format illustration only: one or two sentences citing what the agent read.",
      "evidence": [{"path": "radicale/auth/oauth2.py", "start_line": 52, "end_line": 66}]
    },
    {
      "alert_id": "radicale-storage-multifilesystem-lock-py-102-B602",
      "test_id": "B602",
      "path": "radicale/storage/multifilesystem/lock.py",
      "line": 102,
      "severity": "HIGH",
      "confidence": "HIGH",
      "label": null,
      "status": "error",
      "rationale": "The model reply could not be parsed as a label.",
      "evidence": []
    },
    {
      "alert_id": "radicale-storage-multifilesystem-sync-py-79-B301",
      "test_id": "B301",
      "path": "radicale/storage/multifilesystem/sync.py",
      "line": 79,
      "severity": "MEDIUM",
      "confidence": "HIGH",
      "label": null,
      "status": "budget_exhausted",
      "rationale": "",
      "evidence": []
    }
  ]
}
```

Before committing, confirm the three locations against the Bandit output from Task 2 (`/tmp/hw1-targets/radicale.bandit.json`). Fix `severity` and `confidence` to the values Bandit reports:

```sh
python3 -c "import json; [print(r['test_id'], r['filename'], r['line_number'], r['issue_severity'], r['issue_confidence']) for r in json.load(open('/tmp/hw1-targets/radicale.bandit.json'))['results']]"
```

- [ ] **Step 5: Run the tests and confirm they pass**

Run: the command from Step 2. Expected: `19 passed`.

- [ ] **Step 6: Commit both repos**

```sh
cd /Users/rkrsn/COMSE6998-019/hw1-agent-architectures
git add report.schema.json briefs/report.example.json
git commit -m "Add report.json schema and example

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
cd /Users/rkrsn/COMSE6998-019/instructor-materials
git add hw1/release/test_schema.py
git commit -m "HW1 release checks: report schema

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: `config.example.toml` and the three scan files

**Files:**
- Create: `hw1-agent-architectures/config.example.toml`
- Create: `hw1-agent-architectures/briefs/scan/radicale.toml`, `briefs/scan/sglang.toml`, `briefs/scan/owasp-benchmark-python.toml`
- Create: `instructor-materials/hw1/release/test_config.py`

**Interfaces:**
- Consumes: `contract.HW1_REPO`, `contract.TARGETS`
- Produces: the files that Task 6 includes with `\lstinputlisting`.

- [ ] **Step 1: Write the failing tests**

`instructor-materials/hw1/release/test_config.py`:

```python
import tomllib

import pytest

from contract import HW1_REPO, TARGETS


@pytest.mark.parametrize("name", list(TARGETS))
def test_scan_file_is_byte_identical_to_contract(name):
    assert (HW1_REPO / f"briefs/scan/{name}.toml").read_text() == TARGETS[name]["scan_toml"]


@pytest.mark.parametrize("name", list(TARGETS))
def test_scan_block_has_exactly_the_four_keys(name):
    scan = tomllib.loads(TARGETS[name]["scan_toml"])["scan"]
    assert set(scan) == {"paths", "exclude", "min_severity", "bandit_version"}
    assert scan["min_severity"] == "MEDIUM" and scan["bandit_version"] == "1.9.4"


def test_config_example_scan_equals_radicale():
    config = tomllib.loads((HW1_REPO / "config.example.toml").read_text())
    assert config["scan"] == tomllib.loads(TARGETS["radicale"]["scan_toml"])["scan"]


def test_config_example_model_and_budget():
    config = tomllib.loads((HW1_REPO / "config.example.toml").read_text())
    assert set(config) == {"scan", "model", "budget"}
    assert set(config["model"]) == {"provider", "name"}
    assert all(isinstance(config["model"][k], str) and config["model"][k] for k in config["model"])
    assert config["budget"] == {"max_tokens": 200000, "output_allowance": 1024, "max_steps": 200}
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `cd /Users/rkrsn/COMSE6998-019 && uv run --python 3.12 --with pytest --with jsonschema pytest instructor-materials/hw1/release/test_config.py -q`

Expected: 3 failures from the scan files and 2 from the config (`FileNotFoundError`). The 3 key tests pass.

- [ ] **Step 3: Write the scan files**

Write each file with exactly the content of `contract.TARGETS[name]["scan_toml"]`, with no comment lines and one trailing newline. Generate them rather than typing them, so they are identical byte for byte:

```sh
cd /Users/rkrsn/COMSE6998-019/instructor-materials/hw1/release
uv run --python 3.12 python -c "
from contract import HW1_REPO, TARGETS
d = HW1_REPO / 'briefs/scan'; d.mkdir(parents=True, exist_ok=True)
for n, t in TARGETS.items(): (d / f'{n}.toml').write_text(t['scan_toml'])
"
```

- [ ] **Step 4: Write `config.example.toml`**

```toml
# HW1 agent configuration. Your agent must read this file:
#   ./their-agent --input <target checkout root> --output <out dir> --config config.toml
#
# [scan] is fixed by staff for each target. Copy the block for your target from
# the brief's "Required scan scope for each target" section, unchanged. Graders
# replace it with the same staff block when they run your agent.
[scan]
paths = ["radicale"]                 # globs relative to --input; your Bandit wrapper expands them
exclude = ["radicale/tests"]         # globs relative to --input
min_severity = "MEDIUM"              # required; do not lower
bandit_version = "1.9.4"             # required

# Your choice of provider and model. Read secrets from environment variables,
# never from this file.
[model]
provider = "anthropic"
name = "claude-sonnet-5"

[budget]
max_tokens = 200000                  # the whole run, across all alerts
output_allowance = 1024              # max output tokens for each model call
max_steps = 200                      # failsafe, separate from the token budget
```

- [ ] **Step 5: Run the tests and confirm they pass**

Run: the command from Step 2. Expected: `8 passed`.

- [ ] **Step 6: Commit both repos**

```sh
cd /Users/rkrsn/COMSE6998-019/hw1-agent-architectures
git add config.example.toml briefs/scan
git commit -m "Add config example and required scan blocks

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
cd /Users/rkrsn/COMSE6998-019/instructor-materials
git add hw1/release/test_config.py
git commit -m "HW1 release checks: config and scan blocks

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: `README.template.md`

**Files:**
- Create: `hw1-agent-architectures/README.template.md`
- Create: `instructor-materials/hw1/release/test_readme_template.py`
- Modify: `instructor-materials/hw1/release/contract.py` (add the `Trajectory` heading and the trace constants; spec §4.8 was added after Task 1 ran)

**Step 0 (before Step 1): Update `contract.py` for spec §4.8.** Replace the `README_H2` line and append the trace constants:

```python
README_H2 = ["Team", "Requirements", "Setup", "Fetch targets", "Configs", "Run",
             "Outputs", "Validate", "Trajectory", "Rubric map", "Known issues"]
```

```python
CYBERBIRD_TRACE_URL = ("https://github.com/comse6998-019/cyberbird/blob/"
                       "cf7e96c8bd9e74470b99b7b754bb72392427cfc6/cyberbird/plan_and_validation/trace.py")
CYBERBIRD_TRAJECTORY_URL = ("https://github.com/comse6998-019/cyberbird/blob/"
                            "cf7e96c8bd9e74470b99b7b754bb72392427cfc6/cyberbird/plan_and_validation/trajectory.py")
TRACE_KINDS = ["model_call", "tool_request", "tool_result", "routing", "state_change", "terminal"]
README_CHECK_IDS = [f"R{i}" for i in range(1, 12)]
```

Run the full release suite afterwards; it must stay green. Commit `contract.py` together with this task's staff-repo commit.

**Interfaces:**
- Consumes: `contract.README_H2`, `contract.RUN_H3`, `contract.RUBRIC_IDS`, `contract.FORBIDDEN_STRINGS`
- Produces: the template that teams copy to `README.md`.

- [ ] **Step 1: Write the failing tests**

`instructor-materials/hw1/release/test_readme_template.py`:

```python
import re

import pytest

from contract import FORBIDDEN_STRINGS, HW1_REPO, README_H2, RUBRIC_IDS, RUN_H3


@pytest.fixture(scope="module")
def text():
    return (HW1_REPO / "README.template.md").read_text()


def headings(text, level):
    return re.findall(rf"^{'#' * level} (.+?)\s*$", text, flags=re.M)


def section(text, name):
    m = re.search(rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    assert m, name
    return m.group(1)


def test_h2_headings_exact_and_in_order(text):
    assert headings(text, 2) == README_H2


def test_run_has_the_four_h3_in_order(text):
    assert headings(section(text, "Run"), 3) == RUN_H3


def test_no_h3_outside_run(text):
    for name in README_H2:
        if name != "Run":
            assert headings(section(text, name), 3) == [], name


def test_every_section_has_instructions_and_no_content(text):
    for name in README_H2:
        body = re.sub(r"^### .*$", "", section(text, name), flags=re.M)
        stripped = re.sub(r"<!--.*?-->", "", body, flags=re.S).strip()
        assert "<!--" in body, f"{name} has no instructions"
        assert stripped == "", f"{name} has content outside comments: {stripped[:60]!r}"


def test_rubric_map_lists_every_item(text):
    rubric = section(text, "Rubric map")
    for item in RUBRIC_IDS:
        assert re.search(rf"\b{item}\b", rubric), item


def test_output_dirs_named(text):
    for d in ["runs/radicale", "runs/sglang", "runs/owasp-benchmark-python", "runs/radicale-cutoff"]:
        assert d in text


@pytest.mark.parametrize("s", FORBIDDEN_STRINGS)
def test_no_forbidden_strings(text, s):
    assert s not in text
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `cd /Users/rkrsn/COMSE6998-019 && uv run --python 3.12 --with pytest --with jsonschema pytest instructor-materials/hw1/release/test_readme_template.py -q`

Expected: errors, with `FileNotFoundError: .../README.template.md`.

- [ ] **Step 3: Write `README.template.md`**

All instructions go inside HTML comments. The only visible text is headings.

````markdown
<!--
HW1 README template. Copy this file to README.md and fill in every section.
A grading skill reads README.md, so:
- keep every ## and ### heading exactly as written, in this order;
- add your own headings only as ### inside a section (not inside ## Run);
- put every command in a fenced block tagged sh, one command per line,
  with no $ prompt, no output, no placeholders like <...>, and nothing interactive;
- run every command from the repository root; use repo-relative paths;
- read secrets only from environment variables listed under ## Requirements.
Delete nothing but these comments.
-->

## Team
<!-- Each member's name and UNI. Then the full 40-character commit SHA of the submitted code. -->

## Requirements
<!--
The operating system(s) you tested on. Language and runtime versions.
How Python 3.12 and Bandit 1.9.4 are installed. The model provider and exact model name.
A table with columns Variable, Purpose, listing every environment variable your agent reads.
Never write a value.
-->

## Setup
<!--
One sh block that takes a fresh clone to a ready state: dependencies installed and
Bandit 1.9.4 on the path. The last line prints the Bandit version, for example:
bandit --version
-->

## Fetch targets
<!--
One sh block that clones the three targets into targets/radicale, targets/sglang and
targets/owasp-benchmark-python, checks out the pinned commits from the brief, and
prints git rev-parse HEAD for each.
-->

## Configs
<!--
A table with columns Target, Config file. One row for each target and one row for the
budget-cutoff run. Commit every config file. Each [scan] block must equal the brief's
required block for that target.
-->

## Run
<!--
Four subsections, in this order. Each holds one sh block with one agent command of the form
./their-agent --input targets/radicale --output runs/radicale --config configs/radicale.toml
Output directories: runs/radicale, runs/sglang, runs/owasp-benchmark-python, runs/radicale-cutoff.
Under each block, give the observed wall-clock time and used_tokens.
-->

### Radicale
<!-- Output: runs/radicale -->

### SGLang
<!-- Output: runs/sglang -->

### OWASP BenchmarkPython
<!-- Output: runs/owasp-benchmark-python -->

### Budget cutoff
<!--
Output: runs/radicale-cutoff. The Radicale target with a config whose max_tokens is small
enough that at least one row has status budget_exhausted.
-->

## Outputs
<!--
A table with columns Run, Directory, alert_count, label_1, label_0, null, used_tokens, exhausted.
One row for each run above. Every value must equal the committed report.json in that directory.
-->

## Validate
<!--
One sh block that validates every committed report.json against report.schema.json and exits
non-zero if any fails.
-->

## Trajectory
<!--
One sh block with one command that renders the trajectory of one alert from
runs/radicale/trace.jsonl as a Mermaid sequenceDiagram, using the trace alone.
Then paste the rendered diagram in a fenced block tagged mermaid.
-->

## Rubric map
<!--
A table with columns Item, Where. One row for each item, in this order:
A1 A2 A3 A4 A5 A6 A7 B1 B2 B3 B4 B5 B6 B7 B8 B9 B10 C1 C2 C3.
For B items, Where is path:line or path:start-end in your code.
For A and C items, Where is a section heading in your report.
-->

## Known issues
<!-- Anything that does not work, failed runs, and deviations from the brief. Write None. if there are none. -->
````

- [ ] **Step 4: Run the tests and confirm they pass**

Run: the command from Step 2. Expected: all pass (7 test functions plus 8 parametrised forbidden strings, so `14 passed`).

- [ ] **Step 5: Commit both repos**

```sh
cd /Users/rkrsn/COMSE6998-019/hw1-agent-architectures
git add README.template.md
git commit -m "Add README template for the graded README contract

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
cd /Users/rkrsn/COMSE6998-019/instructor-materials
git add hw1/release/test_readme_template.py
git commit -m "HW1 release checks: README template

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: The LaTeX brief

**Files:**
- Create: `hw1-agent-architectures/briefs/hw1.tex`
- Create (built): `hw1-agent-architectures/briefs/hw1.pdf`
- Create: `instructor-materials/hw1/release/test_brief.py`

**Interfaces:**
- Consumes:
  - `briefs/scan/*.toml` (Task 4), `config.example.toml` (Task 4), `briefs/report.example.json` (Task 3);
  - the measured counts and the answer-key path (Task 2, `RESULTS.md`);
  - `contract.*`.
- Produces: the handout.

- [ ] **Step 1: Write the failing tests**

`instructor-materials/hw1/release/test_brief.py`:

```python
import re

import pytest

from contract import (CYBERBIRD_TRACE_URL, CYBERBIRD_TRAJECTORY_URL, CYBERBIRD_URL,
                      FORBIDDEN_STRINGS, HW1_REPO, README_CHECK_IDS, README_H2, RUBRIC_IDS,
                      RUN_H3, TARGETS, TRACE_KINDS)

TEX = HW1_REPO / "briefs/hw1.tex"
PDF = HW1_REPO / "briefs/hw1.pdf"


@pytest.fixture(scope="module")
def tex():
    return TEX.read_text()


def test_layout_packages(tex):
    assert re.search(r"\\documentclass\[[^\]]*letterpaper[^\]]*\]\{article\}", tex)
    assert r"\usepackage[margins=tight]{savetrees}" in tex


def test_required_scan_scope_section_includes_the_three_files(tex):
    assert "Required scan scope for each target" in tex
    for name in TARGETS:
        assert rf"\lstinputlisting{{scan/{name}.toml}}" in tex


def test_config_and_example_are_included_not_copied(tex):
    assert r"\lstinputlisting{../config.example.toml}" in tex
    assert r"\lstinputlisting{report.example.json}" in tex


@pytest.mark.parametrize("name", list(TARGETS))
def test_targets_pinned(tex, name):
    t = TARGETS[name]
    assert t["commit"] in tex and t["url"] in tex
    assert re.search(rf"{t['expected_alerts']}\s+alerts", tex), f"{name} count"


def test_cli_contract(tex):
    assert "--input" in tex and "--output" in tex and "--config" in tex
    assert "report.json" in tex and "trace.jsonl" in tex


def test_cyberbird_reference(tex):
    assert CYBERBIRD_URL in tex
    for name in ["resolve", "AgentWorkspace", "WITHHELD_GLOBS"]:
        assert name in tex


def test_trace_contract(tex):
    assert "Trace and trajectory" in tex
    assert CYBERBIRD_TRACE_URL in tex and CYBERBIRD_TRAJECTORY_URL in tex
    for kind in TRACE_KINDS:
        assert kind in tex, kind
    for field in ["step", "run_id", "alert_id", "usage_total", "alert_status"]:
        assert field in tex, field
    assert "sequenceDiagram" in tex


def test_withholding_requirements(tex):
    for s in [".git/", "expectedresults", "BenchmarkTest"]:
        assert s in tex


def test_rubric_has_every_item(tex):
    for item in RUBRIC_IDS:
        assert re.search(rf"(^|[^A-Za-z0-9]){item}([^0-9]|$)", tex, flags=re.M), item


def test_readme_contract_reproduced(tex):
    for h in README_H2:
        assert f"## {h}" in tex, h
    for h in RUN_H3:
        assert f"### {h}" in tex, h
    for r in README_CHECK_IDS:
        assert re.search(rf"\b{r}\b", tex), r


def test_dates_and_policy(tex):
    for s in ["September 25, 2026", "October 16, 2026", "11:59"]:
        assert s in tex
    assert "consult" in tex.lower()


@pytest.mark.parametrize("s", FORBIDDEN_STRINGS)
def test_no_forbidden_strings(tex, s):
    assert s not in tex


def test_pdf_built_and_fresh():
    assert PDF.exists(), "run: cd briefs && tectonic -X compile hw1.tex"
    inputs = [TEX, HW1_REPO / "config.example.toml", HW1_REPO / "briefs/report.example.json",
              *(HW1_REPO / f"briefs/scan/{n}.toml" for n in TARGETS)]
    stale = [p.name for p in inputs if p.stat().st_mtime > PDF.stat().st_mtime]
    assert stale == [], f"PDF older than {stale}; rebuild"
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `cd /Users/rkrsn/COMSE6998-019 && uv run --python 3.12 --with pytest --with jsonschema pytest instructor-materials/hw1/release/test_brief.py -q`

Expected: errors, with `FileNotFoundError: .../briefs/hw1.tex`.

- [ ] **Step 3: Load the writing skill**

Invoke the `orwell:academic` skill and follow it for all prose in this task. The spec is the source for every claim. Do not add claims about the targets, counts or tools that the spec and `RESULTS.md` do not support.

- [ ] **Step 4: Write the preamble and the fixed technical blocks**

`briefs/hw1.tex` starts with this preamble, used exactly as written:

```latex
% HW1 brief: COMS E6998-019, Design of Production Agentic Systems.
% Build: cd briefs && tectonic -X compile hw1.tex
\documentclass[10pt,letterpaper]{article}
\usepackage[margins=tight]{savetrees}
\usepackage{booktabs,tabularx,array,enumitem,xcolor,listings}
\usepackage[breakable]{tcolorbox}
\usepackage[hidelinks]{hyperref}
\setlist{nosep,leftmargin=*}
\renewcommand\tabularxcolumn[1]{>{\raggedright\arraybackslash}p{#1}}
\lstset{basicstyle=\ttfamily\small,columns=fullflexible,keepspaces=true,
  breaklines=true,frame=single,framerule=0.3pt,upquote=true}
\newtcolorbox{required}[1]{enhanced,breakable,colback=red!3,colframe=red!60!black,
  title={#1},fonttitle=\bfseries}
\title{HW1: A Bounded Agent for Bandit Alert Triage}
\author{COMS E6998 Section 019, Fall 2026 · Design of Production Agentic Systems\\
  Instructor: Rahul Krishna · TA: In Keun Kim}
\date{Released Friday, September 25, 2026 · Due Friday, October 16, 2026, before 11:59 p.m.}
\begin{document}
\maketitle
```

Sections, in this order. Each row gives the spec section to draft from, and what must appear verbatim:

| § | Section title | Draft from | Must include verbatim or as shown |
|---|---|---|---|
| 1 | Overview | spec §1, §2, §3 | A table of logistics: released and due dates; weight "20% of the course grade, marked out of 20"; "Team assignment"; late days "6 per student per semester, at most 3 on one assignment; each extends the deadline by 24 hours". The sentence that teams may consult the instructors as often as they like. |
| 2 | What you build | spec §2 | The two stages (discovery with Bandit 1.9.4 at MEDIUM+, and triage to 1 or 0 with a rationale and line evidence). No starter code; any language; Bandit needs Python 3.12; target code is read, never installed or run. |
| 3 | Targets | spec §4.2 | A table of the three targets with URL, full commit, role (development or held out) and alert count written as `N alerts`, using the counts from `RESULTS.md`. OWASP's answer key is open to teams and is the development set. **Your agent may not read it.** Radicale and SGLang are held out and scored by staff. Name neither held-out answer key, and no CVE ids. |
| 4 | Required scan scope for each target | spec §4.3 | Inside `\begin{required}{Required scan scope for each target}`: one sentence saying the blocks are mandatory and unchanged, that `paths` and `exclude` are globs relative to `--input` which the Bandit wrapper expands, and one `\lstinputlisting{scan/<name>.toml}` per target, each titled with the target and `N alerts`. |
| 5 | Interface | spec §4.1, §4.4 | The CLI line in a `lstlisting`; `\lstinputlisting{../config.example.toml}`; the rule that the budget covers the whole run and that unclassified alerts get `budget_exhausted` rows. |
| 6 | Output | spec §4.5 | `\lstinputlisting{report.example.json}`, captioned as a format illustration whose labels are not answers; the five rules from §4.5; `report.schema.json` is normative. |
| 7 | Workspace and withholding | spec §4.6 | The four requirements. The cyberbird reference as `\url{` + `CYBERBIRD_URL` + `}`, naming `resolve`, `AgentWorkspace` and `WITHHELD_GLOBS`. The OWASP answer-key path from `RESULTS.md`, `.git/`, and `BenchmarkTest` siblings. |
| 8 | Trace and trajectory | spec §4.8 | The format rules; the `kind` table with required fields; the six invariants; the trajectory command. The cyberbird references as `\url{` + `CYBERBIRD_TRACE_URL` + `}` and `\url{` + `CYBERBIRD_TRAJECTORY_URL` + `}`, naming `Trace`, `EventKind`, `TerminalStatus` and `Usage`. |
| 9 | Rubric | spec §5 | Three tables (A, B, C), each row id and item text as in spec §5, with part totals 7, 10 and 3. The three grading notes. |
| 10 | README contract | spec §4.7 | The format rules; the eleven required sections table with each heading written as `\texttt{\#\# Team}` and so on; the Run `\#\#\#` subsections; the R1 to R11 table; "How the checks are used". Tell teams to start from `README.template.md`. |
| 11 | Deliverables | spec §6 | The bullet list. |
| 12 | Academic integrity and AI tools | spec §2 last paragraph, plus the text below | See below. |

The test searches the source for `## Team` and similar. The source must contain those characters, so write the headings in a `lstlisting` block, for example:

```latex
\begin{lstlisting}
## Team
## Requirements
## Setup
## Fetch targets
## Configs
## Run
### Radicale
### SGLang
### OWASP BenchmarkPython
### Budget cutoff
## Outputs
## Validate
## Trajectory
## Rubric map
## Known issues
\end{lstlisting}
```

Section 11 starts from the current handout's policy, preserved here because Task 1 deletes `ASSIGNMENT.md`:

> AI assistants may be used to learn, debug your own code, review a design, or provide scoped autocomplete. Do not hand the assignment to an agent and submit the result. You remain responsible for every line you submit. Every team member must be able to explain the entire submission; the individual exams test this.

Add the spec §2 policy to it:
- agents may not generate or modify the target code;
- the LLM-use guideline is strictly enforced;
- LLM use is for learning.

Close with `\end{document}`.

- [ ] **Step 5: Build the PDF**

Run: `cd /Users/rkrsn/COMSE6998-019/hw1-agent-architectures/briefs && tectonic -X compile hw1.tex`

The first run downloads the TeX bundle, which can take several minutes. Expected: `Writing 'hw1.pdf'`, with no errors.

Pre-checked on 2026-09-24: tectonic accepts `margins=tight` and resolves `../config.example.toml` without extra flags. (`margins=extreme` is not a valid savetrees value.)

Open the PDF and check:
- every listing fits the text width;
- the red "Required scan scope for each target" box shows three blocks;
- no table overflows the margins.

- [ ] **Step 6: Run the tests and confirm they pass**

Run: the command from Step 2. Expected: all pass.

- [ ] **Step 7: Run the prose self-audit**

Re-read the prose sections against the `orwell:academic` checklist. Also check that every claim about the targets, counts or tools matches the spec or `RESULTS.md`. Rebuild the PDF after any edit, and rerun the tests.

- [ ] **Step 8: Commit both repos**

```sh
cd /Users/rkrsn/COMSE6998-019/hw1-agent-architectures
git add briefs/hw1.tex briefs/hw1.pdf
git commit -m "Add HW1 brief (LaTeX)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
cd /Users/rkrsn/COMSE6998-019/instructor-materials
git add hw1/release/test_brief.py
git commit -m "HW1 release checks: brief

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: The top-level README and the full release check

**Files:**
- Modify: `hw1-agent-architectures/README.md` (full rewrite)
- Modify: `instructor-materials/hw1/release/test_layout.py` (add a completeness test)
- Modify: `hw1-agent-architectures/docs/superpowers/specs/2026-09-24-hw1-redesign-design.md` (status line)

**Interfaces:**
- Consumes: `contract.ALLOWED_FILES`, `contract.FORBIDDEN_STRINGS`

- [ ] **Step 1: Add the failing completeness tests**

Append to `test_layout.py`:

```python
import pytest

from contract import FORBIDDEN_STRINGS


def test_every_allowed_file_exists():
    missing = sorted(f for f in ALLOWED_FILES if not (HW1_REPO / f).exists())
    assert missing == [], missing


def test_readme_points_to_brief_and_lists_files():
    text = (HW1_REPO / "README.md").read_text()
    assert "briefs/hw1.pdf" in text
    for f in ["README.template.md", "config.example.toml", "report.schema.json"]:
        assert f in text
    assert "uv sync" not in text and "triage" not in text   # nothing left from the old starter


@pytest.mark.parametrize("s", FORBIDDEN_STRINGS)
def test_readme_has_no_forbidden_strings(s):
    assert s not in (HW1_REPO / "README.md").read_text()
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `cd /Users/rkrsn/COMSE6998-019 && uv run --python 3.12 --with pytest --with jsonschema pytest instructor-materials/hw1/release/test_layout.py -q`

Expected: `test_readme_points_to_brief_and_lists_files` fails, because the old README mentions `uv sync` and `triage`.

- [ ] **Step 3: Rewrite `README.md`**

```markdown
# hw1-agent-architectures

COMS E6998-019 HW1: build an agent that scans a pinned Python repository with
Bandit and labels each alert. The assignment is in
[briefs/hw1.pdf](briefs/hw1.pdf) (source: `briefs/hw1.tex`).

There is no starter code. You design and write every part of the agent.

| File | What it is |
|---|---|
| `briefs/hw1.pdf` | The assignment brief |
| `briefs/scan/*.toml` | The required `[scan]` block for each target |
| `briefs/report.example.json` | An example `report.json` (format only; its labels are not answers) |
| `config.example.toml` | The config your agent must read |
| `report.schema.json` | JSON Schema your `report.json` must validate against |
| `README.template.md` | Copy to `README.md` in your submission and fill in; it is graded |

Clone targets into `targets/` and write runs to `runs/`. Both are git-ignored.
```

Leave `docs/superpowers/` in place. Whether it ships to students is a staff decision at merge time (see Staff actions).

- [ ] **Step 4: Update the spec status line**

In the spec, replace `Status: approved in brainstorming, awaiting spec review` with `Status: approved; implemented on branch hw1-redesign`.

- [ ] **Step 5: Run the full release check**

Run: `cd /Users/rkrsn/COMSE6998-019 && uv run --python 3.12 --with pytest --with jsonschema pytest instructor-materials/hw1/release -q`

Expected: every test passes, with 0 failures and 0 errors. Paste the summary line into the task report.

- [ ] **Step 6: Commit both repos**

```sh
cd /Users/rkrsn/COMSE6998-019/hw1-agent-architectures
git add README.md docs/superpowers/specs/2026-09-24-hw1-redesign-design.md
git commit -m "Rewrite README as a pointer to the brief

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
cd /Users/rkrsn/COMSE6998-019/instructor-materials
git add hw1/release/test_layout.py
git commit -m "HW1 release checks: completeness

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

## Staff actions (not agent tasks)

These need a human decision or credentials. They are listed so that nothing in spec §9 or §10 is dropped.

1. **Spec §9 check 6.** Label the 10 Radicale alerts (1 or 0, each with a rationale) and store the labels in `instructor-materials/hw1/answer-keys/radicale.json`.
2. **Spec §9 check 3.** Confirm that `github.com/comse6998-019/cyberbird` is visible to students (public, or shared with the class). The commit `cf7e96c` is pushed and contains the named symbols.
3. **Before release:** decide whether `docs/superpowers/` ships in the student repo or is removed at merge.
4. **Merge and push:** `hw1-redesign` into `main` in `hw1-agent-architectures`; push `instructor-materials`.
5. **Spec §10:** update the course site's HW1 text (Semgrep, grading criteria) and the due dates in `course_structure.md` and the Canvas syllabus.
6. **Follow-up:** write the README grading skill. It applies checks R1 to R10 from spec §4.7 and can reuse `contract.README_H2`, `RUN_H3` and `RUBRIC_IDS`.
