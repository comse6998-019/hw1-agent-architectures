from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from triage.domain.model import Finding, TokenCount, Usage, Verdict


class RunStarted(BaseModel):
    type: Literal["RunStarted"] = "RunStarted"
    alert_id: str
    commit: str
    budget_tokens: int
    output_allowance: int
    max_model_calls: int
    provider: str


class ModelCallRequested(BaseModel):
    type: Literal["ModelCallRequested"] = "ModelCallRequested"
    call_index: int
    input_estimate: TokenCount
    output_allowance: int


class ModelCallAdmitted(BaseModel):
    type: Literal["ModelCallAdmitted"] = "ModelCallAdmitted"
    call_index: int
    reserved: int  # input estimate plus output allowance, as your policy computes it
    remaining_before: int


class ModelCallRejected(BaseModel):
    type: Literal["ModelCallRejected"] = "ModelCallRejected"
    call_index: int
    required: int  # input estimate plus output allowance, as your policy computes it
    remaining: int  # budget left before this call
    reason: str


class ModelCallCompleted(BaseModel):
    type: Literal["ModelCallCompleted"] = "ModelCallCompleted"
    call_index: int
    usage: Usage | None
    charged: int
    remaining_after: int
    latency_s: float
    requested_tools: list[str]


class ToolCallCompleted(BaseModel):
    type: Literal["ToolCallCompleted"] = "ToolCallCompleted"
    tool: str
    args: dict[str, Any]
    ok: bool
    error: str | None = None
    result_chars: int
    latency_s: float


class FindingSubmitted(BaseModel):
    type: Literal["FindingSubmitted"] = "FindingSubmitted"
    finding: Finding
    accepted: bool
    rejection_reason: str | None = None


class RunTerminated(BaseModel):
    type: Literal["RunTerminated"] = "RunTerminated"
    reason: str  # your terminal vocabulary; a budget refusal is BUDGET_EXHAUSTED
    verdict: Verdict | None
    model_calls_issued: int
    tokens_charged: int
    remaining: int
    detail: str = ""


Event = Annotated[
    RunStarted
    | ModelCallRequested
    | ModelCallAdmitted
    | ModelCallRejected
    | ModelCallCompleted
    | ToolCallCompleted
    | FindingSubmitted
    | RunTerminated,
    Field(discriminator="type"),
]
