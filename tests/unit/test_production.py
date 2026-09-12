import pandas as pd

from metriccue.production import derive_production_metrics


def test_derives_review_wait_and_publication_delay_hours() -> None:
    frame = pd.DataFrame(
        [
            {
                "content_id": "n1",
                "idea_started_at": "2026-09-01 09:00",
                "review_started_at": "2026-09-02 09:00",
                "review_completed_at": "2026-09-03 09:00",
                "scheduled_at": "2026-09-03 10:00",
                "published_at": "2026-09-03 16:00",
            }
        ]
    )
    result = derive_production_metrics(frame)
    assert result.loc[0, "review_wait_hours"] == 24
    assert result.loc[0, "publication_delay_hours"] == 6
    assert result.loc[0, "total_cycle_hours"] == 55


def test_negative_duration_is_left_missing() -> None:
    frame = pd.DataFrame(
        [
            {
                "content_id": "n1",
                "review_started_at": "2026-09-03",
                "review_completed_at": "2026-09-02",
            }
        ]
    )
    result = derive_production_metrics(frame)
    assert pd.isna(result.loc[0, "review_wait_hours"])
