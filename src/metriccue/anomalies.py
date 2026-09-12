import numpy as np
import pandas as pd

from metriccue.config import MetricCueConfig
from metriccue.lifecycle import AnalysisWindow
from metriccue.metrics import METRICS
from metriccue.models import Confidence, Finding, FindingLevel


def robust_z_score(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    median = numeric.median()
    mad = (numeric - median).abs().median()
    if pd.isna(mad) or mad == 0:
        iqr = numeric.quantile(0.75) - numeric.quantile(0.25)
        scale = iqr / 1.349 if iqr > 0 else np.nan
        return (numeric - median) / scale
    return 0.67448975 * (numeric - median) / mad


def confidence_for(
    sample_size: int, relative_effect: float, persistent_days: int, data_quality: float
) -> Confidence:
    if sample_size < 10 or data_quality < 0.8:
        return Confidence.LOW
    score = (
        int(sample_size >= 30)
        + int(abs(relative_effect) >= 0.2)
        + int(persistent_days >= 3)
        + int(data_quality >= 0.95)
    )
    if score >= 4:
        return Confidence.HIGH
    if score >= 2:
        return Confidence.MEDIUM
    return Confidence.LOW


def _aggregate_metric(frame: pd.DataFrame, metric: str) -> float | None:
    definition = METRICS.get(metric)
    if definition and {definition.numerator, definition.denominator}.issubset(frame.columns):
        denominator = pd.to_numeric(frame[definition.denominator], errors="coerce").sum()
        if denominator == 0:
            return None
        return float(
            pd.to_numeric(frame[definition.numerator], errors="coerce").sum() / denominator
        )
    if metric not in frame:
        return None
    value = pd.to_numeric(frame[metric], errors="coerce").median()
    return None if pd.isna(value) else float(value)


def detect_metric_anomalies(
    frame: pd.DataFrame,
    metric: str,
    window: AnalysisWindow,
    config: MetricCueConfig,
    data_quality: float = 1.0,
) -> list[Finding]:
    dates = pd.to_datetime(frame["date"], errors="coerce")
    baseline = frame.loc[dates.between(window.baseline_start, window.baseline_end)]
    current = frame.loc[dates.between(window.current_start, window.current_end)]
    sample_size = int(current["content_id"].nunique()) if "content_id" in current else len(current)
    if sample_size < config.analysis.minimum_contents:
        return []
    baseline_value = _aggregate_metric(baseline, metric)
    current_value = _aggregate_metric(current, metric)
    if baseline_value is None or current_value is None or baseline_value == 0:
        return []
    absolute = current_value - baseline_value
    relative = absolute / baseline_value
    if abs(relative) < 0.1:
        return []
    daily_values = (
        current.assign(_date=dates.loc[current.index])
        .groupby("_date", sort=True)
        .apply(lambda group: _aggregate_metric(group, metric), include_groups=False)
    )
    persistent = int(
        (daily_values < baseline_value).sum()
        if relative < 0
        else (daily_values > baseline_value).sum()
    )
    direction = "down" if relative < 0 else "up"
    return [
        Finding(
            finding_id=f"{metric}_{direction}_001",
            level=FindingLevel.SIGNAL,
            metric=metric,
            direction=direction,
            current_value=current_value,
            baseline_value=baseline_value,
            absolute_change=absolute,
            relative_change=relative,
            sample_size=sample_size,
            confidence=confidence_for(sample_size, relative, persistent, data_quality),
            evidence=[
                f"Current window differs from baseline by {relative:.1%}.",
                f"Direction persisted on {persistent} current-window days.",
            ],
            limitations=[],
        )
    ]
