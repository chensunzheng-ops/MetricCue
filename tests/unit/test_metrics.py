import pandas as pd

from metriccue.config import MetricCueConfig
from metriccue.metrics import compute_metrics, normalize_counters


def _counter_frame(values: list[int]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2026-09-01") + pd.Timedelta(days=index),
                "platform": "xhs",
                "account_id": "a1",
                "content_id": "n1",
                "views": value,
            }
            for index, value in enumerate(values)
        ]
    )


def test_cumulative_values_become_daily_increments() -> None:
    normalized, issues = normalize_counters(_counter_frame([10, 25]), "cumulative")

    assert normalized["views"].tolist() == [10.0, 15.0]
    assert issues == []


def test_counter_reset_is_missing_and_reported() -> None:
    normalized, issues = normalize_counters(_counter_frame([25, 4]), "cumulative")

    assert pd.isna(normalized.loc[1, "views"])
    assert any(issue.code == "counter_reset" for issue in issues)


def test_daily_values_are_not_differenced() -> None:
    normalized, issues = normalize_counters(_counter_frame([10, 25]), "daily")

    assert normalized["views"].tolist() == [10.0, 25.0]
    assert issues == []


def test_zero_denominator_produces_missing_metric() -> None:
    frame = pd.DataFrame(
        [{"views": 0, "likes": 1, "comments": 0, "saves": 0, "shares": 0}]
    )

    result = compute_metrics(frame, MetricCueConfig())

    assert pd.isna(result.loc[0, "engagement_rate"])


def test_interactions_and_default_engagement_rate_are_calculated() -> None:
    frame = pd.DataFrame(
        [{"views": 100, "likes": 4, "comments": 2, "saves": 3, "shares": 1}]
    )

    result = compute_metrics(frame, MetricCueConfig())

    assert result.loc[0, "interactions"] == 10
    assert result.loc[0, "engagement_rate"] == 0.1


def test_configured_denominator_overrides_default() -> None:
    frame = pd.DataFrame(
        [
            {
                "impressions": 200,
                "views": 100,
                "likes": 4,
                "comments": 2,
                "saves": 3,
                "shares": 1,
            }
        ]
    )
    config = MetricCueConfig(denominators={"engagement_rate": "impressions"})

    result = compute_metrics(frame, config)

    assert result.loc[0, "engagement_rate"] == 0.05
