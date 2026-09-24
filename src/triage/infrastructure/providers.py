from __future__ import annotations

import json
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage
from pydantic import BaseModel, Field

from triage.application.config import RunConfig
from triage.application.ports import ModelProvider, ModelResponse
from triage.domain.model import TokenCount, Usage
from triage.infrastructure.eventlog import append_jsonl

# --- scripted provider: deterministic, offline, synthetic -------------------


class ScriptExhausted(RuntimeError):
    """The runtime issued a model call the script did not plan for."""


class ScriptStep(BaseModel):
    preflight_input_tokens: int = Field(ge=0)
    usage: Usage | None
    content: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)  # [{"name": ..., "args": {...}}]


class Script(BaseModel):
    description: str
    steps: list[ScriptStep]


class ScriptedProvider:
    """Replays a fixed sequence of responses with declared preflight counts and usage.

    Step i answers the i-th *issued* call. Preflight counts are declared as
    bounds, so a controlled test can check a hard ceiling. The numbers are
    synthetic fixtures, not measurements of any real model.
    """

    name = "scripted"

    def __init__(self, script: Script) -> None:
        self.script = script
        self.issued = 0
        self.requests: list[list[BaseMessage]] = []  # the messages each issued call received

    @classmethod
    def from_file(cls, path: Path) -> ScriptedProvider:
        return cls(Script.model_validate_json(path.read_text()))

    def _step(self) -> ScriptStep:
        if self.issued >= len(self.script.steps):
            raise ScriptExhausted(
                f"model call {self.issued + 1} requested; the script plans {len(self.script.steps)}"
            )
        return self.script.steps[self.issued]

    def count_input_tokens(self, messages: Sequence[BaseMessage], tools: Sequence[dict[str, Any]]) -> TokenCount:
        return TokenCount(tokens=self._step().preflight_input_tokens, kind="bound")

    def invoke(
        self, messages: Sequence[BaseMessage], tools: Sequence[dict[str, Any]], max_output_tokens: int
    ) -> ModelResponse:
        step = self._step()
        self.requests.append(list(messages))
        self.issued += 1
        tool_calls = [
            {"name": c["name"], "args": c["args"], "id": f"call_{self.issued}_{i}", "type": "tool_call"}
            for i, c in enumerate(step.tool_calls)
        ]
        return ModelResponse(AIMessage(content=step.content, tool_calls=tool_calls), step.usage, 0.0)


# --- live provider through LangChain -----------------------------------------


class LangChainProvider:
    """A LangChain chat model, chosen by a "<provider>:<model>" string.

    Checked offline (request payloads) with langchain-anthropic, langchain-openai,
    and langchain-ollama.
    Requires `uv sync --extra live` plus that integration package (for example
    `uv add langchain-anthropic`). Input counts are labelled "estimate" and do
    not bound actual usage: Anthropic counts through its token-counting API (a
    free network request that includes tool schemas), OpenAI counts locally and
    ignores tool schemas, and Ollama, which has no tokenizer here, gets
    characters / 4.
    """

    def __init__(self, model: str) -> None:
        from langchain.chat_models import (
            init_chat_model,  # optional extra; imported only for live runs
        )

        self.name = model
        self.model = init_chat_model(model, max_retries=0)  # HW1: no automatic retries

    def count_input_tokens(self, messages: Sequence[BaseMessage], tools: Sequence[dict[str, Any]]) -> TokenCount:
        if type(self.model).__name__ == "ChatOllama":  # no tokenizer; LangChain's fallback needs transformers
            chars = len(json.dumps([m.model_dump(mode="json") for m in messages] + list(tools)))
            return TokenCount(tokens=chars // 4, kind="estimate")
        count = self.model.get_num_tokens_from_messages(list(messages), tools=list(tools) or None)
        return TokenCount(tokens=count, kind="estimate")

    def invoke(
        self, messages: Sequence[BaseMessage], tools: Sequence[dict[str, Any]], max_output_tokens: int
    ) -> ModelResponse:
        start = time.perf_counter()
        if type(self.model).__name__ == "ChatOllama":  # Ollama's output cap is the num_predict option; it rejects max_tokens
            model = self.model.model_copy(update={"num_predict": max_output_tokens}).bind_tools(list(tools))
        else:
            model = self.model.bind_tools(list(tools)).bind(max_tokens=max_output_tokens)
        message = model.invoke(list(messages))
        latency = time.perf_counter() - start
        meta = message.usage_metadata
        usage = None
        if meta is not None:
            details = meta.get("input_token_details", {})
            usage = Usage(
                input_tokens=meta["input_tokens"],
                output_tokens=meta["output_tokens"],
                cache_read_tokens=details.get("cache_read", 0),
                cache_write_tokens=details.get("cache_creation", 0),
            )
        return ModelResponse(message, usage, latency)


# --- independent boundary recorder -------------------------------------------


@dataclass
class RecordingProvider:
    """Wraps a provider and logs every call issued through it, including calls that raise.

    The log is written by this wrapper, not by your runtime. Comparing it with
    your trace is how "the third call never happened" is verified.
    """

    inner: ModelProvider
    log_path: Path
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.inner.name
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.touch()  # an empty log is the record of a run that issued no call

    def count_input_tokens(self, messages: Sequence[BaseMessage], tools: Sequence[dict[str, Any]]) -> TokenCount:
        return self.inner.count_input_tokens(messages, tools)

    def invoke(
        self, messages: Sequence[BaseMessage], tools: Sequence[dict[str, Any]], max_output_tokens: int
    ) -> ModelResponse:
        record: dict[str, Any] = {
            "index": len(self.calls),
            "ts": time.time(),
            "messages": len(messages),
            "max_output_tokens": max_output_tokens,
            "usage": None,
            "latency_s": None,
        }
        try:
            response = self.inner.invoke(messages, tools, max_output_tokens)
            record["usage"] = response.usage.model_dump() if response.usage else None
            record["latency_s"] = response.latency_s
            return response
        except Exception as e:  # the call was issued even though it failed
            record["error"] = f"{type(e).__name__}: {e}"
            raise
        finally:
            self.calls.append(record)
            append_jsonl(self.log_path, record)


def make_provider(config: RunConfig) -> ModelProvider:
    """A fresh provider for every run, so runs share no state."""
    if config.provider == "scripted":
        assert config.script is not None  # enforced by RunConfig
        return ScriptedProvider.from_file(config.script)
    assert config.model is not None
    return LangChainProvider(config.model)
