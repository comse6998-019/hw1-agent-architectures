from __future__ import annotations

import json
from pathlib import Path

from conftest import ROOT

from triage.application import intake, pipeline
from triage.domain.alert import Alert
from triage.domain.model import BUDGET_EXHAUSTED, EvidenceRef, Finding, InvestigationResult, Verdict
from triage.infrastructure.settings import load_config
from triage.infrastructure.target import load_scanners, load_targets

SCANNERS = load_scanners(ROOT / "data/targets.json")
SNAPSHOT = load_targets(ROOT / "data/targets.json")["radicale"].snapshot


def radicale_alerts() -> list[Alert]:
    raw = json.loads((ROOT / "data/scans/radicale/bandit.json").read_text())
    return intake.normalize_bandit(raw, SNAPSHOT, SCANNERS["bandit"])


def test_plan_selects_a_small_subset_without_duplicates() -> None:
    alerts = radicale_alerts()
    chosen = pipeline.plan(alerts, load_config(ROOT / "configs/scripted.toml"))
    ids = [a.alert_id for a in chosen]
    assert ids and len(ids) == len(set(ids)) and set(ids) <= {a.alert_id for a in alerts}
    assert len(ids) < len(alerts)


def test_report_separates_verdicts_from_terminal_reasons(tmp_path: Path) -> None:
    first, second = radicale_alerts()[:2]
    ref = EvidenceRef(commit=SNAPSHOT.commit, path=first.path, start_line=first.start_line,
                      end_line=first.end_line, note="placeholder")
    results = [
        InvestigationResult(run_id="r1", alert_id=first.alert_id, commit=SNAPSHOT.commit, terminal_reason="finished",
                            ledger=[], model_calls_issued=3, budget_tokens=100,
                            finding=Finding(alert_id=first.alert_id, verdict=Verdict.OTHER, rationale="placeholder",
                                            evidence=[ref], uncertainty="placeholder")),
        InvestigationResult(run_id="r2", alert_id=second.alert_id, commit=SNAPSHOT.commit,
                            terminal_reason=BUDGET_EXHAUSTED, finding=None, ledger=[], model_calls_issued=2,
                            budget_tokens=100),
    ]
    pipeline.write_report(results, [first, second], tmp_path / "report.md")
    text = (tmp_path / "report.md").read_text()
    assert first.alert_id in text and second.alert_id in text
    assert BUDGET_EXHAUSTED in text and "Other" in text
