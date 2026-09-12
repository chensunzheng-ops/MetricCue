import pandas as pd

from metriccue.anomalies import (
    confidence_for,
    detect_metric_anomalies,
    robust_score_against,
    robust_z_score,
)
from metriccue.config import MetricCueConfig
from metriccue.lifecycle import AnalysisWindow
from metriccue.models import Confidence


def test_viral_outlier_does_not_shift_robust_center() -> None:
    scores = robust_z_score(pd.Series([10, 11, 10, 9, 10, 1000], dtype=float))
    assert abs(scores.iloc[0]) < 1
    assert scores.iloc[-1] > 10


def test_flat_baseline_gives_changed_value_infinite_robust_score() -> None:
    assert robust_score_against(pd.Series([100, 100, 100, 100], dtype=float), 50) == float("-inf")


def test_low_quality_and_small_sample_force_low_confidence() -> None:
    assert confidence_for(5, 0.5, 5, 0.6) is Confidence.LOW


def test_rate_change_uses_summed_counts_not_average_row_rates() -> None:
    rows = []
    for day in pd.date_range("2026-08-01", periods=14):
        current = day >= pd.Timestamp("2026-08-08")
        for index in range(2):
            views = 1000 if index == 0 else 10
            rate = (0.04 if current else 0.08) if index == 0 else 0.5
            rows.append(
                {
                    "date": day,
                    "content_id": f"{day:%d}-{index}",
                    "views": views,
                    "interactions": views * rate,
                }
            )
    frame = pd.DataFrame(rows)
    window = AnalysisWindow(
        pd.Timestamp("2026-08-01"),
        pd.Timestamp("2026-08-07"),
        pd.Timestamp("2026-08-08"),
        pd.Timestamp("2026-08-14"),
    )
    findings = detect_metric_anomalies(frame, "engagement_rate", window, MetricCueConfig())
    assert len(findings) == 1
    assert findings[0].current_value is not None and findings[0].current_value < 0.05
    assert findings[0].direction == "down"


def test_data_quality_penalty_forces_low_confidence() -> None:
    rows = [
        {"date": day, "content_id": f"n{index}", "views": 100 if index < 28 else 50}
        for index, day in enumerate(pd.date_range("2026-08-01", periods=35))
    ]
    window = AnalysisWindow(
        pd.Timestamp("2026-08-01"),
        pd.Timestamp("2026-08-28"),
        pd.Timestamp("2026-08-29"),
        pd.Timestamp("2026-09-04"),
    )

    finding = detect_metric_anomalies(
        pd.DataFrame(rows),
        "views",
        window,
        MetricCueConfig.model_validate({"analysis": {"minimum_contents": 2}}),
        data_quality=0.7,
    )[0]

    assert finding.confidence is Confidence.LOW
    assert any("quality" in item.lower() for item in finding.limitations)
