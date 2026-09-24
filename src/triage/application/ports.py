from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from langchain_core.messages import AIMessage, BaseMessage

from triage.domain.events import Event
from triage.domain.model import TokenCount, Usage


@dataclass
class ModelResponse:
    message: AIMessage  # tool calls are in message.tool_calls
    usage: Usage | None  # None means the provider reported no usage. It does not mean zero.
    latency_s: float


class ModelProvider(Protocol):
    name: str

    def count_input_tokens(self, messages: Sequence[BaseMessage], tools: Sequence[dict[str, Any]]) -> TokenCount:
        """Pre-call input-token figure for exactly this request."""
        ...

    def invoke(
        self, messages: Sequence[BaseMessage], tools: Sequence[dict[str, Any]], max_output_tokens: int
    ) -> ModelResponse:
        """Issue one model call. max_output_tokens is sent to the provider as its output cap."""
        ...


class EventSink(Protocol):
    run_id: str

    def emit(self, event: Event) -> None:
        """Record one domain event in the run's trace."""
        ...
