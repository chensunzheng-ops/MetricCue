import re

import pandas as pd

from metriccue.config import MetricCueConfig
from metriccue.ingestion import InputTables
from metriccue.models import Severity, ValidationIssue

REQUIRED_DIMENSIONS = {"date", "content_id", "platform", "account_id"}
SUPPORTED_METRICS = {
    "impressions",
    "views",
    "clicks",
    "likes",
    "comments",
    "saves",
    "shares",
    "completed_views",
    "follows",
    "leads",
    "orders",
    "revenue",
}
SEGMENT_COLUMNS = {"content_type", "topic", "campaign", "author", "tags"}
SENSITIVE_NAME = re.compile(
    r"(^|_)(phone|mobile|email|e-mail|full_name|real_name|姓名|手机|电话|邮箱)($|_)",
    re.IGNORECASE,
)


def _issue(
    code: str,
    severity: Severity,
    message: str,
    table: str,
    rows: list[int] | None = None,
    repair: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        severity=severity,
        message=message,
        table=table,
        rows=[] if rows is None else rows,
        repair=repair,
    )


def _validate_performance(frame: pd.DataFrame) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = sorted(REQUIRED_DIMENSIONS - set(frame.columns))
    if missing:
        issues.append(
            _issue(
                "missing_required_columns",
                Severity.ERROR,
                f"Missing required columns: {', '.join(missing)}",
                "performance",
                repair="Map or add every required dimension.",
            )
        )
    if not (SUPPORTED_METRICS & set(frame.columns)):
        issues.append(
            _issue(
                "missing_supported_metric",
                Severity.ERROR,
                "Performance table has no supported metric.",
                "performance",
                repair="Add at least one supported metric column.",
            )
        )

    key = ["platform", "account_id", "content_id", "date"]
    if set(key).issubset(frame.columns):
        duplicate_rows = frame.index[frame.duplicated(key, keep=False)].tolist()
        if duplicate_rows:
            issues.append(
                _issue(
                    "duplicate_performance_key",
                    Severity.ERROR,
                    "Duplicate platform/account/content/date rows make the grain ambiguous.",
                    "performance",
                    duplicate_rows,
                    "Aggregate or remove duplicate rows before analysis.",
                )
            )

    if "date" in frame and frame["date"].isna().any():
        issues.append(
            _issue(
                "invalid_required_date",
                Severity.ERROR,
                "One or more required dates could not be parsed.",
                "performance",
                frame.index[frame["date"].isna()].tolist(),
                "Use an ISO date such as 2026-09-01.",
            )
        )

    metric_columns = sorted(SUPPORTED_METRICS.intersection(frame.columns))
    for column in metric_columns:
        numeric = pd.to_numeric(frame[column], errors="coerce")
        negative = frame.index[numeric.lt(0)].tolist()
        if negative:
            issues.append(
                _issue(
                    "negative_metric",
                    Severity.ERROR,
                    f"Metric '{column}' contains negative values.",
                    "performance",
                    negative,
                    "Correct negative source values before analysis.",
                )
            )

    for numerator, denominator in (
        ("views", "impressions"),
        ("clicks", "views"),
        ("completed_views", "views"),
        ("orders", "leads"),
    ):
        if numerator in frame and denominator in frame:
            numerator_values = pd.to_numeric(frame[numerator], errors="coerce")
            denominator_values = pd.to_numeric(frame[denominator], errors="coerce")
            affected = frame.index[numerator_values.gt(denominator_values)].tolist()
            if affected:
                issues.append(
                    _issue(
                        "implausible_funnel",
                        Severity.WARNING,
                        f"'{numerator}' exceeds '{denominator}' under the configured funnel semantics.",
                        "performance",
                        affected,
                        "Confirm that both metrics use compatible scopes and counters.",
                    )
                )

    for column in (name for name in frame.columns if str(name).endswith("_rate")):
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        if values.le(1).any() and values.gt(1).any():
            issues.append(
                _issue(
                    "mixed_percentage_scale",
                    Severity.WARNING,
                    f"Rate column '{column}' mixes decimal and percentage scales.",
                    "performance",
                    repair="Express every rate as a decimal between 0 and 1.",
                )
            )
    return issues


def _validate_content_relationship(tables: InputTables) -> list[ValidationIssue]:
    content = tables.content
    if content is None:
        return []
    issues: list[ValidationIssue] = []
    available_segments = SEGMENT_COLUMNS.intersection(content.columns)
    for column in sorted(available_segments):
        if content[column].isna().any():
            issues.append(
                _issue(
                    "missing_segment_value",
                    Severity.WARNING,
                    f"Segment column '{column}' has missing values; affected comparisons will have reduced coverage.",
                    "content",
                    content.index[content[column].isna()].tolist(),
                    "Fill the value or accept reduced segment coverage.",
                )
            )

    join_key = ["platform", "account_id", "content_id"]
    if set(join_key + ["published_at"]).issubset(content.columns) and set(
        join_key + ["date"]
    ).issubset(tables.performance.columns):
        merged = tables.performance.reset_index(names="_performance_row").merge(
            content[join_key + ["published_at"]], on=join_key, how="left"
        )
        invalid = merged.loc[
            merged["published_at"].notna() & merged["date"].lt(merged["published_at"]),
            "_performance_row",
        ].astype(int)
        if not invalid.empty:
            issues.append(
                _issue(
                    "observation_before_publication",
                    Severity.WARNING,
                    "Performance observations occur before the content publication timestamp.",
                    "performance",
                    invalid.tolist(),
                    "Check publication time, timezone, and performance dates.",
                )
            )
    return issues


def _validate_privacy(tables: InputTables) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for table_name, frame in (
        ("performance", tables.performance),
        ("content", tables.content),
        ("production", tables.production),
    ):
        if frame is None:
            continue
        for column in frame.columns:
            if SENSITIVE_NAME.search(str(column)):
                issues.append(
                    _issue(
                        "sensitive_column",
                        Severity.WARNING,
                        f"Column '{column}' may contain personal data; local analysis may continue but model handoff is blocked.",
                        table_name,
                        repair="Remove, anonymize, or explicitly exclude the column.",
                    )
                )
    return issues


def validate_inputs(tables: InputTables, config: MetricCueConfig) -> list[ValidationIssue]:
    del config
    return [
        *_validate_performance(tables.performance),
        *_validate_content_relationship(tables),
        *_validate_privacy(tables),
    ]


def has_blocking_issues(issues: list[ValidationIssue]) -> bool:
    return any(issue.severity is Severity.ERROR for issue in issues)
