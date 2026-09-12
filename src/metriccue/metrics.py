from dataclasses import dataclass
from typing import Literal

import pandas as pd

from metriccue.config import MetricCueConfig
from metriccue.models import Severity, ValidationIssue

COUNT_COLUMNS = [
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
]
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
    interaction_columns = [
        name for name in ("likes", "comments", "saves", "shares") if name in result
    ]
    if interaction_columns:
        result["interactions"] = result[interaction_columns].fillna(0).sum(axis=1)
    for name, definition in METRICS.items():
        denominator = config.denominators.get(name, definition.denominator)
        if definition.numerator in result and denominator in result:
            result[name] = _safe_divide(
                pd.to_numeric(result[definition.numerator], errors="coerce"),
                pd.to_numeric(result[denominator], errors="coerce"),
            )
    return result


def normalize_counters(
    frame: pd.DataFrame,
    mode: Literal["daily", "cumulative"],
) -> tuple[pd.DataFrame, list[ValidationIssue]]:
    result = frame.copy()
    available_counts = [column for column in COUNT_COLUMNS if column in result]
    for column in available_counts:
        result[column] = pd.to_numeric(result[column], errors="coerce").astype(float)
    if mode == "daily" or not available_counts:
        return result, []

    required = [*KEY_COLUMNS, "date"]
    if not set(required).issubset(result.columns):
        return result, []

    result["_original_index"] = result.index
    result = result.sort_values([*KEY_COLUMNS, "date"], kind="stable")
    issues: list[ValidationIssue] = []

    for column in available_counts:
        differences = result.groupby(KEY_COLUMNS, dropna=False, sort=False)[column].diff()
        first_observation = result.groupby(KEY_COLUMNS, dropna=False, sort=False).cumcount().eq(0)
        increments = differences.where(~first_observation, result[column])
        reset_mask = increments.lt(0)
        if reset_mask.any():
            affected = result.loc[reset_mask, "_original_index"].astype(int).tolist()
            issues.append(
                ValidationIssue(
                    code="counter_reset",
                    severity=Severity.WARNING,
                    message=f"Cumulative metric '{column}' decreased; affected increments were left missing.",
                    table="performance",
                    rows=affected,
                    repair="Confirm whether the source reset, corrected, or changed its counting scope.",
                )
            )
            increments = increments.mask(reset_mask)
        result[column] = increments

    result = result.sort_values("_original_index", kind="stable").set_index("_original_index")
    result.index.name = None
    return result, issues
