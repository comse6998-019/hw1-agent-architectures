from __future__ import annotations

from typing import Any

from triage import StudentTODO
from triage.domain.alert import Alert
from triage.domain.model import RepoSnapshot, ScannerProvenance


def normalize_bandit(raw: dict[str, Any], snapshot: RepoSnapshot, scanner: ScannerProvenance) -> list[Alert]:
    """One alert per Bandit result, in a deterministic order (ASSIGNMENT.md, Part 2)."""
    # TODO(student): normalize Bandit JSON into your contract.
    raise StudentTODO("triage.application.intake.normalize_bandit")


def normalize_semgrep(raw: dict[str, Any], snapshot: RepoSnapshot, scanner: ScannerProvenance) -> list[Alert]:
    """One alert per Semgrep result, in the same contract as normalize_bandit (ASSIGNMENT.md, Part 2)."""
    # TODO(student): normalize Semgrep JSON into the same contract.
    raise StudentTODO("triage.application.intake.normalize_semgrep")
