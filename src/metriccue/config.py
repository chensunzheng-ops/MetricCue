from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class DataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    counter_mode: Literal["daily", "cumulative"] = "cumulative"
    timezone: str = "Asia/Shanghai"


class AnalysisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_window_days: int = Field(default=7, ge=1)
    baseline_window_days: int = Field(default=28, ge=7)
    minimum_contents: int = Field(default=10, ge=2)
    exclude_incomplete_today: bool = True
    compare_same_weekday: bool = True


class MetricCueConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: DataConfig = Field(default_factory=DataConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    columns: dict[str, str] = Field(default_factory=dict)
    denominators: dict[str, str] = Field(default_factory=dict)


def load_config(path: Path | None) -> MetricCueConfig:
    payload = {} if path is None else yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    try:
        return MetricCueConfig.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
