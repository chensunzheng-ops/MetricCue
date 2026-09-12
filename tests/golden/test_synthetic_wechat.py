import json
from datetime import UTC, datetime
from pathlib import Path

from metriccue.pipeline import AnalysisRequest, run_analysis

CASE = Path("examples/synthetic_wechat")


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
    metrics = {item["metric"] for item in findings}

    assert {"views", "engagement_rate", "review_wait_hours"}.issubset(metrics)
    assert any(
        item["metric"] == "views"
        and item["direction"] == "down"
        and item["segment"].get("topic") == "animation_news"
        for item in findings
    )
    assert not any(item["code"].startswith("sensitive_") for item in validation)
    assert not any(item["code"] == "observation_before_publication" for item in validation)
    assert all(item["finding_id"] for item in findings)
    assert (result.run_dir / "report.md").is_file()
    assert (result.run_dir / "charts" / "finding_changes.svg").is_file()
