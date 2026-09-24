from __future__ import annotations

import operator
from pathlib import Path
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages

from triage import StudentTODO
from triage.application.config import RunConfig
from triage.application.ports import EventSink, ModelProvider
from triage.domain.alert import Alert
from triage.domain.model import Finding, InvestigationResult, LedgerEntry


class RunState(TypedDict, total=False):
    """A starting point for your run state; extend or replace it (ASSIGNMENT.md, Part 5)."""

    run_id: str
    alert: Alert
    messages: Annotated[list, add_messages]
    observations: Annotated[list[dict[str, Any]], operator.add]
    ledger: list[LedgerEntry]
    model_calls: int
    finding: Finding | None
    terminal_reason: str | None


def investigate(
    alert: Alert,
    repo_root: Path,
    config: RunConfig,
    provider: ModelProvider,
    trace: EventSink,
) -> InvestigationResult:
    """Run one bounded investigation of one alert and return its result (ASSIGNMENT.md, Part 5)."""
    # TODO(student): the reactive control loop, its state transitions, and tool dispatch.
    # TODO(student): your exhaustion outcome (what a BUDGET_EXHAUSTED run returns).
    raise StudentTODO("triage.application.agent.investigate")
