from metriccue.models import Confidence, Finding, FindingLevel


def test_finding_serializes_stable_evidence_shape() -> None:
    finding = Finding(
        finding_id="engagement_rate_decline_001",
        level=FindingLevel.SIGNAL,
        metric="engagement_rate",
        direction="down",
        current_value=0.044,
        baseline_value=0.062,
        absolute_change=-0.018,
        relative_change=-0.2903225806,
        sample_size=47,
        confidence=Confidence.MEDIUM,
        evidence=["连续5天低于历史中位数"],
        limitations=["当前窗口样本有限"],
    )

    payload = finding.model_dump(mode="json")

    assert payload["finding_id"] == "engagement_rate_decline_001"
    assert payload["level"] == "signal"
    assert payload["confidence"] == "medium"
