from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from conftest import ROOT, head
from pydantic import ValidationError

from triage import StudentTODO
from triage.application import intake
from triage.domain.events import (
    ModelCallAdmitted,
    ModelCallCompleted,
    ModelCallRejected,
    ModelCallRequested,
    RunStarted,
    RunTerminated,
)
from triage.domain.model import BUDGET_EXHAUSTED, EvidenceRef, Finding, TokenCount, Usage, Verdict
from triage.infrastructure.eventlog import TraceWriter, read_trace
from triage.infrastructure.providers import RecordingProvider, Script, ScriptedProvider, ScriptExhausted
from triage.infrastructure.rundir import summarize
from triage.infrastructure.settings import load_config
from triage.infrastructure.target import (
    Selector,
    TargetError,
    check_location,
    load_selection,
    load_targets,
    raw_matches,
    select_alert,
)
from triage.interfaces.cli import build_parser, main

TARGETS = ROOT / "data/targets.json"
SELECTION = load_selection(ROOT / "data/selected_alerts.json")
EXHAUSTION_SCRIPT = ROOT / "data/provider_scripts/radicale-exhaustion.json"
CHECKOUT = ROOT / "targets/radicale"


def test_manifest_pins_full_commits() -> None:
    targets = load_targets(TARGETS)
    assert {t.role for t in targets.values()} == {"primary", "backup"}
    assert all(len(t.commit) == 40 for t in targets.values())


def test_each_selection_names_exactly_one_raw_result() -> None:
    assert SELECTION.experiment in {s.key for s in SELECTION.alerts}
    for sel in SELECTION.alerts:
        raw = json.loads((ROOT / f"data/scans/radicale/{sel.scanner}.json").read_text())
        assert len(raw_matches(raw, sel)) == 1, sel.key


@pytest.mark.skipif(not (CHECKOUT / ".git").exists(), reason="run `uv run triage fetch-target` first")
def test_selections_exist_at_the_pinned_commit() -> None:
    commit = load_targets(TARGETS)[SELECTION.target].commit
    for sel in SELECTION.alerts:
        check_location(CHECKOUT, commit, sel.path, sel.line, sel.line)


def test_check_location_rejects_bad_locations(mini_repo: Path) -> None:
    commit = head(mini_repo)
    assert len(check_location(mini_repo, commit, "app/server.py", 7, 9)) == 64
    bad = (("../secret.txt", 1, 1), ("app/missing.py", 1, 1), ("app/server.py", 9, 10), ("app/server.py", 0, 1))
    for path, start, end in bad:
        with pytest.raises(TargetError):
            check_location(mini_repo, commit, path, start, end)


def test_select_alert_needs_exactly_one_match() -> None:
    def alert(alert_id: str, scanner: str, rule_id: str, start: int, end: int) -> SimpleNamespace:
        return SimpleNamespace(alert_id=alert_id, scanner=scanner, rule_id=rule_id, commit="a" * 40,
                               path="app/server.py", start_line=start, end_line=end)

    sel = Selector(key="k", scanner="bandit", rule_id="B602", path="app/server.py", line=9)
    alerts = [alert("1", "bandit", "bandit:B602", 7, 9), alert("2", "semgrep", "subprocess-shell-true", 9, 9),
              alert("3", "bandit", "B404", 2, 2)]
    assert select_alert(alerts, sel).alert_id == "1"
    with pytest.raises(TargetError):
        select_alert([*alerts, alert("4", "bandit", "B602", 9, 9)], sel)
    with pytest.raises(TargetError):
        select_alert(alerts[1:], sel)


def test_finding_needs_evidence_and_ordered_ranges() -> None:
    ref = dict(commit="a" * 40, path="x.py", note="n")
    with pytest.raises(ValidationError):
        Finding(alert_id="a", verdict=Verdict.OTHER, rationale="r", evidence=[], uncertainty="u")
    with pytest.raises(ValidationError):
        EvidenceRef(start_line=5, end_line=4, **ref)
    assert {v.value for v in Verdict} == {"TP", "FP", "Other"}
    assert BUDGET_EXHAUSTED not in {v.value for v in Verdict}


def test_configs_load_and_overrides_apply() -> None:
    config = load_config(ROOT / "configs/scripted.toml", budget_tokens=1000)
    assert (config.budget_tokens, config.output_allowance, config.provider) == (1000, 20, "scripted")
    with pytest.raises(ValidationError):  # live.toml ships without a model on purpose
        load_config(ROOT / "configs/live.toml")


