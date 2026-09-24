from __future__ import annotations

from pathlib import Path

from triage import StudentTODO
from triage.application.config import RunConfig
from triage.domain.alert import Alert
from triage.domain.model import InvestigationResult


def plan(alerts: list[Alert], config: RunConfig) -> list[Alert]:
    """Choose and order the small alert set to investigate (ASSIGNMENT.md, Part 6)."""
    # TODO(student): implement the planner.
    raise StudentTODO("triage.application.pipeline.plan")


def write_report(results: list[InvestigationResult], alerts: list[Alert], path: Path) -> None:
    """Write one human-readable report across the investigated alerts (ASSIGNMENT.md, Part 6)."""
    # TODO(student): implement the cross-alert report.
    raise StudentTODO("triage.application.pipeline.write_report")
