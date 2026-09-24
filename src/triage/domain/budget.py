from __future__ import annotations

from triage import StudentTODO
from triage.domain.model import Admission, LedgerEntry, TokenCount, Usage


class TokenBudget:
    """Per-investigation token budget (ASSIGNMENT.md, Part 3)."""

    def __init__(self, budget_tokens: int, output_allowance: int) -> None:
        self.budget_tokens = budget_tokens
        self.output_allowance = output_allowance
        self.ledger: list[LedgerEntry] = []

    @property
    def remaining(self) -> int:
        """budget_tokens minus everything charged so far."""
        # TODO(student): budget policy.
        raise StudentTODO("triage.domain.budget.TokenBudget.remaining")

    def admit(self, call_index: int, input_estimate: TokenCount) -> Admission:
        """Decide whether the next call is affordable. Charges nothing."""
        # TODO(student): pre-call admission with the output allowance.
        raise StudentTODO("triage.domain.budget.TokenBudget.admit")

    def reconcile(self, admission: Admission, usage: Usage | None) -> LedgerEntry:
        """Charge one completed call, append it to the ledger, and return it. ValueError if not admitted."""
        # TODO(student): post-call reconciliation of reported usage.
        raise StudentTODO("triage.domain.budget.TokenBudget.reconcile")
