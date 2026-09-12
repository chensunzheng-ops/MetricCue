import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal

import pandas as pd

from metriccue import __version__
from metriccue.anomalies import detect_metric_anomalies
from metriccue.config import load_config
from metriccue.ingestion import read_inputs
from metriccue.lifecycle import (
    AnalysisWindow,
    align_content_age,
    build_analysis_window,
    lifecycle_summary,
)
from metriccue.metrics import METRICS, compute_metrics, normalize_counters
from metriccue.models import Confidence, Finding, FindingLevel, RunManifest, Severity
from metriccue.production import analyze_production
from metriccue.recommendations import build_recommendations
from metriccue.reporting import write_report
from metriccue.segments import compare_segments, decompose_change, detect_aggregate_reversal
from metriccue.validation import has_blocking_issues, validate_inputs


@dataclass(frozen=True)
class AnalysisRequest:
    performance_path: Path
    output_root: Path
    content_path: Path | None = None
    production_path: Path | None = None
    config_path: Path | None = None
    now: datetime | None = None


@dataclass(frozen=True)
class RunResult:
    run_dir: Path
    finding_count: int
    blocking: bool


class ReportGenerationError(RuntimeError):
    pass


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _available_run_dir(root: Path, base: str) -> Path:
    candidate = root / base
    index = 1
    while candidate.exists() or candidate.with_name(candidate.name + ".partial").exists():
        candidate = root / f"{base}-{index:03d}"
        index += 1
    return candidate


def _content_analysis(
    measured: pd.DataFrame,
    content: pd.DataFrame,
    window: AnalysisWindow,
    minimum: int,
    data_quality: float,
) -> tuple[list[Finding], dict[str, object]]:
    keys = ["platform", "account_id", "content_id"]
    dimensions = [
        name for name in ("content_type", "topic", "campaign", "author") if name in content
    ]
    columns = [*keys, *dimensions]
    if "published_at" in content:
        columns.append("published_at")
    joined = measured.merge(content[columns], on=keys, how="left", validate="many_to_one")
    metadata: dict[str, object] = {}
    if "published_at" in joined:
        aligned = align_content_age(measured, content)
        summary = lifecycle_summary(
            aligned, [metric for metric in ("views", "completion_rate") if metric in aligned]
        )
        metadata["lifecycle_summary"] = summary.to_dict(orient="records")
    dates = pd.to_datetime(joined["date"], errors="coerce")
    joined["period"] = "outside"
    joined.loc[dates.between(window.baseline_start, window.baseline_end), "period"] = "baseline"
    joined.loc[dates.between(window.current_start, window.current_end), "period"] = "current"
    findings: list[Finding] = []
    decomposition_count = 0
    contribution_summaries: list[dict[str, object]] = []
    for metric in ("views", "completion_rate", "follow_conversion"):
        if metric not in joined:
            continue
        for dimension in dimensions:
            comparisons = compare_segments(joined, dimension, metric, "period", minimum)
            for comparison in comparisons:
                change = comparison.relative_difference
                if not comparison.eligible or change is None or abs(change) < 0.1:
                    continue
                direction: Literal["up", "down"] = "down" if change < 0 else "up"
                label = "".join(
                    character if character.isalnum() else "_" for character in comparison.segment
                )
                findings.append(
                    Finding(
                        finding_id=f"segment_{dimension}_{label}_{metric}_{direction}_001",
                        level=FindingLevel.SIGNAL,
                        metric=metric,
                        direction=direction,
                        current_value=comparison.current_median,
                        baseline_value=comparison.baseline_median,
                        absolute_change=comparison.current_median - comparison.baseline_median,
                        relative_change=change,
                        sample_size=comparison.sample_size,
                        confidence=Confidence.LOW if data_quality < 0.8 else Confidence.MEDIUM,
                        segment={dimension: comparison.segment},
                        evidence=[f"Segment coverage is {comparison.coverage:.1%}."],
                        limitations=["Segment comparison is observational, not causal."],
                    )
                )
            eligible_segments = {
                comparison.segment for comparison in comparisons if comparison.eligible
            }
            subset = joined.loc[
                joined["period"].isin(["baseline", "current"])
                & joined[dimension].astype(str).isin(eligible_segments)
            ].dropna(subset=[dimension, metric])
            content_level = subset.groupby([dimension, *keys, "period"], as_index=False)[
                metric
            ].median()
            pivot = content_level.pivot_table(
                index=dimension, columns="period", values=metric, aggfunc="median"
            )
            if content_level.empty or not {"baseline", "current"}.issubset(pivot.columns):
                continue
            common = pivot.dropna().index
            counts = content_level.groupby([dimension, "period"]).size().unstack(fill_value=0)
            baseline = pd.DataFrame(
                {
                    "segment": common.astype(str),
                    "value": pivot.loc[common, "baseline"].to_numpy(),
                    "weight": (
                        counts.loc[common, "baseline"] / counts.loc[common, "baseline"].sum()
                    ).to_numpy(),
                }
            )
            current = pd.DataFrame(
                {
                    "segment": common.astype(str),
                    "value": pivot.loc[common, "current"].to_numpy(),
                    "weight": (
                        counts.loc[common, "current"] / counts.loc[common, "current"].sum()
                    ).to_numpy(),
                }
            )
            if not baseline.empty and not current.empty:
                decomposition = decompose_change(baseline, current)
                contribution_summaries.append(
                    {
                        "dimension": dimension,
                        "metric": metric,
                        "within_effect": float(decomposition["within_effect"].sum()),
                        "mix_effect": float(decomposition["mix_effect"].sum()),
                    }
                )
                aggregate_baseline = float(
                    content_level.loc[content_level["period"].eq("baseline"), metric].median()
                )
                aggregate_current = float(
                    content_level.loc[content_level["period"].eq("current"), metric].median()
                )
                reversal = detect_aggregate_reversal(
                    pivot.loc[common, ["baseline", "current"]].reset_index(drop=True),
                    aggregate_current - aggregate_baseline,
                )
                if reversal:
                    findings.append(
                        Finding(
                            finding_id=f"aggregate_reversal_{dimension}_{metric}_001",
                            level=FindingLevel.SIGNAL,
                            metric=metric,
                            direction="mixed",
                            current_value=aggregate_current,
                            baseline_value=aggregate_baseline,
                            absolute_change=aggregate_current - aggregate_baseline,
                            relative_change=(
                                None
                                if aggregate_baseline == 0
                                else (aggregate_current - aggregate_baseline) / aggregate_baseline
                            ),
                            sample_size=int(
                                content_level.loc[content_level["period"].eq("current"), keys]
                                .drop_duplicates()
                                .shape[0]
                            ),
                            confidence=Confidence.LOW,
                            segment={"dimension": dimension},
                            evidence=[
                                "Aggregate direction opposes every eligible segment direction."
                            ],
                            limitations=[
                                "Possible aggregate reversal requires human review; it is not causal."
                            ],
                        )
                    )
                decomposition_count += 1
    metadata["contribution_decompositions"] = decomposition_count
    metadata["contribution_summaries"] = contribution_summaries
    return findings, metadata


