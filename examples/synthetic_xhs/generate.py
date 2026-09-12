"""Generate deterministic synthetic data; no row represents a real person or account."""

import csv
from datetime import date, datetime, time, timedelta
from pathlib import Path
from random import Random

ROOT = Path(__file__).parent
RANDOM = Random(20260912)


def write(name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    with (ROOT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    performance, content, production = [], [], []
    start = date(2026, 6, 14)
    for index in range(180):
        published = start + timedelta(days=index // 2)
        current = published >= date(2026, 9, 5)
        tutorial = index % 3 == 0
        long_video = current or index % 4 == 0
        views = (600 if current else 1000) + RANDOM.randint(-30, 30)
        completion_rate = 0.40 if current else 0.70
        follow_rate = 0.01 if current else 0.03
        content_id = f"note-{index:03d}"
        performance.append(
            {
                "date": published,
                "content_id": content_id,
                "platform": "xhs",
                "account_id": "synthetic-a1",
                "impressions": views * 2,
                "views": views,
                "likes": int(views * 0.05),
                "comments": int(views * 0.01),
                "saves": int(views * (0.10 if tutorial else 0.03)),
                "shares": int(views * 0.01),
                "completed_views": int(views * completion_rate),
                "follows": int(views * follow_rate),
            }
        )
        content.append(
            {
                "content_id": content_id,
                "platform": "xhs",
                "account_id": "synthetic-a1",
                "published_at": datetime.combine(published, time(18)),
                "content_type": "video",
                "topic": "tutorial" if tutorial else ("" if index == 20 else "story"),
                "duration_seconds": 75 if long_video else 35,
            }
        )
        review_start = datetime.combine(published - timedelta(days=4), time(9))
        review_hours = 72 if current else 24
        production.append(
            {
                "content_id": content_id,
                "review_started_at": review_start,
                "review_completed_at": review_start + timedelta(hours=review_hours),
                "scheduled_at": datetime.combine(published, time(17)),
                "published_at": datetime.combine(published, time(18)),
                "revision_count": 2,
                "production_cost": 100,
            }
        )
    performance[50]["views"] = 12000
    performance.append({**performance[0], "date": start + timedelta(days=1), "views": 10})
    write("performance.csv", list(performance[0]), performance)
    write("content.csv", list(content[0]), content)
    write("production.csv", list(production[0]), production)


if __name__ == "__main__":
    main()
