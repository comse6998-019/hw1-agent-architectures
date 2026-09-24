from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from triage.application.config import RunConfig
from triage.infrastructure.eventlog import read_jsonl, read_trace


def new_run_dir(config: RunConfig, label: str) -> Path:
    return config.runs_dir / f"{time.strftime('%Y%m%dT%H%M%S')}-{config.provider}-{label}"


@dataclass(frozen=True)
class RunSummary:
    measurement: str
    kinds: Counter[str]
    tools: Counter[str]
    terminal_reasons: list[str]
    issued: int
    raised: int
    tokens_reported: int
    calls_without_usage: int

    @property
    def reconciles(self) -> bool:
        """Every admitted call reached the provider, and the run ended exactly once."""
        return self.kinds["ModelCallAdmitted"] == self.issued and len(self.terminal_reasons) == 1


def summarize(run_dir: Path) -> RunSummary:
    """Fold a run's trace and boundary log into one summary."""
    events = read_trace(run_dir / "trace.jsonl")
    boundary_path = run_dir / "boundary.jsonl"
    boundary = read_jsonl(boundary_path) if boundary_path.exists() else []
    return RunSummary(
        measurement=json.loads((run_dir / "meta.json").read_text())["measurement"],
        kinds=Counter(e["type"] for e in events),
        tools=Counter(e["tool"] for e in events if e["type"] == "ToolCallCompleted"),
        terminal_reasons=[e["reason"] for e in events if e["type"] == "RunTerminated"],
        issued=len(boundary),
        raised=sum(1 for c in boundary if c.get("error")),
        tokens_reported=sum(c["usage"]["input_tokens"] + c["usage"]["output_tokens"] for c in boundary if c["usage"]),
        calls_without_usage=sum(1 for c in boundary if not c["usage"] and not c.get("error")),
    )
