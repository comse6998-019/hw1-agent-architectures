from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from triage.domain.events import Event

_EVENT = TypeAdapter(Event)


class TraceWriter:
    """Appends one JSON object per event: {run_id, seq, ts, type, ...fields}."""

    def __init__(self, path: Path, run_id: str) -> None:
        self.path = path
        self.run_id = run_id
        self._seq = 0
        path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: Event) -> None:
        append_jsonl(self.path, {"run_id": self.run_id, "seq": self._seq, "ts": time.time(), **event.model_dump(mode="json")})
        self._seq += 1


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append one record as one JSON line. Lines are never rewritten."""
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def read_trace(path: Path) -> list[dict[str, Any]]:
    """Read a trace, validating every line against the event schemas."""
    records = read_jsonl(path)
    for record in records:
        _EVENT.validate_python({k: v for k, v in record.items() if k not in ("run_id", "seq", "ts")})
    return records
