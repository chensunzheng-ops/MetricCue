"""Generate a fictional WeChat-style case; no values come from a real account."""

import csv
from datetime import date, datetime, time, timedelta
from pathlib import Path
from random import Random

ROOT = Path(__file__).parent
RANDOM = Random(20260913)


def write(name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    with (ROOT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    performance: list[dict[str, object]] = []
    content: list[dict[str, object]] = []
    production: list[dict[str, object]] = []
    start = date(2026, 6, 14)
    topics = ("game_update", "card_release", "animation_news")

    for index in range(90):
        published = start + timedelta(days=index)
        current = published >= date(2026, 9, 5)
        topic = "animation_news" if current and index % 7 < 5 else topics[index % 3]
        baseline_views = {
            "game_update": 1800,
            "card_release": 1400,
            "animation_news": 1100,
        }[topic]
        current_multiplier = {
            "game_update": 0.72,
            "card_release": 0.68,
            "animation_news": 0.58,
        }[topic]
        views = int(
            baseline_views * (current_multiplier if current else 1.0) + RANDOM.randint(-35, 35)
        )
        engagement_rate = 0.065 if current else 0.12
        content_id = f"article-{index:03d}"
        interactions = int(views * engagement_rate)

        performance.append(
            {
                "date": published,
                "content_id": content_id,
                "platform": "wechat_official_account",
                "account_id": "synthetic-game-content",
                "impressions": views * 2,
                "views": views,
                "likes": int(interactions * 0.45),
                "comments": int(interactions * 0.10),
                "saves": int(interactions * 0.25),
                "shares": interactions
                - int(interactions * 0.45)
                - int(interactions * 0.10)
                - int(interactions * 0.25),
                "follows": int(views * (0.012 if current else 0.02)),
            }
        )
        content.append(
            {
                "content_id": content_id,
                "platform": "wechat_official_account",
                "account_id": "synthetic-game-content",
                # Performance is daily-grain, so metadata uses the same day boundary.
                "published_at": datetime.combine(published, time()),
                "content_type": "article",
                "topic": topic,
                "campaign": "routine_editorial",
            }
        )
        review_started = datetime.combine(published - timedelta(days=3), time(10))
        review_hours = 58 if current else 20
        production.append(
            {
                "content_id": content_id,
                "review_started_at": review_started,
                "review_completed_at": review_started + timedelta(hours=review_hours),
                "scheduled_at": datetime.combine(published, time(20)),
                "published_at": datetime.combine(published, time(20)),
                "revision_count": 3 if current else 1,
            }
        )

    write("performance.csv", list(performance[0]), performance)
    write("content.csv", list(content[0]), content)
    write("production.csv", list(production[0]), production)


if __name__ == "__main__":
    main()
