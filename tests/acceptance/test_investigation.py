from __future__ import annotations

from pathlib import Path

from conftest import mini_alert

from triage.application.agent import investigate
from triage.application.config import RunConfig
from triage.domain.model import BUDGET_EXHAUSTED, Usage
from triage.infrastructure.eventlog import TraceWriter, read_trace
from triage.infrastructure.providers import RecordingProvider, Script, ScriptedProvider, ScriptStep


def step(pre: int, used_in: int, used_out: int, name: str, **args: object) -> ScriptStep:
    return ScriptStep(preflight_input_tokens=pre, usage=Usage(input_tokens=used_in, output_tokens=used_out),
                      tool_calls=[{"name": name, "args": args}])


def submit(pre: int, start: int, end: int) -> ScriptStep:
    return step(pre, pre, 10, "submit_finding", verdict="Other", rationale="SCRIPTED PLACEHOLDER",
                evidence=[{"path": "app/server.py", "start_line": start, "end_line": end, "note": "placeholder"}],
                uncertainty="scripted")


# Mirrors the course table: 20+20 then 25+20 admitted (charged 30, 40); 15+20 needs 35.
COURSE_STEPS = [
    step(20, 20, 10, "search_repo", pattern="HOOK"),
    step(25, 25, 15, "read_file", path="app/server.py", start_line=1, end_line=9),
    submit(15, 7, 9),
]


def run(repo: Path, tmp: Path, steps: list[ScriptStep], budget: int, max_calls: int = 10):
    alert = mini_alert(repo)
    provider = ScriptedProvider(Script(description="synthetic", steps=steps))
    recorder = RecordingProvider(provider, tmp / "boundary.jsonl")
    config = RunConfig(budget_tokens=budget, output_allowance=20, max_model_calls=max_calls,
                       provider="scripted", script=Path("unused.json"))
    result = investigate(alert, repo, config, recorder, TraceWriter(tmp / "trace.jsonl", "test-run"))
    return alert, result, provider, recorder, read_trace(tmp / "trace.jsonl")


def types(events: list[dict]) -> list[str]:
    return [e["type"] for e in events]


def test_control_budget_admits_all_three_calls(mini_repo: Path, tmp_path: Path) -> None:
    alert, result, provider, recorder, events = run(mini_repo, tmp_path, COURSE_STEPS, budget=1000)
    assert result.finding is not None and result.terminal_reason != BUDGET_EXHAUSTED
    assert provider.issued == 3 == len(recorder.calls) == result.model_calls_issued
    assert all(c["max_output_tokens"] == 20 for c in recorder.calls)
    assert [e.charged for e in result.ledger] == [30, 40, 25]
    assert all(ref.commit == alert.commit for ref in result.finding.evidence)
    assert types(events)[0] == "RunStarted" and types(events)[-1] == "RunTerminated"
    assert types(events).count("RunStarted") == 1 == types(events).count("RunTerminated")
    assert types(events).count("ModelCallRequested") == 3 == types(events).count("ModelCallCompleted")
    assert types(events).count("ModelCallAdmitted") == 3
    assert [e["tool"] for e in events if e["type"] == "ToolCallCompleted"] == ["search_repo", "read_file"]


def test_observations_reach_the_next_model_call(mini_repo: Path, tmp_path: Path) -> None:
    """The markers come from app/settings.py, which the alert does not point to."""
    steps = [
        step(20, 20, 10, "search_repo", pattern="HOOK"),
        step(20, 20, 10, "read_file", path="app/settings.py", start_line=1, end_line=2),
        *COURSE_STEPS[1:],  # read the cited lines, then submit
    ]
    _, _, provider, _, _ = run(mini_repo, tmp_path, steps, budget=1000)
    first, second, third = ("".join(str(m.content) for m in req).replace(" ", "") for req in provider.requests[:3])
    assert "app/settings.py:2" not in first and "app/settings.py:2" in second  # the search result
    assert "2|HOOK" not in second and "2|HOOK" in third  # the numbered read_file result


