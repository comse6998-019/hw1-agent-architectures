from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class RunConfig(BaseModel):
    budget_tokens: int = Field(ge=0, description="Per-investigation token budget.")
    output_allowance: int = Field(ge=1, description="max_output_tokens sent with every model call.")
    max_model_calls: int = Field(ge=1, description="Failsafe only. Not the budget mechanism.")
    provider: Literal["scripted", "langchain"]
    model: str | None = None
    script: Path | None = None
    runs_dir: Path = Path("runs")

    @model_validator(mode="after")
    def _provider_fields(self) -> RunConfig:
        if self.provider == "langchain" and not self.model:
            raise ValueError('provider "langchain" needs model = "<provider>:<model-name>"')
        if self.provider == "scripted" and not self.script:
            raise ValueError('provider "scripted" needs script = "<path to script JSON>"')
        return self