def test_trace_roundtrip(tmp_path: Path) -> None:
    writer = TraceWriter(tmp_path / "trace.jsonl", "run1")
    writer.emit(RunStarted(alert_id="a", commit="a" * 40, budget_tokens=100, output_allowance=20,
                           max_model_calls=5, provider="scripted"))
    writer.emit(ModelCallRejected(call_index=2, required=35, remaining=30, reason="insufficient budget"))
    writer.emit(RunTerminated(reason=BUDGET_EXHAUSTED, verdict=None, model_calls_issued=2, tokens_charged=70, remaining=30))
    records = read_trace(tmp_path / "trace.jsonl")
    assert [r["seq"] for r in records] == [0, 1, 2]
    assert records[-1]["reason"] == "budget_exhausted"
    (tmp_path / "trace.jsonl").write_text('{"type": "NotAnEvent"}\n')
    with pytest.raises(ValidationError):
        read_trace(tmp_path / "trace.jsonl")


def test_exhaustion_script_reproduces_course_table() -> None:
    """Budget 100, allowance 20: admit 40 (charge 30), admit 45 (charge 40), refuse 35 with 30 left."""
    steps = Script.model_validate_json(EXHAUSTION_SCRIPT.read_text()).steps
    remaining, allowance = 100, 20
    for step in steps[:2]:
        assert step.preflight_input_tokens + allowance <= remaining
        remaining -= step.usage.input_tokens + step.usage.output_tokens
    assert remaining == 30 and steps[2].preflight_input_tokens + allowance == 35


def test_scripted_provider_replays_without_enforcing_budget(tmp_path: Path) -> None:
    provider = ScriptedProvider.from_file(EXHAUSTION_SCRIPT)
    assert provider.count_input_tokens([], []).tokens == 20
    assert provider.count_input_tokens([], []).tokens == 20  # counting does not consume a step
    recorder = RecordingProvider(provider, tmp_path / "boundary.jsonl")
    for _ in range(3):
        recorder.invoke([], [], max_output_tokens=0)  # a provider never refuses on budget grounds
    assert provider.issued == 3 and len(recorder.calls) == 3
    assert len((tmp_path / "boundary.jsonl").read_text().splitlines()) == 3
    with pytest.raises(ScriptExhausted):
        recorder.invoke([], [], max_output_tokens=20)


def test_summarize_reconciles_the_trace_with_the_boundary_log(tmp_path: Path) -> None:
    """The projection behind `triage summarize`: admitted calls must equal issued calls, with one RunTerminated."""
    terminated = RunTerminated(reason="finished", verdict=None, model_calls_issued=1, tokens_charged=30, remaining=70)

    def one_call_run(run_dir: Path) -> tuple[TraceWriter, RecordingProvider]:
        run_dir.mkdir()
        (run_dir / "meta.json").write_text(json.dumps({"measurement": "synthetic (scripted provider)"}))
        trace = TraceWriter(run_dir / "trace.jsonl", "run1")
        trace.emit(RunStarted(alert_id="a", commit="a" * 40, budget_tokens=100, output_allowance=20,
                              max_model_calls=5, provider="scripted"))
        trace.emit(ModelCallRequested(call_index=0, input_estimate=TokenCount(tokens=20, kind="bound"), output_allowance=20))
        trace.emit(ModelCallAdmitted(call_index=0, reserved=40, remaining_before=100))
        trace.emit(ModelCallCompleted(call_index=0, usage=Usage(input_tokens=20, output_tokens=10), charged=30,
                                      remaining_after=70, latency_s=0.0, requested_tools=["search_repo"]))
        trace.emit(terminated)
        recorder = RecordingProvider(ScriptedProvider.from_file(EXHAUSTION_SCRIPT), run_dir / "boundary.jsonl")
        recorder.invoke([], [], max_output_tokens=20)
        return trace, recorder

    _, recorder = one_call_run(tmp_path / "extra-call")
    summary = summarize(tmp_path / "extra-call")
    assert (summary.issued, summary.tokens_reported, summary.terminal_reasons, summary.reconciles) == (1, 30, ["finished"], True)
    recorder.invoke([], [], max_output_tokens=20)  # issued but never admitted in the trace
    assert not summarize(tmp_path / "extra-call").reconciles

    trace, _ = one_call_run(tmp_path / "extra-end")
    trace.emit(terminated)  # admitted still equals issued, but the run ends twice
    assert not summarize(tmp_path / "extra-end").reconciles


@pytest.mark.parametrize(
    "command", [[], ["fetch-target"], ["validate-fixtures"], ["intake"], ["investigate"], ["run-set"], ["summarize"]]
)
def test_cli_help(command: list[str]) -> None:
    with pytest.raises(SystemExit) as exit_:
        build_parser().parse_args([*command, "--help"])
    assert exit_.value.code == 0


def test_cli_reports_student_todo_instead_of_crashing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def stub(*_: object) -> None:
        raise StudentTODO("triage.application.intake.normalize_bandit")

    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(intake, "normalize_bandit", stub)
    with pytest.raises(SystemExit) as exit_:
        main(["intake", "--out", str(tmp_path / "alerts")])
    assert "student TODO" in str(exit_.value.code)
    assert not (tmp_path / "alerts").exists()
