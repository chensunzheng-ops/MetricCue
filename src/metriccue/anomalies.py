from typing import Literal

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


def robust_score_against(reference: pd.Series, value: float) -> float:
    numeric = pd.to_numeric(reference, errors="coerce").dropna()
    median = float(numeric.median())
    mad = float((numeric - median).abs().median())
    if mad > 0:
        return 0.67448975 * (value - median) / mad
    iqr = float(numeric.quantile(0.75) - numeric.quantile(0.25))
    if iqr > 0:
        return (value - median) / (iqr / 1.349)
    if value == median:
        return 0.0
    return float("inf") if value > median else float("-inf")


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
    daily_values = pd.Series(
        [
            value
            for _, group in current.assign(_date=dates.loc[current.index]).groupby(
                "_date", sort=True
            )
            if (value := _aggregate_metric(group, metric)) is not None
        ],
        dtype=float,
    )
    persistent = int(
        (daily_values < baseline_value).sum()
        if relative < 0
        else (daily_values > baseline_value).sum()
    )
    baseline_daily = pd.Series(
        [
            value
            for _, group in baseline.assign(_date=dates.loc[baseline.index]).groupby(
                "_date", sort=True
            )
            if (value := _aggregate_metric(group, metric)) is not None
        ],
        dtype=float,
    )
    robust_score: float | None = None
    if len(baseline_daily) >= 4:
        robust_score = robust_score_against(baseline_daily, current_value)
    direction: Literal["up", "down"] = "down" if relative < 0 else "up"
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
            confidence=(
                Confidence.LOW
                if robust_score is not None and abs(robust_score) < 2
                else confidence_for(sample_size, relative, persistent, data_quality)
            ),
            evidence=[
                f"Current window differs from baseline by {relative:.1%}.",
                f"Direction persisted on {persistent} current-window days.",
                *(
                    []
                    if robust_score is None
                    else [f"Robust median/MAD score is {robust_score:.2f}."]
                ),
            ],
            limitations=(
                []
                if data_quality >= 0.8
                else ["Data-quality warnings force low confidence for this signal."]
            ),
        )
    ]
