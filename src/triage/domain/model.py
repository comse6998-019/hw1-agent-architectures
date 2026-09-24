from __future__ import annotations

from enum import StrEnum
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

SHA1_PATTERN = r"^[0-9a-f]{40}$"

# The one terminal reason every team must use verbatim. The rest of your
# terminal vocabulary, and what an exhausted run returns, are your own.
BUDGET_EXHAUSTED = "budget_exhausted"


class RepoSnapshot(BaseModel):
    """One pinned revision of the target repository."""

    model_config = ConfigDict(frozen=True)

    name: str
    url: str
    commit: str = Field(pattern=SHA1_PATTERN)

    @property
    def snapshot_id(self) -> str:
        return f"{self.name}@{self.commit[:12]}"


class ScannerProvenance(BaseModel):
    """How a staff-pinned scan was produced. An input to your intake stage."""

    name: Literal["bandit", "semgrep"]
    version: str
    command: str
    ruleset_sha256: dict[str, str] = Field(default_factory=dict)


class AlertView(Protocol):
    """The attributes the CLI, the tests, and the grader read from your alert.

    Your contract (triage/domain/alert.py) decides everything else.
    """

    alert_id: str  # stable for the same claim on the same commit; only [A-Za-z0-9._-] (used as a file name)
    scanner: str  # "bandit" or "semgrep"
    rule_id: str  # contains the scanner's own rule id, e.g. "B602"
    commit: str  # the pinned target commit
    path: str  # repository-relative POSIX path
    start_line: int
    end_line: int


class Verdict(StrEnum):
    TP = "TP"
    FP = "FP"
    OTHER = "Other"


class EvidenceRef(BaseModel):
    """A line range at the pinned commit that a reviewer can open without the agent."""

    commit: str = Field(pattern=SHA1_PATTERN)
    path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    note: str

    @model_validator(mode="after")
    def _ordered(self) -> EvidenceRef:
        if self.end_line < self.start_line:
            raise ValueError("end_line precedes start_line")
        return self


class Finding(BaseModel):
    alert_id: str
    verdict: Verdict
    rationale: str = Field(min_length=1)
    evidence: list[EvidenceRef] = Field(min_length=1)
    uncertainty: str = Field(min_length=1, description="What static inspection did not establish.")


class Usage(BaseModel):
    """Provider-reported usage for one call.

    input_tokens follows LangChain's usage_metadata convention: all input tokens,
    including any read from or written to a prompt cache.
    """

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(default=0, ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)


class TokenCount(BaseModel):
    """A pre-call input-token figure and how much it can be trusted."""

    tokens: int = Field(ge=0)
    kind: Literal["exact", "bound", "estimate"]


class Admission(BaseModel):
    """One pre-call admission decision."""

    call_index: int = Field(ge=0)
    input_estimate: TokenCount
    output_allowance: int = Field(ge=0)
    remaining_before: int
    admitted: bool


class LedgerEntry(BaseModel):
    """One admitted call after reconciliation."""

    admission: Admission
    usage: Usage | None
    charged: int = Field(ge=0)
    remaining_after: int


class InvestigationResult(BaseModel):
    """What investigate() returns.

    terminal_reason uses your own vocabulary, except that a budget refusal must
    be BUDGET_EXHAUSTED. Add fields for your own outcomes (e.g. partial evidence).
    """

    model_config = ConfigDict(extra="allow")

    run_id: str
    alert_id: str
    commit: str = Field(pattern=SHA1_PATTERN)
    terminal_reason: str = Field(min_length=1)
    finding: Finding | None
    ledger: list[LedgerEntry]
    model_calls_issued: int = Field(ge=0)
    budget_tokens: int = Field(ge=0)
