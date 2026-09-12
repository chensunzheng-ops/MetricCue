import json
from datetime import UTC, datetime
from pathlib import Path

from metriccue.pipeline import AnalysisRequest, run_analysis


def test_pipeline_writes_traceable_immutable_artifacts(
    tmp_path: Path, minimal_performance_csv: Path
) -> None:
    output = tmp_path / "runs"
    request = AnalysisRequest(
        performance_path=minimal_performance_csv,
        output_root=output,
        now=datetime(2026, 8, 15, tzinfo=UTC),
    )
    first = run_analysis(request)
    second = run_analysis(request)
    assert first.run_dir != second.run_dir
    manifest = json.loads((first.run_dir / "manifest.json").read_text(encoding="utf-8"))
    evidence = json.loads((first.run_dir / "evidence.json").read_text(encoding="utf-8"))
    assert manifest["input_hashes"]["performance"]
    assert all(item["finding_id"] for item in evidence)
    assert (first.run_dir / "validation.json").exists()


def test_blocking_data_preserves_validation_without_findings(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text("date,content_id\n2026-08-01,n1\n", encoding="utf-8")
    result = run_analysis(
        AnalysisRequest(source, tmp_path / "runs", now=datetime(2026, 8, 15, tzinfo=UTC))
    )
    assert result.blocking
    assert json.loads((result.run_dir / "evidence.json").read_text(encoding="utf-8")) == []
    assert json.loads((result.run_dir / "validation.json").read_text(encoding="utf-8"))
