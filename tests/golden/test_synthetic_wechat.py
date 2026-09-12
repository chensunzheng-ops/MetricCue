import json
import runpy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from metriccue.pipeline import AnalysisRequest, run_analysis

CASE = Path("examples/synthetic_wechat")


def test_generator_matches_committed_fixtures_and_is_repeatable(tmp_path: Path) -> None:
    namespace = runpy.run_path(str(CASE / "generate.py"))
    main = namespace["main"]
    main.__globals__["ROOT"] = tmp_path

    main()
    first = {
        name: (tmp_path / name).read_text(encoding="utf-8").splitlines()
        for name in ("performance.csv", "content.csv", "production.csv")
    }
    main()
    second = {name: (tmp_path / name).read_text(encoding="utf-8").splitlines() for name in first}

    assert second == first
    assert first == {name: (CASE / name).read_text(encoding="utf-8").splitlines() for name in first}


def test_wechat_case_traces_engagement_decline_to_operational_signals(
    tmp_path: Path,
) -> None:
    result = run_analysis(
        AnalysisRequest(
            performance_path=CASE / "performance.csv",
            content_path=CASE / "content.csv",
            production_path=CASE / "production.csv",
            config_path=CASE / "metriccue.yaml",
            output_root=tmp_path,
            now=datetime(2026, 9, 12, tzinfo=UTC),
        )
    )

    findings = json.loads((result.run_dir / "evidence.json").read_text(encoding="utf-8"))
    validation = json.loads((result.run_dir / "validation.json").read_text(encoding="utf-8"))
    by_id = {item["finding_id"]: item for item in findings}

    expected_changes = {
        "engagement_rate_down_001": ("down", -0.464),
        "views_down_001": ("down", -0.554),
        "segment_topic_animation_news_views_down_001": ("down", -0.422),
        "review_wait_hours_up_001": ("up", 1.900),
    }
    for finding_id, (direction, relative_change) in expected_changes.items():
        assert by_id[finding_id]["direction"] == direction
        assert by_id[finding_id]["relative_change"] == pytest.approx(relative_change, abs=0.0005)
    assert by_id["segment_topic_animation_news_views_down_001"]["segment"] == {
        "topic": "animation_news"
    }
    assert by_id["review_wait_hours_up_001"]["baseline_value"] == 20
    assert by_id["review_wait_hours_up_001"]["current_value"] == 58
    assert not any(item["code"].startswith("sensitive_") for item in validation)
    assert not any(item["code"] == "observation_before_publication" for item in validation)
    assert all(item["finding_id"] for item in findings)
    assert (result.run_dir / "report.md").is_file()
    assert (result.run_dir / "charts" / "finding_changes.svg").is_file()

    preview = Path("docs/assets/metriccue-wechat-preview.svg").read_text(encoding="utf-8")
    for value in ("-46.4%", "-55.4%", "下降 42.2%", "+190.0%"):
        assert value in preview
    assert "主要指标：审核等待时间" in preview
