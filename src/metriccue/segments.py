from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SegmentComparison:
    dimension: str
    segment: str
    sample_size: int
    current_median: float
    baseline_median: float
    q25: float
    q75: float
    relative_difference: float | None
    effect_size: float | None
    coverage: float
    eligible: bool


def decompose_change(baseline: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    merged = baseline.merge(
        current, on="segment", suffixes=("_baseline", "_current"), validate="one_to_one"
    )
    merged["within_effect"] = (
        0.5
        * (merged["weight_baseline"] + merged["weight_current"])
        * (merged["value_current"] - merged["value_baseline"])
    )
    merged["mix_effect"] = (
        0.5
        * (merged["value_baseline"] + merged["value_current"])
        * (merged["weight_current"] - merged["weight_baseline"])
    )
    return merged


def detect_aggregate_reversal(grouped: pd.DataFrame, aggregate_change: float) -> bool:
    changes = grouped["current"] - grouped["baseline"]
    if changes.empty or aggregate_change == 0 or changes.eq(0).any():
        return False
    return bool(
        (changes.gt(0).all() and aggregate_change < 0)
        or (changes.lt(0).all() and aggregate_change > 0)
    )


def compare_segments(
    frame: pd.DataFrame, dimension: str, metric: str, period_column: str, minimum_contents: int
) -> list[SegmentComparison]:
    results: list[SegmentComparison] = []
    clean = frame.dropna(subset=[dimension, metric])
    identity = [name for name in ("platform", "account_id", "content_id") if name in clean]
    if "content_id" in identity:
        clean = (
            clean.groupby([dimension, *identity, period_column])[metric]
            .median()
            .to_frame(name=metric)
            .reset_index()
        )
        total = len(clean[identity].drop_duplicates())
    else:
        total = len(clean)
    for segment, group in clean.groupby(dimension):
        baseline = pd.to_numeric(
            group.loc[group[period_column].eq("baseline"), metric], errors="coerce"
        ).dropna()
        current = pd.to_numeric(
            group.loc[group[period_column].eq("current"), metric], errors="coerce"
        ).dropna()
        if baseline.empty or current.empty:
            continue
        base_median = float(baseline.median())
        current_median = float(current.median())
        results.append(
            SegmentComparison(
                dimension,
                str(segment),
                int(
                    len(group.loc[group[period_column].eq("current"), identity].drop_duplicates())
                    if "content_id" in identity
                    else len(current)
                ),
                current_median,
                base_median,
                float(current.quantile(0.25)),
                float(current.quantile(0.75)),
                None if base_median == 0 else (current_median - base_median) / base_median,
                None,
                (
                    len(group[identity].drop_duplicates()) / total
                    if total and "content_id" in identity
                    else len(group) / total
                    if total
                    else 0.0
                ),
                (
                    len(group.loc[group[period_column].eq("current"), identity].drop_duplicates())
                    if "content_id" in identity
                    else len(current)
                )
                >= minimum_contents,
            )
        )
    return results
