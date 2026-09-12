from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class FindingLevel(StrEnum):
    FACT = "fact"
    SIGNAL = "signal"
    HYPOTHESIS = "hypothesis"
    PROPOSED_EXPERIMENT = "proposed_experiment"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    severity: Severity
    message: str
    table: str
    rows: list[int] = Field(default_factory=list)
    repair: str | None = None


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    level: FindingLevel
    metric: str
    direction: Literal["up", "down", "mixed", "none"]
    current_value: float | None
    baseline_value: float | None
    absolute_change: float | None
    relative_change: float | None
    sample_size: int
    confidence: Confidence
    segment: dict[str, str] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    metriccue_version: str
    created_at: datetime
    timezone: str
    input_hashes: dict[str, str]
    config_hash: str
    data_start: str | None
    data_end: str | None
    enabled_modules: list[str]
    skipped_modules: dict[str, str]
    issue_counts: dict[str, int]
    metadata: dict[str, Any] = Field(default_factory=dict)
