from typing import Literal

import pandas as pd

from metriccue.models import Confidence, Finding, FindingLevel

TIMESTAMP_COLUMNS = [
    "idea_started_at",
    "brief_completed_at",
    "draft_completed_at",
    "review_started_at",
    "review_completed_at",
    "scheduled_at",
    "published_at",
]


def _hours(end: pd.Series, start: pd.Series) -> pd.Series:
    result = (end - start).dt.total_seconds() / 3600
    return result.mask(result.lt(0))


def derive_production_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in TIMESTAMP_COLUMNS:
        if column in result:
            result[column] = pd.to_datetime(result[column], errors="coerce")
    pairs = {
        "review_wait_hours": ("review_completed_at", "review_started_at"),
        "publication_delay_hours": ("published_at", "scheduled_at"),
        "total_cycle_hours": ("published_at", "idea_started_at"),
    }
    for output, (end, start) in pairs.items():
        if end in result and start in result:
            result[output] = _hours(result[end], result[start])
    if "published_at" in result and "scheduled_at" in result:
        result["is_on_time"] = result["published_at"].le(result["scheduled_at"])
    return result


def analyze_production(frame: pd.DataFrame, minimum_contents: int = 10) -> list[Finding]:
    derived = derive_production_metrics(frame)
    if "period" not in derived:
        return []
    findings: list[Finding] = []
    for metric in (
        "total_cycle_hours",
        "review_wait_hours",
        "publication_delay_hours",
        "revision_count",
        "production_cost",
    ):
        if metric not in derived:
            continue
        baseline = pd.to_numeric(
            derived.loc[derived["period"].eq("baseline"), metric], errors="coerce"
        ).dropna()
        current = pd.to_numeric(
            derived.loc[derived["period"].eq("current"), metric], errors="coerce"
        ).dropna()
        if len(current) < minimum_contents or baseline.empty:
            continue
        before, now = float(baseline.median()), float(current.median())
        if before == 0 or abs((now - before) / before) < 0.1:
            continue
        change = (now - before) / before
        direction: Literal["up", "down"] = "up" if change > 0 else "down"
        findings.append(
            Finding(
                finding_id=f"{metric}_{direction}_001",
                level=FindingLevel.SIGNAL,
                metric=metric,
                direction=direction,
                current_value=now,
                baseline_value=before,
                absolute_change=now - before,
                relative_change=change,
                sample_size=len(current),
                confidence=Confidence.MEDIUM,
                evidence=[f"Current median differs from baseline by {change:.1%}."],
                limitations=[
                    "Production timing and content performance are observational, not causal."
                ],
            )
        )
    return findings
