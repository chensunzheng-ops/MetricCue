from pathlib import Path

import pandas as pd

from metriccue.config import MetricCueConfig
from metriccue.ingestion import read_inputs


def test_read_inputs_maps_chinese_columns_and_parses_dates(tmp_path: Path) -> None:
    path = tmp_path / "performance.csv"
    path.write_text(
        "数据日期,笔记ID,平台,账号,曝光数\n2026-09-01,n1,xhs,a1,120\n",
        encoding="utf-8",
    )
    config = MetricCueConfig.model_validate(
        {
            "columns": {
                "date": "数据日期",
                "content_id": "笔记ID",
                "platform": "平台",
                "account_id": "账号",
                "impressions": "曝光数",
            }
        }
    )

    tables = read_inputs(path, None, None, config)

    assert list(tables.performance.columns) == [
        "date",
        "content_id",
        "platform",
        "account_id",
        "impressions",
    ]
    assert tables.performance.loc[0, "date"] == pd.Timestamp("2026-09-01")


def test_read_inputs_parses_production_timestamps(tmp_path: Path) -> None:
    performance = tmp_path / "performance.csv"
    production = tmp_path / "production.csv"
    performance.write_text(
        "date,content_id,platform,account_id,views\n2026-09-01,n1,xhs,a1,10\n",
        encoding="utf-8",
    )
    production.write_text(
        "content_id,review_started_at\nn1,2026-08-31 10:00\n",
        encoding="utf-8",
    )

    tables = read_inputs(performance, None, production, MetricCueConfig())

    assert tables.production is not None
    assert tables.production.loc[0, "review_started_at"] == pd.Timestamp("2026-08-31 10:00")
