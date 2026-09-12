from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from metriccue.config import MetricCueConfig
from metriccue.lifecycle import align_content_age, build_analysis_window, lifecycle_summary


def test_window_excludes_incomplete_today() -> None:
    dates = pd.Series(pd.date_range("2026-08-01", "2026-09-12", freq="D"))
    now = datetime(2026, 9, 12, 15, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    window = build_analysis_window(dates, MetricCueConfig(), now)
    assert str(window.current_end.date()) == "2026-09-11"
    assert str(window.current_start.date()) == "2026-09-05"
    assert str(window.baseline_start.date()) == "2026-08-08"


def test_content_age_aligns_items_by_days_since_publish() -> None:
    performance = pd.DataFrame(
        [
            {
                "date": "2026-09-03",
                "platform": "xhs",
                "account_id": "a1",
                "content_id": "n1",
                "views": 20,
            }
        ]
    )
    content = pd.DataFrame(
        [{"platform": "xhs", "account_id": "a1", "content_id": "n1", "published_at": "2026-09-01"}]
    )
    result = align_content_age(performance, content)
    assert result.loc[0, "content_age_days"] == 2


def test_lifecycle_summary_reports_hand_checked_quartiles() -> None:
    frame = pd.DataFrame({"content_age_days": [1, 1, 1, 1], "views": [10, 20, 30, 40]})
    result = lifecycle_summary(frame, ["views"])
    row = result.iloc[0]
    assert row["count"] == 4
    assert row["median"] == 25
    assert row["q25"] == 17.5
    assert row["q75"] == 32.5
