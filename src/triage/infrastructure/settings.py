from __future__ import annotations

import os
import tomllib
from pathlib import Path

from triage.application.config import RunConfig


def load_config(path: Path, **overrides: object) -> RunConfig:
    """Load a TOML config. Keyword overrides (e.g. from the CLI) win when not None."""
    raw = tomllib.loads(path.read_text())
    flat = {**raw.get("budget", {}), **raw.get("limits", {}), **raw.get("provider", {}), **raw.get("paths", {})}
    fields = {
        "budget_tokens": flat.get("tokens"),
        "output_allowance": flat.get("output_allowance"),
        "max_model_calls": flat.get("max_model_calls"),
        "provider": flat.get("kind"),
        "model": flat.get("model"),
        "script": flat.get("script"),
        "runs_dir": flat.get("runs_dir", "runs"),
    }
    fields.update({k: v for k, v in overrides.items() if v is not None})
    return RunConfig(**fields)


def load_dotenv(path: Path = Path(".env")) -> None:
    """Export KEY=VALUE lines from .env without overriding variables already set."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep and not key.lstrip().startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))
