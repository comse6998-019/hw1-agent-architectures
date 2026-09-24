from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from triage import StudentTODO
from triage.application import intake
from triage.domain.alert import Alert
from triage.domain.model import RepoSnapshot, ScannerProvenance
from triage.infrastructure.target import Selector, select_alert

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if (call.when == "call" and call.excinfo is not None and call.excinfo.errisinstance(StudentTODO)
            and "acceptance" in item.path.parts):
        report.outcome = "skipped"
        report.wasxfail = f"student TODO not implemented: {call.excinfo.value}"


@pytest.fixture
def mini_repo(tmp_path: Path) -> Path:
    """A committed copy of the synthetic repo, plus a symlink that points outside it."""
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURES / "mini_repo", repo)
    (tmp_path / "secret.txt").write_text("hw1-secret-7f3a1c\n")  # a token no refusal message would contain
    (repo / "app" / "escape.txt").symlink_to(tmp_path / "secret.txt")
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
           "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null"]  # ignore global signing and hooks
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "fixture"], check=True)
    return repo


def head(repo: Path) -> str:
    out = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def mini_alert(repo: Path) -> Alert:
    """The B602 alert in the synthetic repo, built by *your* normalize_bandit from real Bandit output."""
    snapshot = RepoSnapshot(name="mini", url="file://synthetic", commit=head(repo))
    scanner = ScannerProvenance(name="bandit", version="1.9.4", command="bandit -q -r app -f json (synthetic test repo)")
    raw = json.loads((FIXTURES / "mini_repo_bandit.json").read_text())
    alerts = intake.normalize_bandit(raw, snapshot, scanner)
    return select_alert(alerts, Selector(key="mini", scanner="bandit", rule_id="B602", path="app/server.py", line=9))
