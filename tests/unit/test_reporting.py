from metriccue.models import Confidence, Finding, FindingLevel
from metriccue.reporting import render_markdown


def test_markdown_cites_finding_id_and_limitations() -> None:
    finding = Finding(
        finding_id="views_decline_001",
        level=FindingLevel.SIGNAL,
        metric="views",
        direction="down",
        current_value=80,
        baseline_value=100,
        absolute_change=-20,
        relative_change=-0.2,
        sample_size=30,
        confidence=Confidence.MEDIUM,
        evidence=["最近7天中位数低于基准"],
        limitations=["数据仅来自一个账号"],
    )
    report = render_markdown([finding], [], {})
    assert "views_decline_001" in report
    assert "80" in report and "100" in report
    assert "数据仅来自一个账号" in report
    assert "假设" not in report


def test_empty_findings_explain_insufficient_evidence() -> None:
    assert "当前数据不足以形成可靠诊断" in render_markdown([], [], {})


def test_report_renders_lifecycle_and_contribution_metadata() -> None:
    report = render_markdown(
        [],
        [],
        {
            "lifecycle_summary": [
                {"content_age_days": 1, "metric": "views", "count": 12, "median": 80}
            ],
            "contribution_summaries": [
                {
                    "dimension": "topic",
                    "metric": "views",
                    "within_effect": -10,
                    "mix_effect": 2,
                }
            ],
        },
    )

    assert "Day 1" in report
    assert "within=-10" in report
