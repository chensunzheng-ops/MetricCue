# MetricCue v0.1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first Python CLI that validates content-operations CSV data, produces reproducible evidence-backed diagnostics and reports, and exposes those results to a safe optional skill.

**Architecture:** A typed Python core owns ingestion, validation, metric calculation, diagnostics, evidence persistence, and reporting. Typer exposes stable CLI commands; the skill invokes only those commands and turns aggregate evidence into explicitly labeled hypotheses and experiment cards.

**Tech Stack:** Python 3.11+, pandas, Pydantic 2, PyYAML, Typer, Matplotlib, pytest, pytest-cov, Ruff, mypy, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-12-metriccue-design.md`

## Global Constraints

- Support Python 3.11, 3.12, and 3.13.
- Run offline without model credentials; no platform login, scraping, API collection, publishing, messaging, or advertising.
- Keep raw input local; model-facing artifacts contain aggregate evidence only.
- Distinguish fact, signal, hypothesis, and proposed experiment; never present correlation as causation.
- Every reported number must be traceable to a stable finding ID in `evidence.json`.
- Preserve platform-scoped metric semantics and do not compare incompatible platform definitions by default.
- Use error, warning, and informational validation severities; insufficient evidence must block unsupported findings.
- Generate immutable run directories containing manifest, validation, evidence, recommendations, report, and charts.
- Verify Windows and Ubuntu behavior in CI.
- Use the working name and package identifier `MetricCue` / `metriccue`.
- Present the repository as a normal open-source product, not as an interview or portfolio exercise.

## Planned File Map

```text
pyproject.toml                         Package metadata, dependencies, tools, CLI entry point
README.md                              Chinese-first product documentation and quick start
README.en.md                           Concise English documentation
LICENSE                               MIT license
CHANGELOG.md                           Release history
metriccue.example.yaml                Annotated default configuration
src/metriccue/__init__.py             Version export
src/metriccue/models.py               Shared typed contracts
src/metriccue/config.py               YAML configuration loading and validation
src/metriccue/ingestion.py            CSV reading, mapping, and canonicalization
src/metriccue/validation.py           Schema, quality, semantic, and privacy validation
src/metriccue/metrics.py              Counter normalization and metric registry
src/metriccue/lifecycle.py            Analysis windows and content-age alignment
src/metriccue/anomalies.py            Robust trends, anomalies, and confidence
src/metriccue/segments.py             Segment comparison and contribution decomposition
src/metriccue/production.py           Production-cycle efficiency analysis
src/metriccue/pipeline.py             End-to-end run orchestration and immutable artifacts
src/metriccue/reporting.py            Markdown and SVG report generation
src/metriccue/cli.py                  Typer commands and exit-code translation
skills/metriccue/SKILL.md              Host-agent orchestration and safety rules
skills/metriccue/references/           CLI, evidence, and experiment-card references
examples/synthetic_xhs/generate.py    Deterministic synthetic case generator
examples/synthetic_xhs/README.md      Synthetic-data provenance and planted scenarios
examples/synthetic_xhs/*.csv          Generated golden example inputs
examples/synthetic_xhs/*.yaml         Mapping and expected findings
tests/unit/                            Focused behavior tests
tests/integration/                     End-to-end CLI and pipeline tests
tests/golden/                          Planted-finding and report-consistency tests
docs/data-contract.md                 User-facing schema and metric semantics
docs/methodology.md                   Statistical methods and limitations
docs/privacy.md                       Local-processing and model-handoff policy
docs/contributing.md                  Contribution and anonymization rules
docs/user-test-protocol.md            Three-to-five-user validation protocol
.github/workflows/ci.yml              Multi-version Windows and Ubuntu checks
.github/ISSUE_TEMPLATE/                Safe structured issue templates
```

---

### Task 1: Package Foundation, Shared Models, and Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/metriccue/__init__.py`
- Create: `src/metriccue/models.py`
- Create: `src/metriccue/config.py`
- Create: `metriccue.example.yaml`
- Test: `tests/unit/test_config.py`
- Test: `tests/unit/test_models.py`

**Interfaces:**
- Produces: `Severity`, `FindingLevel`, `Confidence`, `ValidationIssue`, `Finding`, `RunManifest`, `MetricCueConfig`, and `load_config(path: Path | None) -> MetricCueConfig`.
- Consumes: no project interfaces.

- [ ] **Step 1: Write failing model and configuration tests**

```python
# tests/unit/test_config.py
from pathlib import Path

from metriccue.config import load_config


def test_load_config_applies_documented_defaults(tmp_path: Path) -> None:
    path = tmp_path / "metriccue.yaml"
    path.write_text("data:\n  timezone: Asia/Shanghai\n", encoding="utf-8")

    config = load_config(path)

    assert config.data.timezone == "Asia/Shanghai"
    assert config.data.counter_mode == "cumulative"
    assert config.analysis.current_window_days == 7
    assert config.analysis.baseline_window_days == 28
    assert config.analysis.minimum_contents == 10


def test_unknown_config_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "metriccue.yaml"
    path.write_text("analysis:\n  mystery: true\n", encoding="utf-8")

    try:
        load_config(path)
    except ValueError as exc:
        assert "mystery" in str(exc)
    else:
        raise AssertionError("unknown configuration key was accepted")
```

```python
# tests/unit/test_models.py
from metriccue.models import Confidence, Finding, FindingLevel


def test_finding_serializes_stable_evidence_shape() -> None:
    finding = Finding(
        finding_id="engagement_rate_decline_001",
        level=FindingLevel.SIGNAL,
        metric="engagement_rate",
        direction="down",
        current_value=0.044,
        baseline_value=0.062,
        absolute_change=-0.018,
        relative_change=-0.2903225806,
        sample_size=47,
        confidence=Confidence.MEDIUM,
        evidence=["连续5天低于历史中位数"],
        limitations=["当前窗口样本有限"],
    )

    payload = finding.model_dump(mode="json")

    assert payload["finding_id"] == "engagement_rate_decline_001"
    assert payload["level"] == "signal"
    assert payload["confidence"] == "medium"
```

- [ ] **Step 2: Run tests and verify the package does not exist yet**

Run: `python -m pytest tests/unit/test_config.py tests/unit/test_models.py -v`

Expected: collection fails with `ModuleNotFoundError: No module named 'metriccue'`.

- [ ] **Step 3: Add package metadata and dependencies**

```toml
# pyproject.toml
[build-system]
requires = ["hatchling>=1.25,<2"]
build-backend = "hatchling.build"

[project]
name = "metriccue"
version = "0.1.0.dev0"
description = "Evidence-first diagnostics for content operations data"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
dependencies = [
  "matplotlib>=3.9,<4",
  "pandas>=2.2,<3",
  "pydantic>=2.8,<3",
  "pyyaml>=6,<7",
  "typer>=0.12,<1",
]

[project.optional-dependencies]
dev = [
  "build>=1.2,<2",
  "mypy>=1.11,<2",
  "pandas-stubs>=2.2,<3",
  "pytest>=8.3,<9",
  "pytest-cov>=5,<7",
  "ruff>=0.6,<1",
  "types-PyYAML>=6.0,<7",
]

[project.scripts]
metriccue = "metriccue.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/metriccue"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--strict-markers"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
packages = ["metriccue"]
```

Create the initial `README.md` with the exact title `# MetricCue`, the sentence `Evidence-first diagnostics for content operations data.`, and a truthful note that v0.1.0 implementation is in progress. Task 13 replaces this minimal package document with the complete user-facing README.

- [ ] **Step 4: Implement shared typed contracts**

```python
# src/metriccue/models.py
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
```

- [ ] **Step 5: Implement strict configuration loading and the example YAML**

```python
# src/metriccue/config.py
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
    data: DataConfig = DataConfig()
    analysis: AnalysisConfig = AnalysisConfig()
    columns: dict[str, str] = Field(default_factory=dict)
    denominators: dict[str, str] = Field(default_factory=dict)


def load_config(path: Path | None) -> MetricCueConfig:
    payload = {} if path is None else yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    try:
        return MetricCueConfig.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
```

Create `metriccue.example.yaml` with the exact defaults and Chinese mapping example from the spec.

- [ ] **Step 6: Run focused quality checks**

Run: `python -m pytest tests/unit/test_config.py tests/unit/test_models.py -v`

Expected: all tests pass.

Run: `python -m ruff check src/metriccue tests/unit/test_config.py tests/unit/test_models.py`

Expected: exit code 0.

- [ ] **Step 7: Commit the foundation**

```bash
git add pyproject.toml README.md metriccue.example.yaml src/metriccue tests/unit/test_config.py tests/unit/test_models.py
git commit -m "feat: establish MetricCue typed foundation"
```

---

### Task 2: CSV Ingestion, Schema Validation, and Privacy Checks

**Files:**
- Create: `src/metriccue/ingestion.py`
- Create: `src/metriccue/validation.py`
- Test: `tests/unit/test_ingestion.py`
- Test: `tests/unit/test_validation.py`

**Interfaces:**
- Consumes: `MetricCueConfig`, `ValidationIssue`, and `Severity` from Task 1.
- Produces: `InputTables`, `read_inputs(...) -> InputTables`, `validate_inputs(tables, config) -> list[ValidationIssue]`, and `has_blocking_issues(issues) -> bool`.

- [ ] **Step 1: Write failing ingestion tests**

```python
# tests/unit/test_ingestion.py
from pathlib import Path

from metriccue.config import MetricCueConfig
from metriccue.ingestion import read_inputs


def test_read_inputs_maps_chinese_columns_and_parses_dates(tmp_path: Path) -> None:
    path = tmp_path / "performance.csv"
    path.write_text(
        "数据日期,笔记ID,平台,账号,曝光数\n2026-09-01,n1,xhs,a1,120\n",
        encoding="utf-8",
    )
    config = MetricCueConfig.model_validate(
        {"columns": {"date": "数据日期", "content_id": "笔记ID", "platform": "平台", "account_id": "账号", "impressions": "曝光数"}}
    )

    tables = read_inputs(path, None, None, config)

    assert list(tables.performance.columns) == ["date", "content_id", "platform", "account_id", "impressions"]
    assert str(tables.performance.loc[0, "date"].date()) == "2026-09-01"
```

- [ ] **Step 2: Write failing validation and privacy tests**

```python
# tests/unit/test_validation.py
import pandas as pd

from metriccue.config import MetricCueConfig
from metriccue.ingestion import InputTables
from metriccue.models import Severity
from metriccue.validation import has_blocking_issues, validate_inputs


def test_duplicate_performance_key_is_blocking() -> None:
    frame = pd.DataFrame(
        [
            {"date": "2026-09-01", "content_id": "n1", "platform": "xhs", "account_id": "a1", "views": 10},
            {"date": "2026-09-01", "content_id": "n1", "platform": "xhs", "account_id": "a1", "views": 12},
        ]
    )
    issues = validate_inputs(InputTables(performance=frame), MetricCueConfig())

    assert any(issue.code == "duplicate_performance_key" and issue.severity is Severity.ERROR for issue in issues)
    assert has_blocking_issues(issues)


def test_sensitive_column_blocks_model_handoff_but_not_local_analysis() -> None:
    frame = pd.DataFrame(
        [{"date": "2026-09-01", "content_id": "n1", "platform": "xhs", "account_id": "a1", "views": 10, "customer_phone": "13800000000"}]
    )
    issues = validate_inputs(InputTables(performance=frame), MetricCueConfig())

    issue = next(item for item in issues if item.code == "sensitive_column")
    assert issue.severity is Severity.WARNING
    assert "model" in issue.message.lower()
```

- [ ] **Step 3: Run tests and verify missing interfaces**

Run: `python -m pytest tests/unit/test_ingestion.py tests/unit/test_validation.py -v`

Expected: collection fails because `metriccue.ingestion` and `metriccue.validation` do not exist.

- [ ] **Step 4: Implement canonical CSV ingestion**

```python
# src/metriccue/ingestion.py
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from metriccue.config import MetricCueConfig


@dataclass(frozen=True)
class InputTables:
    performance: pd.DataFrame
    content: pd.DataFrame | None = None
    production: pd.DataFrame | None = None


def _read(path: Path, config: MetricCueConfig) -> pd.DataFrame:
    frame = pd.read_csv(path, encoding="utf-8")
    reverse_mapping = {source: canonical for canonical, source in config.columns.items()}
    frame = frame.rename(columns=reverse_mapping)
    for column in ("date", "published_at", "idea_started_at", "brief_completed_at", "draft_completed_at", "review_started_at", "review_completed_at", "scheduled_at"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
    return frame


def read_inputs(
    performance_path: Path,
    content_path: Path | None,
    production_path: Path | None,
    config: MetricCueConfig,
) -> InputTables:
    return InputTables(
        performance=_read(performance_path, config),
        content=None if content_path is None else _read(content_path, config),
        production=None if production_path is None else _read(production_path, config),
    )
```

- [ ] **Step 5: Implement validation rules and privacy detection**

```python
# src/metriccue/validation.py
import re

from metriccue.config import MetricCueConfig
from metriccue.ingestion import InputTables
from metriccue.models import Severity, ValidationIssue

REQUIRED_DIMENSIONS = {"date", "content_id", "platform", "account_id"}
SUPPORTED_METRICS = {"impressions", "views", "clicks", "likes", "comments", "saves", "shares", "completed_views", "follows", "leads", "orders", "revenue"}
SENSITIVE_NAME = re.compile(r"(phone|mobile|email|e-mail|name|姓名|手机|电话|邮箱)", re.IGNORECASE)


def validate_inputs(tables: InputTables, config: MetricCueConfig) -> list[ValidationIssue]:
    del config
    issues: list[ValidationIssue] = []
    frame = tables.performance
    missing = sorted(REQUIRED_DIMENSIONS - set(frame.columns))
    if missing:
        issues.append(ValidationIssue(code="missing_required_columns", severity=Severity.ERROR, message=f"Missing required columns: {', '.join(missing)}", table="performance", repair="Map or add every required dimension."))
    if not (SUPPORTED_METRICS & set(frame.columns)):
        issues.append(ValidationIssue(code="missing_supported_metric", severity=Severity.ERROR, message="Performance table has no supported metric.", table="performance", repair="Add at least one supported metric column."))
    key = ["platform", "account_id", "content_id", "date"]
    if set(key).issubset(frame.columns):
        duplicate_rows = frame.index[frame.duplicated(key, keep=False)].tolist()
        if duplicate_rows:
            issues.append(ValidationIssue(code="duplicate_performance_key", severity=Severity.ERROR, message="Duplicate platform/account/content/date rows make the grain ambiguous.", table="performance", rows=duplicate_rows, repair="Aggregate or remove duplicate rows before analysis."))
    for table_name, candidate in (("performance", tables.performance), ("content", tables.content), ("production", tables.production)):
        if candidate is None:
            continue
        for column in candidate.columns:
            if SENSITIVE_NAME.search(str(column)):
                issues.append(ValidationIssue(code="sensitive_column", severity=Severity.WARNING, message=f"Column '{column}' may contain personal data; local analysis may continue but model handoff is blocked.", table=table_name, repair="Remove, anonymize, or explicitly exclude the column."))
    return issues


def has_blocking_issues(issues: list[ValidationIssue]) -> bool:
    return any(issue.severity is Severity.ERROR for issue in issues)
```

- [ ] **Step 6: Add semantic cases and run focused tests**

Extend `tests/unit/test_validation.py` with exact cases for unparseable required dates, negative counts, observations before publication, implausible funnel values, mixed percentage scales, and missing values in an available segment column such as `topic`. Implement one stable issue code per case; use `missing_segment_value` for the segment-coverage warning and assert the documented severity.

Run: `python -m pytest tests/unit/test_ingestion.py tests/unit/test_validation.py -v`

Expected: all tests pass.

- [ ] **Step 7: Commit ingestion and validation**

```bash
git add src/metriccue/ingestion.py src/metriccue/validation.py tests/unit/test_ingestion.py tests/unit/test_validation.py
git commit -m "feat: ingest and validate content operations data"
```

---

### Task 3: Counter Normalization and Metric Registry

**Files:**
- Create: `src/metriccue/metrics.py`
- Test: `tests/unit/test_metrics.py`

**Interfaces:**
- Consumes: canonical performance frames and `MetricCueConfig`.
- Produces: `normalize_counters(frame, mode) -> tuple[pd.DataFrame, list[ValidationIssue]]`, `MetricDefinition`, `METRICS`, and `compute_metrics(frame, config) -> pd.DataFrame`.

- [ ] **Step 1: Write failing counter and formula tests**

```python
# tests/unit/test_metrics.py
import pandas as pd

from metriccue.config import MetricCueConfig
from metriccue.metrics import compute_metrics, normalize_counters


def test_cumulative_values_become_daily_increments() -> None:
    frame = pd.DataFrame(
        [
            {"date": "2026-09-01", "platform": "xhs", "account_id": "a1", "content_id": "n1", "views": 10},
            {"date": "2026-09-02", "platform": "xhs", "account_id": "a1", "content_id": "n1", "views": 25},
        ]
    )

    normalized, issues = normalize_counters(frame, "cumulative")

    assert normalized["views"].tolist() == [10.0, 15.0]
    assert issues == []


def test_counter_reset_is_missing_and_reported() -> None:
    frame = pd.DataFrame(
        [
            {"date": "2026-09-01", "platform": "xhs", "account_id": "a1", "content_id": "n1", "views": 25},
            {"date": "2026-09-02", "platform": "xhs", "account_id": "a1", "content_id": "n1", "views": 4},
        ]
    )

    normalized, issues = normalize_counters(frame, "cumulative")

    assert pd.isna(normalized.loc[1, "views"])
    assert any(issue.code == "counter_reset" for issue in issues)


def test_zero_denominator_produces_missing_metric() -> None:
    frame = pd.DataFrame([{"views": 0, "likes": 1, "comments": 0, "saves": 0, "shares": 0}])

    result = compute_metrics(frame, MetricCueConfig())

    assert pd.isna(result.loc[0, "engagement_rate"])
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/unit/test_metrics.py -v`

Expected: collection fails because `metriccue.metrics` does not exist.

- [ ] **Step 3: Implement metric definitions and safe division**

```python
# src/metriccue/metrics.py
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from metriccue.config import MetricCueConfig
from metriccue.models import Severity, ValidationIssue

COUNT_COLUMNS = ["impressions", "views", "clicks", "likes", "comments", "saves", "shares", "completed_views", "follows", "leads", "orders", "revenue"]
KEY_COLUMNS = ["platform", "account_id", "content_id"]


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    numerator: str
    denominator: str


METRICS = {
    item.name: item
    for item in (
        MetricDefinition("click_through_rate", "clicks", "impressions"),
        MetricDefinition("view_rate", "views", "impressions"),
        MetricDefinition("engagement_rate", "interactions", "views"),
        MetricDefinition("completion_rate", "completed_views", "views"),
        MetricDefinition("follow_conversion", "follows", "views"),
        MetricDefinition("lead_conversion", "leads", "clicks"),
        MetricDefinition("order_conversion", "orders", "leads"),
        MetricDefinition("average_order_value", "revenue", "orders"),
    )
}


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.div(denominator.where(denominator.ne(0)))


def compute_metrics(frame: pd.DataFrame, config: MetricCueConfig) -> pd.DataFrame:
    result = frame.copy()
    interaction_columns = [name for name in ("likes", "comments", "saves", "shares") if name in result]
    if interaction_columns:
        result["interactions"] = result[interaction_columns].fillna(0).sum(axis=1)
    for name, definition in METRICS.items():
        denominator = config.denominators.get(name, definition.denominator)
        if definition.numerator in result and denominator in result:
            result[name] = _safe_divide(result[definition.numerator], result[denominator])
    return result
```

- [ ] **Step 4: Implement cumulative normalization without silent repair**

Add `normalize_counters` to `metrics.py`. Sort by keys and date, compute grouped differences, keep the first observation as its own increment, replace negative differences with `NA`, and emit `ValidationIssue(code="counter_reset", severity=Severity.WARNING, ...)` with affected row indices. In `daily` mode return a numeric copy unchanged except for type coercion.

- [ ] **Step 5: Run metric tests**

Run: `python -m pytest tests/unit/test_metrics.py -v`

Expected: all tests pass.

- [ ] **Step 6: Commit metrics**

```bash
git add src/metriccue/metrics.py tests/unit/test_metrics.py
git commit -m "feat: normalize counters and calculate metrics"
```

---

### Task 4: Analysis Windows and Content Lifecycle Alignment

**Files:**
- Create: `src/metriccue/lifecycle.py`
- Test: `tests/unit/test_lifecycle.py`

**Interfaces:**
- Consumes: normalized performance and optional content frames.
- Produces: `AnalysisWindow`, `build_analysis_window(dates, config, now) -> AnalysisWindow`, `align_content_age(performance, content) -> pd.DataFrame`, and `lifecycle_summary(frame, metrics) -> pd.DataFrame`.

- [ ] **Step 1: Write failing window and lifecycle tests**

```python
# tests/unit/test_lifecycle.py
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from metriccue.config import MetricCueConfig
from metriccue.lifecycle import align_content_age, build_analysis_window


def test_window_excludes_incomplete_today() -> None:
    dates = pd.Series(pd.date_range("2026-08-01", "2026-09-12", freq="D"))
    now = datetime(2026, 9, 12, 15, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    window = build_analysis_window(dates, MetricCueConfig(), now)

    assert str(window.current_end.date()) == "2026-09-11"
    assert str(window.current_start.date()) == "2026-09-05"
    assert str(window.baseline_start.date()) == "2026-08-08"


def test_content_age_aligns_items_by_days_since_publish() -> None:
    performance = pd.DataFrame([{"date": "2026-09-03", "platform": "xhs", "account_id": "a1", "content_id": "n1", "views": 20}])
    content = pd.DataFrame([{"platform": "xhs", "account_id": "a1", "content_id": "n1", "published_at": "2026-09-01"}])

    result = align_content_age(performance, content)

    assert result.loc[0, "content_age_days"] == 2
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/unit/test_lifecycle.py -v`

Expected: collection fails because `metriccue.lifecycle` does not exist.

- [ ] **Step 3: Implement immutable analysis windows**

```python
# src/metriccue/lifecycle.py
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from metriccue.config import MetricCueConfig


@dataclass(frozen=True)
class AnalysisWindow:
    baseline_start: pd.Timestamp
    baseline_end: pd.Timestamp
    current_start: pd.Timestamp
    current_end: pd.Timestamp


def build_analysis_window(dates: pd.Series, config: MetricCueConfig, now: datetime) -> AnalysisWindow:
    del dates
    last_complete = pd.Timestamp(now.date()) - pd.Timedelta(days=1) if config.analysis.exclude_incomplete_today else pd.Timestamp(now.date())
    current_start = last_complete - pd.Timedelta(days=config.analysis.current_window_days - 1)
    baseline_end = current_start - pd.Timedelta(days=1)
    baseline_start = baseline_end - pd.Timedelta(days=config.analysis.baseline_window_days - 1)
    return AnalysisWindow(baseline_start, baseline_end, current_start, last_complete)
```

- [ ] **Step 4: Implement lifecycle alignment and summaries**

Implement a many-to-one merge on `platform`, `account_id`, and `content_id`; calculate normalized calendar-day age; reject negative age through validation; aggregate each requested metric by `content_age_days` with count, median, and quartiles. Add explicit 1-day, 3-day, and 7-day cumulative helper columns only when complete coverage exists.

- [ ] **Step 5: Run lifecycle tests and commit**

Run: `python -m pytest tests/unit/test_lifecycle.py -v`

Expected: all tests pass.

```bash
git add src/metriccue/lifecycle.py tests/unit/test_lifecycle.py
git commit -m "feat: align analysis windows and content lifecycle"
```

---

### Task 5: Robust Anomaly Detection and Confidence

**Files:**
- Create: `src/metriccue/anomalies.py`
- Test: `tests/unit/test_anomalies.py`

**Interfaces:**
- Consumes: metric frames, `AnalysisWindow`, and analysis configuration.
- Produces: `robust_z_score(values) -> pd.Series`, `confidence_for(...) -> Confidence`, and `detect_metric_anomalies(...) -> list[Finding]`.

- [ ] **Step 1: Write failing robust-statistics tests**

```python
# tests/unit/test_anomalies.py
import pandas as pd

from metriccue.anomalies import confidence_for, robust_z_score
from metriccue.models import Confidence


def test_viral_outlier_does_not_shift_robust_center() -> None:
    scores = robust_z_score(pd.Series([10, 11, 10, 9, 10, 1000], dtype=float))

    assert abs(scores.iloc[0]) < 1
    assert scores.iloc[-1] > 10


def test_low_quality_and_small_sample_force_low_confidence() -> None:
    result = confidence_for(sample_size=5, relative_effect=0.5, persistent_days=5, data_quality=0.6)

    assert result is Confidence.LOW
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/unit/test_anomalies.py -v`

Expected: collection fails because `metriccue.anomalies` does not exist.

- [ ] **Step 3: Implement MAD scores and deterministic confidence**

```python
# src/metriccue/anomalies.py
import numpy as np
import pandas as pd

from metriccue.models import Confidence


def robust_z_score(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    median = numeric.median()
    mad = (numeric - median).abs().median()
    if pd.isna(mad) or mad == 0:
        iqr = numeric.quantile(0.75) - numeric.quantile(0.25)
        scale = iqr / 1.349 if iqr > 0 else np.nan
        return (numeric - median) / scale
    return 0.67448975 * (numeric - median) / mad


def confidence_for(sample_size: int, relative_effect: float, persistent_days: int, data_quality: float) -> Confidence:
    if sample_size < 10 or data_quality < 0.8:
        return Confidence.LOW
    score = int(sample_size >= 30) + int(abs(relative_effect) >= 0.2) + int(persistent_days >= 3) + int(data_quality >= 0.95)
    if score >= 4:
        return Confidence.HIGH
    if score >= 2:
        return Confidence.MEDIUM
    return Confidence.LOW
```

- [ ] **Step 4: Implement finding generation**

Implement `detect_metric_anomalies` to aggregate numerator and denominator before calculating rate metrics, compare current and baseline windows, check persistence in daily values, incorporate robust scores, and emit stable IDs derived from metric plus a deterministic ordinal. Every finding must include sample size, evidence strings describing window comparisons, limitations, and `FindingLevel.SIGNAL`; do not create hypotheses in this module.

- [ ] **Step 5: Test rate aggregation, persistence, and insufficient evidence**

Add tests asserting that rates are computed from summed numerators and denominators rather than averaged row rates, a one-day spike is lower confidence than a five-day decline, and samples below `minimum_contents` produce no signal finding.

Run: `python -m pytest tests/unit/test_anomalies.py -v`

Expected: all tests pass.

- [ ] **Step 6: Commit anomaly analysis**

```bash
git add src/metriccue/anomalies.py tests/unit/test_anomalies.py
git commit -m "feat: detect robust metric anomalies"
```

---

### Task 6: Segment Comparison and Contribution Decomposition

**Files:**
- Create: `src/metriccue/segments.py`
- Test: `tests/unit/test_segments.py`

**Interfaces:**
- Consumes: metric frames, an `AnalysisWindow`, dimension names, and minimum sample size.
- Produces: `SegmentComparison`, `compare_segments(...) -> list[SegmentComparison]`, `decompose_change(...) -> pd.DataFrame`, and `detect_aggregate_reversal(...) -> bool`.

- [ ] **Step 1: Write failing mix-shift and reversal tests**

```python
# tests/unit/test_segments.py
import pandas as pd

from metriccue.segments import decompose_change, detect_aggregate_reversal


def test_decomposition_separates_mix_and_within_segment_change() -> None:
    baseline = pd.DataFrame({"segment": ["short", "long"], "weight": [0.8, 0.2], "value": [0.08, 0.05]})
    current = pd.DataFrame({"segment": ["short", "long"], "weight": [0.6, 0.4], "value": [0.08, 0.04]})

    result = decompose_change(baseline, current)

    assert result["mix_effect"].sum() < 0
    assert result["within_effect"].sum() < 0


def test_detects_aggregate_direction_reversal() -> None:
    grouped = pd.DataFrame({"baseline": [0.10, 0.04], "current": [0.11, 0.05]})

    assert detect_aggregate_reversal(grouped, aggregate_change=-0.01)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/unit/test_segments.py -v`

Expected: collection fails because `metriccue.segments` does not exist.

- [ ] **Step 3: Implement typed comparisons and Oaxaca-style two-part decomposition**

Create a frozen `SegmentComparison` dataclass with dimension, segment, sample size, current median, baseline median, IQR, relative difference, effect size, and coverage. Implement a symmetric decomposition using the midpoint weights and midpoint values so total change equals the sum of mix and within effects within floating-point tolerance.

- [ ] **Step 4: Implement segment eligibility and aggregate-reversal warning**

Exclude segments below `minimum_contents` from primary conclusions but return them with an `eligible=False` flag for observation tables. Detect when every eligible segment moves in one direction while the aggregate moves in the other direction. Emit a limitation message instead of a causal interpretation.

- [ ] **Step 5: Run segment tests and commit**

Run: `python -m pytest tests/unit/test_segments.py -v`

Expected: all tests pass.

```bash
git add src/metriccue/segments.py tests/unit/test_segments.py
git commit -m "feat: explain segment and mix contributions"
```

---

### Task 7: Production-Efficiency Analysis

**Files:**
- Create: `src/metriccue/production.py`
- Test: `tests/unit/test_production.py`

**Interfaces:**
- Consumes: optional canonical production and content frames.
- Produces: `derive_production_metrics(frame) -> pd.DataFrame` and `analyze_production(frame, minimum_contents) -> list[Finding]`.

- [ ] **Step 1: Write failing production-cycle tests**

```python
# tests/unit/test_production.py
import pandas as pd

from metriccue.production import derive_production_metrics


def test_derives_review_wait_and_publication_delay_hours() -> None:
    frame = pd.DataFrame(
        [{
            "content_id": "n1",
            "idea_started_at": "2026-09-01 09:00",
            "review_started_at": "2026-09-02 09:00",
            "review_completed_at": "2026-09-03 09:00",
            "scheduled_at": "2026-09-03 10:00",
            "published_at": "2026-09-03 16:00",
        }]
    )

    result = derive_production_metrics(frame)

    assert result.loc[0, "review_wait_hours"] == 24
    assert result.loc[0, "publication_delay_hours"] == 6
    assert result.loc[0, "total_cycle_hours"] == 55
```

- [ ] **Step 2: Run test and verify failure**

Run: `python -m pytest tests/unit/test_production.py -v`

Expected: collection fails because `metriccue.production` does not exist.

- [ ] **Step 3: Implement duration derivation and chronology protection**

Parse all supported timestamps with `errors="coerce"`, subtract only valid ordered pairs, and leave negative durations missing. Add `is_on_time` when both schedule and publish timestamps exist. Preserve `revision_count` and `production_cost` as numeric values.

- [ ] **Step 4: Implement production findings**

Compare current and baseline medians for total cycle, review wait, publication delay, revision count, and cost. Emit findings only when sample eligibility is met. When content outcomes are joinable, report associations as signals and add the limitation `Production timing and content performance are observational, not causal.`

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/unit/test_production.py -v`

Expected: all tests pass.

```bash
git add src/metriccue/production.py tests/unit/test_production.py
git commit -m "feat: diagnose content production efficiency"
```

---

### Task 8: Immutable Analysis Pipeline and Evidence Store

**Files:**
- Create: `src/metriccue/pipeline.py`
- Create: `tests/conftest.py`
- Test: `tests/integration/test_pipeline.py`

**Interfaces:**
- Consumes: all analysis interfaces from Tasks 1 through 7.
- Produces: `RunResult`, `run_analysis(request: AnalysisRequest) -> RunResult`, immutable run directories, and JSON artifacts.

- [ ] **Step 1: Write a failing end-to-end artifact test**

```python
# tests/integration/test_pipeline.py
import json
from pathlib import Path

from metriccue.pipeline import AnalysisRequest, run_analysis


def test_pipeline_writes_traceable_immutable_artifacts(tmp_path: Path, minimal_performance_csv: Path) -> None:
    output_root = tmp_path / "runs"
    result = run_analysis(AnalysisRequest(performance_path=minimal_performance_csv, output_root=output_root))

    assert result.run_dir.parent == output_root
    manifest = json.loads((result.run_dir / "manifest.json").read_text(encoding="utf-8"))
    evidence = json.loads((result.run_dir / "evidence.json").read_text(encoding="utf-8"))
    assert manifest["input_hashes"]["performance"]
    assert all(item["finding_id"] for item in evidence)
    assert (result.run_dir / "validation.json").exists()
```

Create the shared fixture at the same time:

```python
# tests/conftest.py
from pathlib import Path

import pytest


@pytest.fixture
def minimal_performance_csv(tmp_path: Path) -> Path:
    path = tmp_path / "performance.csv"
    path.write_text(
        "date,content_id,platform,account_id,views\n"
        "2026-08-01,n1,xhs,a1,10\n"
        "2026-08-02,n1,xhs,a1,15\n",
        encoding="utf-8",
    )
    return path
```

- [ ] **Step 2: Run the test and verify failure**

Run: `python -m pytest tests/integration/test_pipeline.py -v`

Expected: collection fails because `metriccue.pipeline` does not exist.

- [ ] **Step 3: Implement request/result types, hashing, and run IDs**

```python
# src/metriccue/pipeline.py
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True)
class AnalysisRequest:
    performance_path: Path
    output_root: Path
    content_path: Path | None = None
    production_path: Path | None = None
    config_path: Path | None = None
    now: datetime | None = None


@dataclass(frozen=True)
class RunResult:
    run_dir: Path
    finding_count: int
    blocking: bool


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_id(now: datetime) -> str:
    return now.astimezone(UTC).strftime("%Y-%m-%dT%H%M%SZ")
```

- [ ] **Step 4: Implement staged orchestration**

`run_analysis` must load config, read inputs, validate, write validation even when blocked, normalize counters, calculate metrics, create the analysis window, run available modules, create stable findings, and serialize Pydantic models with UTF-8 and `ensure_ascii=False`. It must write to `<run-id>.partial`, atomically rename to `<run-id>` only after the core artifacts succeed, and refuse to overwrite an existing completed run.

- [ ] **Step 5: Add blocked, repeat-run, and no-finding tests**

Assert that blocking validation produces `blocking=True` and no unsupported evidence, two runs with the same explicit `now` do not overwrite one another, and a valid small dataset returns no findings without throwing an unexpected exception.

Run: `python -m pytest tests/integration/test_pipeline.py -v`

Expected: all tests pass.

- [ ] **Step 6: Commit pipeline orchestration**

```bash
git add src/metriccue/pipeline.py tests/integration/test_pipeline.py
git commit -m "feat: orchestrate reproducible diagnostic runs"
```

---

### Task 9: Markdown Reports, SVG Charts, and Offline Recommendations

**Files:**
- Create: `src/metriccue/reporting.py`
- Test: `tests/unit/test_reporting.py`
- Test: `tests/integration/test_report_artifacts.py`

**Interfaces:**
- Consumes: run manifest, validation issues, findings, canonical summary tables, and run directory.
- Produces: `render_markdown(...) -> str`, `write_charts(...) -> list[Path]`, and `write_report(run_dir) -> Path`.

- [ ] **Step 1: Write failing traceability and empty-chart tests**

```python
# tests/unit/test_reporting.py
from metriccue.models import Confidence, Finding, FindingLevel
from metriccue.reporting import render_markdown


def test_markdown_cites_finding_id_and_limitations() -> None:
    finding = Finding(
        finding_id="views_decline_001",
        level=FindingLevel.SIGNAL,
        metric="views",
        direction="down",
        current_value=80,
        baseline_value=100,
        absolute_change=-20,
        relative_change=-0.2,
        sample_size=30,
        confidence=Confidence.MEDIUM,
        evidence=["最近7天中位数低于基准"],
        limitations=["数据仅来自一个账号"],
    )

    report = render_markdown([finding], [], {})

    assert "views_decline_001" in report
    assert "数据仅来自一个账号" in report
    assert "假设" not in report
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/unit/test_reporting.py -v`

Expected: collection fails because `metriccue.reporting` does not exist.

- [ ] **Step 3: Implement deterministic Markdown rendering**

Render the eight report sections in the spec. Use finding IDs beside every numerical claim. Render an explicit `当前数据不足以形成可靠诊断` summary when findings are empty. Offline recommendations must map finding metric/direction pairs to a small checked-in dictionary and label every action as a candidate rather than a guaranteed solution.

- [ ] **Step 4: Implement SVG charts with empty-data guards**

Use Matplotlib's non-interactive `Agg` backend. Implement trend, funnel, lifecycle, segment-contribution, and production-cycle charts as separate focused functions. Each function returns `None` and records a skipped-chart reason when required data is absent; no blank chart file is written. Close every figure after saving.

- [ ] **Step 5: Add report artifact integration tests**

Assert generated SVG files contain `<svg`, do not contain `NaN` or `Infinity`, and that every percentage and numeric current/baseline pair in `report.md` can be found in `evidence.json` after formatting.

Run: `python -m pytest tests/unit/test_reporting.py tests/integration/test_report_artifacts.py -v`

Expected: all tests pass.

- [ ] **Step 6: Commit reporting**

```bash
git add src/metriccue/reporting.py tests/unit/test_reporting.py tests/integration/test_report_artifacts.py
git commit -m "feat: generate evidence-linked reports and charts"
```

---

### Task 10: Stable Typer CLI and Exit Codes

**Files:**
- Create: `src/metriccue/cli.py`
- Test: `tests/integration/test_cli.py`

**Interfaces:**
- Consumes: configuration, validation, pipeline, and reporting public functions.
- Produces: Typer `app` and commands `init`, `validate`, `analyze`, `findings`, and `report`.

- [ ] **Step 1: Write failing CLI tests**

```python
# tests/integration/test_cli.py
from pathlib import Path

from typer.testing import CliRunner

from metriccue.cli import app

runner = CliRunner()


def test_init_creates_templates_without_overwriting(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--directory", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / "metriccue.yaml").exists()
    assert (tmp_path / "performance.csv").exists()

    second = runner.invoke(app, ["init", "--directory", str(tmp_path)])
    assert second.exit_code == 2


def test_validate_returns_three_for_blocking_data(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("date,content_id\n2026-09-01,n1\n", encoding="utf-8")

    result = runner.invoke(app, ["validate", str(path), "--json"])

    assert result.exit_code == 3
    assert "missing_required_columns" in result.stdout
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/integration/test_cli.py -v`

Expected: collection fails because `metriccue.cli` does not exist.

- [ ] **Step 3: Implement commands and stable exit translation**

Use Typer arguments typed as `Path` with existence/readability checks. `validate` emits human-readable output by default and JSON under `--json`. `analyze` prints only the completed run directory and concise issue counts. `findings` reads only completed `evidence.json`. `report` regenerates presentation artifacts from saved core evidence without rerunning analysis.

Map expected failures to the specified exit codes: configuration/argument `2`, blocking data `3`, valid no-finding result `4`, and report failure `5`. Unexpected exceptions use `1` without dumping raw rows or environment variables.

- [ ] **Step 4: Run CLI tests and installed smoke test**

Run: `python -m pytest tests/integration/test_cli.py -v`

Expected: all tests pass.

Run: `python -m pip install -e ".[dev]"`

Expected: editable package installs successfully.

Run: `metriccue --help`

Expected: output lists `init`, `validate`, `analyze`, `findings`, and `report`.

- [ ] **Step 5: Commit the CLI**

```bash
git add src/metriccue/cli.py tests/integration/test_cli.py
git commit -m "feat: expose stable MetricCue CLI"
```

---

### Task 11: Synthetic Golden Case and Regression Suite

**Files:**
- Create: `examples/synthetic_xhs/generate.py`
- Create: `examples/synthetic_xhs/README.md`
- Create: `examples/synthetic_xhs/metriccue.yaml`
- Create: `examples/synthetic_xhs/expected_findings.yaml`
- Generate: `examples/synthetic_xhs/performance.csv`
- Generate: `examples/synthetic_xhs/content.csv`
- Generate: `examples/synthetic_xhs/production.csv`
- Test: `tests/golden/test_synthetic_xhs.py`

**Interfaces:**
- Consumes: public CLI and completed run artifacts.
- Produces: deterministic 90-day example with approximately 180 items and a machine-readable expected-finding contract.

- [ ] **Step 1: Write the failing golden acceptance test**

```python
# tests/golden/test_synthetic_xhs.py
import json
from pathlib import Path

import yaml

from metriccue.pipeline import AnalysisRequest, run_analysis


CASE = Path("examples/synthetic_xhs")


def test_planted_problems_are_detected_without_false_high_confidence(tmp_path: Path) -> None:
    expected = yaml.safe_load((CASE / "expected_findings.yaml").read_text(encoding="utf-8"))
    result = run_analysis(
        AnalysisRequest(
            performance_path=CASE / "performance.csv",
            content_path=CASE / "content.csv",
            production_path=CASE / "production.csv",
            config_path=CASE / "metriccue.yaml",
            output_root=tmp_path,
        )
    )
    findings = json.loads((result.run_dir / "evidence.json").read_text(encoding="utf-8"))
    validation = json.loads((result.run_dir / "validation.json").read_text(encoding="utf-8"))
    codes = {item["metric"] for item in findings}
    validation_codes = {item["code"] for item in validation}

    assert set(expected["required_metrics"]).issubset(codes)
    assert set(expected["required_validation_codes"]).issubset(validation_codes)
    assert not any(item["metric"] in expected["forbidden_high_confidence_metrics"] and item["confidence"] == "high" for item in findings)
    assert 2 <= len(json.loads((result.run_dir / "recommendations.json").read_text(encoding="utf-8"))) <= 4
```

- [ ] **Step 2: Run the test and verify fixtures are absent**

Run: `python -m pytest tests/golden/test_synthetic_xhs.py -v`

Expected: test fails because the example files do not exist.

- [ ] **Step 3: Implement the deterministic generator**

Use `random.Random(20260912)` and deterministic dates. Generate 180 content items over 90 days with daily cumulative observations. Encode exactly five planted conditions: long-video mix and completion decline in the last 14 days, tutorial save strength with weak follow conversion, one viral outlier, review wait increasing from about one to three days, and one counter reset plus controlled tag omissions. State in the generator module docstring and `examples/synthetic_xhs/README.md` that every row is synthetic and contains no real account or person data; keep the CSV files standards-compliant without comment rows.

- [ ] **Step 4: Define the golden contract and generate files**

`expected_findings.yaml` must list required finding metrics `completion_rate`, `follow_conversion`, `views`, and `review_wait_hours`; required validation codes `counter_reset` and `missing_segment_value`; and a short list of unrelated forbidden high-confidence metrics. Run `python examples/synthetic_xhs/generate.py` twice and verify `git diff --exit-code` after the second run to prove determinism.

- [ ] **Step 5: Run golden and full tests**

Run: `python -m pytest tests/golden/test_synthetic_xhs.py -v`

Expected: the planted-finding contract passes.

Run: `python -m pytest -v`

Expected: the complete suite passes.

- [ ] **Step 6: Commit the golden case**

```bash
git add examples/synthetic_xhs tests/golden/test_synthetic_xhs.py
git commit -m "test: add synthetic content operations case"
```

---

### Task 12: MetricCue Skill and Contract Tests

**Files:**
- Create: `skills/metriccue/SKILL.md`
- Create: `skills/metriccue/references/cli.md`
- Create: `skills/metriccue/references/evidence.md`
- Create: `skills/metriccue/references/experiment-card.md`
- Test: `tests/integration/test_skill_contract.py`

**Interfaces:**
- Consumes: only the public CLI and saved `manifest.json`, `validation.json`, and `evidence.json`.
- Produces: an installable skill that generates evidence-linked hypotheses and proposed experiment cards without changing engine values.

- [ ] **Step 1: Invoke the required skill-authoring process before editing**

Read and follow both `skill-creator` and `superpowers:writing-skills`. Confirm their current validation commands before creating `SKILL.md`.

- [ ] **Step 2: Write failing static contract tests**

```python
# tests/integration/test_skill_contract.py
from pathlib import Path


SKILL = Path("skills/metriccue/SKILL.md")


def test_skill_uses_only_public_cli_and_preserves_evidence() -> None:
    text = SKILL.read_text(encoding="utf-8")

    for command in ("metriccue validate", "metriccue analyze", "metriccue findings", "metriccue report"):
        assert command in text
    assert "finding_id" in text
    assert "不得重新计算" in text
    assert "事实" in text and "线索" in text and "假设" in text


def test_skill_forbids_external_writes_and_raw_model_handoff() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "不得执行发布、投放、群发" in text
    assert "原始数据" in text
    assert "聚合证据" in text
```

- [ ] **Step 3: Run tests and verify the skill is absent**

Run: `python -m pytest tests/integration/test_skill_contract.py -v`

Expected: tests fail with `FileNotFoundError` for `skills/metriccue/SKILL.md`.

- [ ] **Step 4: Author the skill and focused references**

The skill must trigger for content-operations CSV diagnosis, ask for the business goal and metric semantics, validate before analysis, stop on exit code 3, read aggregate artifacts only, preserve finding IDs and confidence, label explanations as hypotheses, produce experiment cards using the documented schema, and request confirmation before writing task files. It must explicitly prohibit external platform writes and unsupported benchmarks.

- [ ] **Step 5: Run skill validation and contract tests**

Run the exact skill linter/validator prescribed by the current `skill-creator` and `superpowers:writing-skills` instructions.

Run: `python -m pytest tests/integration/test_skill_contract.py -v`

Expected: all contract tests and the skill validator pass.

- [ ] **Step 6: Commit the skill**

```bash
git add skills/metriccue tests/integration/test_skill_contract.py
git commit -m "feat: add evidence-safe MetricCue skill"
```

---

### Task 13: Documentation, User-Test Protocol, CI, and Release Candidate

**Files:**
- Modify: `README.md`
- Create: `README.en.md`
- Create: `LICENSE`
- Create: `CHANGELOG.md`
- Create: `docs/data-contract.md`
- Create: `docs/methodology.md`
- Create: `docs/privacy.md`
- Create: `docs/contributing.md`
- Create: `docs/user-test-protocol.md`
- Create: `.github/workflows/ci.yml`
- Create: `.github/ISSUE_TEMPLATE/bug.yml`
- Create: `.github/ISSUE_TEMPLATE/platform-mapping.yml`
- Create: `.github/ISSUE_TEMPLATE/diagnostic-rule.yml`
- Test: `tests/integration/test_repository_contract.py`

**Interfaces:**
- Consumes: all public commands, example artifacts, methods, and limitations.
- Produces: a reproducible public repository and `v0.1.0-rc1` release-ready state.

- [ ] **Step 1: Write failing repository-contract tests**

```python
# tests/integration/test_repository_contract.py
from pathlib import Path


def test_readme_contains_reproducible_quick_start_and_boundaries() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "metriccue init" in text
    assert "metriccue validate" in text
    assert "metriccue analyze" in text
    assert "不支持" in text
    assert "合成数据" in text
    assert "面试" not in text


def test_required_method_and_privacy_documents_exist() -> None:
    for path in (
        "docs/data-contract.md",
        "docs/methodology.md",
        "docs/privacy.md",
        "docs/contributing.md",
        "docs/user-test-protocol.md",
    ):
        assert Path(path).is_file(), path
```

- [ ] **Step 2: Run tests and verify documentation is absent**

Run: `python -m pytest tests/integration/test_repository_contract.py -v`

Expected: tests fail because README and documentation files do not exist.

- [ ] **Step 3: Write product, method, privacy, and contribution documentation**

The Chinese README must open with product value, an input-to-output visual, generated example, and three-command quick start. Document data contracts, formulas, robust anomaly methods, observational limitations, local processing, model handoff, anonymized issue requirements, supported Python versions, Windows/Ubuntu status, and all explicit non-goals. The English README must describe the same scope without adding unsupported claims.

- [ ] **Step 4: Write the user-test protocol and results template**

Specify the exact task: `Identify the main source of the recent engagement decline and propose one experiment for next week.` Record participant role, completion time, blocked steps, interpretation errors, evidence-trace success, experiment quality, and unprompted feedback. Store only anonymized participant IDs. State that `v0.1.0` is withheld until at least three target users complete the protocol; before then the release is `v0.1.0-rc1`.

- [ ] **Step 5: Add CI and issue templates**

Configure a matrix for `ubuntu-latest` and `windows-latest` with Python `3.11`, `3.12`, and `3.13`. Each job installs `.[dev]`, runs Ruff, mypy, pytest with coverage, builds the package, runs the golden example, and scans generated artifacts for common email/phone patterns. Issue templates must require anonymized reproduction data and reject secrets or personal customer data.

- [ ] **Step 6: Run the complete local release gate**

Run: `python -m ruff format --check .`

Expected: exit code 0.

Run: `python -m ruff check .`

Expected: exit code 0.

Run: `python -m mypy src/metriccue`

Expected: exit code 0.

Run: `python -m pytest --cov=metriccue --cov-report=term-missing --cov-fail-under=80`

Expected: all tests pass and total coverage is at least 80%.

Run: `python -m build`

Expected: wheel and source distribution are created successfully.

Run: `metriccue analyze examples/synthetic_xhs/performance.csv --content examples/synthetic_xhs/content.csv --production examples/synthetic_xhs/production.csv --config examples/synthetic_xhs/metriccue.yaml --output work/release-check`

Expected: a completed run directory is printed and contains manifest, validation, evidence, recommendations, report, and non-empty SVG charts.

- [ ] **Step 7: Verify public name availability again**

Run: `gh search repos "MetricCue in:name" --limit 20 --json fullName,url,updatedAt`

Expected: no conflicting project that would make the name misleading.

Run: `python -m pip index versions metriccue`

Expected: no published distribution. If either check finds a conflict, stop before public release and choose a new name; do not rename mechanically without updating package metadata, CLI, skill, docs, examples, tests, and spec.

- [ ] **Step 8: Commit the release-candidate repository**

```bash
git add README.md README.en.md LICENSE CHANGELOG.md docs .github tests/integration/test_repository_contract.py
git commit -m "docs: prepare MetricCue release candidate"
```

- [ ] **Step 9: Tag only the validated release stage**

Before three completed user tests, create `v0.1.0-rc1`. After at least three completed tests and documented corrections, rerun the complete release gate and create `v0.1.0`. Do not claim measured time savings until the user-test results support the exact claim.

---

## Final Verification Checklist

- [ ] Every spec section maps to at least one task above.
- [ ] `metriccue init`, `validate`, `analyze`, `findings`, and `report` work from an installed package.
- [ ] The golden case detects all planted problems and avoids unrelated high-confidence claims.
- [ ] Every report number traces to `evidence.json` through a finding ID.
- [ ] Blocking data errors prevent unsupported findings while preserving validation output.
- [ ] A no-model environment completes validation, analysis, recommendations, charts, and reports.
- [ ] The skill reads aggregate evidence only and never performs external platform writes.
- [ ] Windows and Ubuntu CI pass on Python 3.11 through 3.13.
- [ ] Documentation states method limitations, privacy boundaries, and all v0.1.0 non-goals.
- [ ] The repository contains no real user, account, customer, or platform credential data.
- [ ] The public name is rechecked immediately before release.
- [ ] The release remains `v0.1.0-rc1` until three target-user tests are complete.
