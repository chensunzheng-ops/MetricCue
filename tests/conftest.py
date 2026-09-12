from pathlib import Path

import pytest


@pytest.fixture
def minimal_performance_csv(tmp_path: Path) -> Path:
    path = tmp_path / "performance.csv"
    rows = ["date,content_id,platform,account_id,views"]
    for day in range(1, 15):
        rows.append(f"2026-08-{day:02d},n{day},xhs,a1,{100 if day < 8 else 70}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path
