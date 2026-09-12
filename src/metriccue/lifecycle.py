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


def build_analysis_window(
    dates: pd.Series, config: MetricCueConfig, now: datetime
) -> AnalysisWindow:
    del dates
    last_complete = pd.Timestamp(now.date())
    if config.analysis.exclude_incomplete_today:
        last_complete -= pd.Timedelta(days=1)
    current_start = last_complete - pd.Timedelta(days=config.analysis.current_window_days - 1)
    baseline_end = current_start - pd.Timedelta(days=1)
    baseline_start = baseline_end - pd.Timedelta(days=config.analysis.baseline_window_days - 1)
    return AnalysisWindow(baseline_start, baseline_end, current_start, last_complete)


def align_content_age(performance: pd.DataFrame, content: pd.DataFrame) -> pd.DataFrame:
    keys = ["platform", "account_id", "content_id"]
    result = performance.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    metadata = content[keys + ["published_at"]].copy()
    metadata["published_at"] = pd.to_datetime(metadata["published_at"], errors="coerce")
    result = result.merge(metadata, on=keys, how="left", validate="many_to_one")
    result["content_age_days"] = (
        result["date"].dt.normalize() - result["published_at"].dt.normalize()
    ).dt.days
    return result


def lifecycle_summary(frame: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    records: list[dict[str, float | int | str]] = []
    for metric in metrics:
        if metric not in frame:
            continue
        grouped = frame.dropna(subset=["content_age_days", metric]).groupby("content_age_days")[
            metric
        ]
        for age, values in grouped:
            records.append(
                {
                    "content_age_days": int(age),
                    "metric": metric,
                    "count": int(values.count()),
                    "median": float(values.median()),
                    "q25": float(values.quantile(0.25)),
                    "q75": float(values.quantile(0.75)),
                }
            )
    return pd.DataFrame.from_records(records)