def run_analysis(request: AnalysisRequest) -> RunResult:
    now = request.now or datetime.now(UTC)
    config = load_config(request.config_path)
    tables = read_inputs(
        request.performance_path, request.content_path, request.production_path, config
    )
    request.output_root.mkdir(parents=True, exist_ok=True)
    final = _available_run_dir(
        request.output_root, now.astimezone(UTC).strftime("%Y-%m-%dT%H%M%SZ")
    )
    partial = final.with_name(final.name + ".partial")
    partial.mkdir()
    issues = validate_inputs(tables, config)
    blocking = has_blocking_issues(issues)
    findings: list[Finding] = []
    enabled: list[str] = []
    run_metadata: dict[str, object] = {}
    skipped: dict[str, str] = {}
    if not blocking:
        normalized, counter_issues = normalize_counters(
            tables.performance, config.data.counter_mode
        )
        issues.extend(counter_issues)
        warning_count = sum(item.severity is Severity.WARNING for item in issues)
        data_quality = max(0.5, 1.0 - 0.1 * warning_count)
        measured = compute_metrics(normalized, config)
        window = build_analysis_window(measured["date"], config, now)
        for metric in [*METRICS, "views", "impressions"]:
            if metric in measured:
                findings.extend(
                    detect_metric_anomalies(
                        measured, metric, window, config, data_quality=data_quality
                    )
                )
        enabled.extend(["metrics", "anomalies"])
        sensitive_handoff = any(
            item.code in {"sensitive_column", "sensitive_value"} for item in issues
        )
        if tables.content is not None and not sensitive_handoff:
            content_findings, content_metadata = _content_analysis(
                measured,
                tables.content,
                window,
                config.analysis.minimum_contents,
                data_quality,
            )
            findings.extend(content_findings)
            run_metadata.update(content_metadata)
            if "published_at" in tables.content:
                enabled.append("lifecycle")
            enabled.extend(["segments", "contribution"])
        elif tables.content is not None:
            skipped.update(
                {
                    "lifecycle": "sensitive fields block content artifact generation",
                    "segments": "sensitive fields block segment label handoff",
                    "contribution": "sensitive fields block segment label handoff",
                }
            )
        if tables.production is not None and "published_at" in tables.production:
            production = tables.production.copy()
            published = production["published_at"].dt.normalize()
            production["period"] = "outside"
            production.loc[
                published.between(window.baseline_start, window.baseline_end), "period"
            ] = "baseline"
            production.loc[
                published.between(window.current_start, window.current_end), "period"
            ] = "current"
            findings.extend(analyze_production(production, config.analysis.minimum_contents))
            enabled.append("production")
    issue_payload = [item.model_dump(mode="json") for item in issues]
    finding_payload = [item.model_dump(mode="json") for item in findings]
    hashes = {"performance": _hash_file(request.performance_path)}
    for name, path in (("content", request.content_path), ("production", request.production_path)):
        if path is not None:
            hashes[name] = _hash_file(path)
    config_hash = (
        _hash_file(request.config_path)
        if request.config_path
        else sha256(config.model_dump_json().encode()).hexdigest()
    )
    dates = tables.performance.get("date")
    manifest = RunManifest(
        run_id=final.name,
        metriccue_version=__version__,
        created_at=now,
        timezone=config.data.timezone,
        input_hashes=hashes,
        config_hash=config_hash,
        data_start=None if dates is None or dates.dropna().empty else str(dates.min().date()),
        data_end=None if dates is None or dates.dropna().empty else str(dates.max().date()),
        enabled_modules=enabled,
        skipped_modules=({"analysis": "blocking validation errors"} if blocking else skipped),
        issue_counts={
            severity.value: sum(item.severity is severity for item in issues)
            for severity in Severity
        },
        metadata=run_metadata,
    )
    _write_json(partial / "manifest.json", manifest.model_dump(mode="json"))
    _write_json(partial / "validation.json", issue_payload)
    _write_json(partial / "evidence.json", finding_payload)
    _write_json(partial / "recommendations.json", build_recommendations(findings))
    try:
        write_report(partial)
    except (OSError, ValueError, KeyError) as exc:
        raise ReportGenerationError(str(exc)) from exc
    partial.rename(final)
    return RunResult(final, len(findings), blocking)
