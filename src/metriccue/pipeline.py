import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from metriccue import __version__
from metriccue.anomalies import detect_metric_anomalies
from metriccue.config import load_config
from metriccue.ingestion import read_inputs
from metriccue.lifecycle import build_analysis_window
from metriccue.metrics import METRICS, compute_metrics, normalize_counters
from metriccue.models import Finding, RunManifest, Severity
from metriccue.production import analyze_production
from metriccue.reporting import write_report
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


def run_analysis(request: AnalysisRequest) -> RunResult:
    now = request.now or datetime.now(UTC)
    request.output_root.mkdir(parents=True, exist_ok=True)
    final = _available_run_dir(
        request.output_root, now.astimezone(UTC).strftime("%Y-%m-%dT%H%M%SZ")
    )
    partial = final.with_name(final.name + ".partial")
    partial.mkdir()
    config = load_config(request.config_path)
    tables = read_inputs(
        request.performance_path, request.content_path, request.production_path, config
    )
    issues = validate_inputs(tables, config)
    blocking = has_blocking_issues(issues)
    findings: list[Finding] = []
    enabled: list[str] = []
    if not blocking:
        normalized, counter_issues = normalize_counters(
            tables.performance, config.data.counter_mode
        )
        issues.extend(counter_issues)
        measured = compute_metrics(normalized, config)
        window = build_analysis_window(measured["date"], config, now)
        for metric in [*METRICS, "views", "impressions"]:
            if metric in measured:
                findings.extend(detect_metric_anomalies(measured, metric, window, config))
        enabled.extend(["metrics", "anomalies"])
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
        skipped_modules={"analysis": "blocking validation errors"} if blocking else {},
        issue_counts={
            severity.value: sum(item.severity is severity for item in issues)
            for severity in Severity
        },
    )
    _write_json(partial / "manifest.json", manifest.model_dump(mode="json"))
    _write_json(partial / "validation.json", issue_payload)
    _write_json(partial / "evidence.json", finding_payload)
    _write_json(partial / "recommendations.json", [])
    write_report(partial)
    partial.rename(final)
    return RunResult(final, len(findings), blocking)
