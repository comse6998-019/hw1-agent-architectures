from __future__ import annotations

from pathlib import Path

from triage import StudentTODO
from triage.domain.model import Finding


def resolve_evidence(finding: Finding, repo_root: Path, commit: str) -> list[str]:
    """Return the reasons the finding's evidence does not resolve; [] means it resolves (ASSIGNMENT.md, Part 4)."""
    # TODO(student): implement evidence resolution.
    raise StudentTODO("triage.application.evidence.resolve_evidence")
