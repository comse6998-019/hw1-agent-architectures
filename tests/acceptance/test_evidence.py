from __future__ import annotations

from pathlib import Path

from conftest import head

from triage.application.evidence import resolve_evidence
from triage.domain.model import EvidenceRef, Finding, Verdict


def finding(commit: str, path: str = "app/server.py", start: int = 7, end: int = 9) -> Finding:
    ref = EvidenceRef(commit=commit, path=path, start_line=start, end_line=end, note="placeholder")
    return Finding(alert_id="a", verdict=Verdict.OTHER, rationale="placeholder", evidence=[ref], uncertainty="placeholder")


def test_resolvable_evidence_passes(mini_repo: Path) -> None:
    assert resolve_evidence(finding(head(mini_repo)), mini_repo, head(mini_repo)) == []


def test_unresolvable_evidence_is_reported(mini_repo: Path) -> None:
    commit = head(mini_repo)
    for bad in (
        finding(commit, start=8, end=12),  # app/server.py has 9 lines
        finding(commit, path="app/missing.py"),
        finding(commit, path="../secret.txt", start=1, end=1),
        finding(commit, path="app/escape.txt", start=1, end=1),  # symlink out of the repo
        finding("0" * 40),  # not the pinned commit
    ):
        assert resolve_evidence(bad, mini_repo, commit), bad.evidence[0]
