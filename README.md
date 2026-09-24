# hw1-agent-architectures

Starter repository for COMS E6998-019 HW1: build a bounded, sequential agent
that triages static-analysis alerts against a pinned repository. See
[ASSIGNMENT.md](ASSIGNMENT.md) for the specification.

## Setup

Requires Git, `curl`, `shasum`, and [uv](https://docs.astral.sh/uv/); use
macOS, Linux, or WSL because the helper scripts use Bash. `uv` installs
Python 3.12 from `.python-version`.

```sh
uv sync --group scan
uv run triage fetch-target
scripts/scan_target.sh
uv run triage validate-fixtures --scans runs/scans/radicale
uv run pytest
```

For live runs, set `model` in `configs/live.toml`, add one provider
integration to the `live` extra, and, if the provider requires one, set its
API key (see `.env.example`):

```sh
uv add langchain-anthropic --optional live  # or langchain-openai / langchain-ollama
uv sync --group scan --extra live
```

Keep `--extra live` on later `uv sync` commands. Never commit API keys.

## Commands

`scripts/run_normal.sh` uses a live provider and may incur cost.

```sh
uv run triage intake --out runs/alerts/radicale
uv run triage investigate --select bandit-B602-lock --config configs/scripted.toml
scripts/run_exhaustion.sh
scripts/run_normal.sh
uv run triage summarize PATH_TO_RUN_DIR
```

## Student code

| Part | Files in `src/triage/` | Tests in `tests/acceptance/` |
|---|---|---|
| 1 | `application/tools.py` | `test_tools.py` |
| 2 | `domain/alert.py`, `application/intake.py` | `test_intake.py` |
| 3 | `domain/budget.py` | `test_budget.py` |
| 4 | `application/evidence.py` | `test_evidence.py` |
| 5 | `application/agent.py` | `test_investigation.py` |
| 6 | `application/pipeline.py` | `test_pipeline.py` |

All other files under `src/triage/` are staff code. `src/triage` uses the DDD
layers `domain`, `application`, `infrastructure`, and `interfaces`; each imports
only from itself and the layers before it, except for the package-level
`triage.StudentTODO` marker. An acceptance test stopped by `StudentTODO` is
reported as xfail; every other test failure is real.

## Outputs

With the shipped configs, generated artifacts go under git-ignored `runs/`.
See [ASSIGNMENT.md §4](ASSIGNMENT.md#4-deliverables) for what to submit.
