import pandas as pd

from metriccue.config import MetricCueConfig
from metriccue.ingestion import InputTables
from metriccue.models import Severity
from metriccue.validation import has_blocking_issues, validate_inputs


def _frame(**overrides: object) -> pd.DataFrame:
    row: dict[str, object] = {
        "date": pd.Timestamp("2026-09-01"),
        "content_id": "n1",
        "platform": "xhs",
        "account_id": "a1",
        "views": 10,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_duplicate_performance_key_is_blocking() -> None:
    frame = pd.concat([_frame(views=10), _frame(views=12)], ignore_index=True)

    issues = validate_inputs(InputTables(performance=frame), MetricCueConfig())

    assert any(
        issue.code == "duplicate_performance_key" and issue.severity is Severity.ERROR
        for issue in issues
    )
    assert has_blocking_issues(issues)


def test_sensitive_column_blocks_model_handoff_but_not_local_analysis() -> None:
    issues = validate_inputs(
        InputTables(performance=_frame(customer_phone="13800000000")),
        MetricCueConfig(),
    )

    issue = next(item for item in issues if item.code == "sensitive_column")
    assert issue.severity is Severity.WARNING
    assert "model" in issue.message.lower()
    assert not has_blocking_issues(issues)


def test_unparseable_required_date_is_blocking() -> None:
    issues = validate_inputs(
        InputTables(performance=_frame(date=pd.NaT)),
        MetricCueConfig(),
    )

    assert any(
        issue.code == "invalid_required_date" and issue.severity is Severity.ERROR
        for issue in issues
    )


def test_negative_metric_is_blocking() -> None:
    issues = validate_inputs(
        InputTables(performance=_frame(views=-1)),
        MetricCueConfig(),
    )

    assert any(
        issue.code == "negative_metric" and issue.severity is Severity.ERROR for issue in issues
    )


def test_observation_before_publication_is_warning() -> None:
    content = pd.DataFrame(
        [
            {
                "content_id": "n1",
                "platform": "xhs",
                "account_id": "a1",
                "published_at": pd.Timestamp("2026-09-02"),
            }
        ]
    )

    issues = validate_inputs(
        InputTables(performance=_frame(), content=content),
        MetricCueConfig(),
    )

    assert any(
        issue.code == "observation_before_publication"
        and issue.severity is Severity.WARNING
        for issue in issues
    )


def test_implausible_funnel_value_is_warning() -> None:
    issues = validate_inputs(
        InputTables(performance=_frame(views=20, impressions=10)),
        MetricCueConfig(),
    )

    assert any(issue.code == "implausible_funnel" for issue in issues)


def test_mixed_percentage_scale_is_warning() -> None:
    frame = pd.concat(
        [_frame(completion_rate=0.25), _frame(content_id="n2", completion_rate=25)],
        ignore_index=True,
    )

    issues = validate_inputs(InputTables(performance=frame), MetricCueConfig())

    assert any(issue.code == "mixed_percentage_scale" for issue in issues)


def test_missing_segment_value_is_warning() -> None:
    content = pd.DataFrame(
        [
            {
                "content_id": "n1",
                "platform": "xhs",
                "account_id": "a1",
                "published_at": pd.Timestamp("2026-08-31"),
                "topic": pd.NA,
            }
        ]
    )

    issues = validate_inputs(
        InputTables(performance=_frame(), content=content),
        MetricCueConfig(),
    )

    assert any(issue.code == "missing_segment_value" for issue in issues)
