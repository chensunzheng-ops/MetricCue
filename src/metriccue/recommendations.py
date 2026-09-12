from typing import Any

from metriccue.models import Finding


def build_recommendations(findings: list[Finding], limit: int = 4) -> list[dict[str, Any]]:
    candidates = sorted(
        (
            item
            for item in findings
            if item.direction == "down"
            or (item.direction == "up" and item.metric.endswith(("_hours", "_cost")))
        ),
        key=lambda item: abs(item.relative_change or 0),
        reverse=True,
    )[:limit]
    templates = {
        "review_wait_hours": "Test a pre-defined fast review lane while holding publication slots constant.",
        "completion_rate": "Test one opening structure while holding topic, length, title, and cover constant.",
        "follow_conversion": "Test one follow call-to-action while holding the content body constant.",
        "views": "Test one publication slot while holding topic, format, title, and cover constant.",
        "impressions": "Test one distribution-ready packaging variant with a fixed publication slot.",
    }
    return [
        {
            "recommendation_id": f"experiment_{index:03d}",
            "level": "proposed_experiment",
            "finding_ids": [finding.finding_id],
            "hypothesis": templates.get(
                finding.metric,
                f"Test one controlled operational change related to {finding.metric}.",
            ),
            "primary_metric": finding.metric,
            "confidence": finding.confidence.value,
            "limitations": finding.limitations,
            "causal_status": "proposed test; observed association is not causal evidence",
        }
        for index, finding in enumerate(candidates, start=1)
    ]
