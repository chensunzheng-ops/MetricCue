import pandas as pd

from metriccue.segments import compare_segments, decompose_change, detect_aggregate_reversal


def test_decomposition_separates_mix_and_within_segment_change() -> None:
    baseline = pd.DataFrame(
        {"segment": ["short", "long"], "weight": [0.8, 0.2], "value": [0.08, 0.05]}
    )
    current = pd.DataFrame(
        {"segment": ["short", "long"], "weight": [0.6, 0.4], "value": [0.08, 0.04]}
    )
    result = decompose_change(baseline, current)
    assert result["mix_effect"].sum() < 0
    assert result["within_effect"].sum() < 0
    expected = (0.6 * 0.08 + 0.4 * 0.04) - (0.8 * 0.08 + 0.2 * 0.05)
    assert abs(result[["mix_effect", "within_effect"]].to_numpy().sum() - expected) < 1e-12


def test_detects_aggregate_direction_reversal() -> None:
    grouped = pd.DataFrame({"baseline": [0.10, 0.04], "current": [0.11, 0.05]})
    assert detect_aggregate_reversal(grouped, aggregate_change=-0.01)


def test_does_not_report_reversal_when_segments_are_mixed() -> None:
    grouped = pd.DataFrame({"baseline": [0.10, 0.04], "current": [0.11, 0.03]})
    assert not detect_aggregate_reversal(grouped, aggregate_change=-0.01)


def test_repeated_daily_rows_do_not_inflate_segment_content_sample() -> None:
    frame = pd.DataFrame(
        [
            {"content_id": "n1", "topic": "a", "period": period, "views": value}
            for period, value in (("baseline", 100), ("current", 80), ("current", 75))
        ]
    )

    result = compare_segments(frame, "topic", "views", "period", minimum_contents=2)

    assert result[0].sample_size == 1
    assert not result[0].eligible


def test_content_identity_includes_platform_and_account() -> None:
    frame = pd.DataFrame(
        [
            {
                "platform": platform,
                "account_id": "a1",
                "content_id": "shared",
                "topic": "a",
                "period": period,
                "views": value,
            }
            for platform in ("xhs", "video")
            for period, value in (("baseline", 100), ("current", 80))
        ]
    )

    result = compare_segments(frame, "topic", "views", "period", minimum_contents=2)

    assert result[0].sample_size == 2
    assert result[0].eligible