def test_exhaustion_refuses_before_the_provider(mini_repo: Path, tmp_path: Path) -> None:
    _, result, provider, recorder, events = run(mini_repo, tmp_path, COURSE_STEPS, budget=100)
    assert provider.issued == 2 == len(recorder.calls)  # the decisive observation
    assert result.terminal_reason == BUDGET_EXHAUSTED and result.finding is None
    assert [e.charged for e in result.ledger] == [30, 40]
    rejected = [e for e in events if e["type"] == "ModelCallRejected"]
    assert len(rejected) == 1 and rejected[0]["remaining"] == 30 and rejected[0]["required"] > 30  # 15 + 20 at least
    after = types(events)[types(events).index("ModelCallRejected"):]
    assert "ModelCallCompleted" not in after and after[-1] == "RunTerminated"
    assert types(events)[0] == "RunStarted" and types(events).count("RunStarted") == 1 == types(events).count("RunTerminated")
    assert types(events).count("ModelCallRequested") == 3 and types(events).count("ModelCallCompleted") == 2


def test_zero_budget_issues_no_calls(mini_repo: Path, tmp_path: Path) -> None:
    _, result, provider, _, events = run(mini_repo, tmp_path, COURSE_STEPS, budget=0)
    assert provider.issued == 0
    assert result.terminal_reason == BUDGET_EXHAUSTED
    assert "ModelCallRejected" in types(events) and types(events)[-1] == "RunTerminated"
    assert types(events)[0] == "RunStarted" and types(events).count("RunStarted") == 1 == types(events).count("RunTerminated")
    assert types(events).count("ModelCallRequested") == 1 and types(events).count("ModelCallAdmitted") == 0


def test_missing_usage_is_charged_in_the_loop(mini_repo: Path, tmp_path: Path) -> None:
    """Whether the run continues after missing usage is your policy; only the charge is checked."""
    first = ScriptStep(preflight_input_tokens=20, usage=None, tool_calls=[{"name": "search_repo", "args": {"pattern": "HOOK"}}])
    _, result, _, _, events = run(mini_repo, tmp_path, [first, *COURSE_STEPS[1:]], budget=1000)
    assert result.ledger[0].usage is None and result.ledger[0].charged > 0
    completed = [e for e in events if e["type"] == "ModelCallCompleted"]
    assert completed[0]["usage"] is None and completed[0]["charged"] == result.ledger[0].charged


def test_step_limit_is_not_the_budget(mini_repo: Path, tmp_path: Path) -> None:
    _, result, provider, _, _ = run(mini_repo, tmp_path, COURSE_STEPS, budget=1000, max_calls=2)
    assert provider.issued == 2
    assert result.terminal_reason != BUDGET_EXHAUSTED and result.finding is None


def test_unresolvable_evidence_is_never_accepted(mini_repo: Path, tmp_path: Path) -> None:
    steps = [*COURSE_STEPS[:2], submit(15, 50, 60), submit(15, 7, 9)]  # server.py has 9 lines; 7-9 were read
    _, result, _, _, events = run(mini_repo, tmp_path, steps, budget=1000)
    submitted = [e for e in events if e["type"] == "FindingSubmitted"]
    assert submitted and submitted[0]["accepted"] is False
    if result.finding is not None:  # retrying after a rejection is allowed
        assert all(ref.end_line <= 9 for ref in result.finding.evidence)


def test_refused_tool_requests_are_observations(mini_repo: Path, tmp_path: Path) -> None:
    steps = [
        step(20, 20, 10, "read_file", path="../secret.txt", start_line=1, end_line=5),
        step(20, 20, 10, "run_shell", cmd="cat ../secret.txt"),
        step(25, 25, 15, "read_file", path="app/server.py", start_line=1, end_line=9),
        submit(15, 7, 9),
    ]
    _, result, provider, _, events = run(mini_repo, tmp_path, steps, budget=1000)
    tools = [(e["tool"], e["ok"]) for e in events if e["type"] == "ToolCallCompleted"]
    assert tools == [("read_file", False), ("run_shell", False), ("read_file", True)]
    assert not any("hw1-secret-7f3a1c" in str(m.content) for req in provider.requests for m in req)
    assert result.finding is not None
