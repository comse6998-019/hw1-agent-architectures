from __future__ import annotations

import pytest

from triage.domain.budget import TokenBudget
from triage.domain.model import TokenCount, Usage


def bound(n: int) -> TokenCount:
    return TokenCount(tokens=n, kind="bound")


def test_course_table() -> None:
    """Budget 100, allowance 20: admit 40 (charge 30), admit 45 (charge 40), refuse 35 with 30 left."""
    budget = TokenBudget(budget_tokens=100, output_allowance=20)
    first = budget.admit(0, bound(20))
    assert first.admitted
    budget.reconcile(first, Usage(input_tokens=20, output_tokens=10))
    assert budget.remaining == 70
    second = budget.admit(1, bound(25))
    assert second.admitted
    budget.reconcile(second, Usage(input_tokens=25, output_tokens=15))
    assert budget.remaining == 30
    third = budget.admit(2, bound(15))
    assert not third.admitted and third.remaining_before == 30
    assert budget.remaining == 30  # a refusal charges nothing
    assert [e.charged for e in budget.ledger] == [30, 40]


def test_zero_budget_refuses_the_first_call() -> None:
    assert not TokenBudget(budget_tokens=0, output_allowance=20).admit(0, bound(1)).admitted


def test_admission_counts_the_output_allowance() -> None:
    assert TokenBudget(budget_tokens=100, output_allowance=20).admit(0, bound(60)).admitted
    assert not TokenBudget(budget_tokens=100, output_allowance=20).admit(0, bound(81)).admitted  # 81 fits; 81 + 20 does not


def test_reconcile_charges_reported_usage_not_the_estimate() -> None:
    budget = TokenBudget(budget_tokens=1000, output_allowance=100)
    entry = budget.reconcile(budget.admit(0, TokenCount(tokens=300, kind="estimate")), Usage(input_tokens=250, output_tokens=40))
    assert entry.charged == 290 and budget.remaining == 710


def test_missing_usage_is_not_zero() -> None:
    budget = TokenBudget(budget_tokens=1000, output_allowance=100)
    entry = budget.reconcile(budget.admit(0, bound(300)), None)
    assert entry.usage is None and entry.charged > 0 and budget.remaining < 1000


def test_overshoot_blocks_every_later_call() -> None:
    budget = TokenBudget(budget_tokens=1000, output_allowance=20)
    budget.reconcile(budget.admit(0, TokenCount(tokens=50, kind="estimate")), Usage(input_tokens=990, output_tokens=20))
    assert budget.remaining <= 0  # 1010 reported against a budget of 1000; leaves room for any estimate margin
    assert not budget.admit(1, bound(0)).admitted


def test_cannot_reconcile_a_refused_call() -> None:
    budget = TokenBudget(budget_tokens=10, output_allowance=20)
    refused = budget.admit(0, bound(5))
    with pytest.raises(ValueError):
        budget.reconcile(refused, Usage(input_tokens=5, output_tokens=5))
