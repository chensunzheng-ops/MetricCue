import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from metriccue.pipeline import AnalysisRequest, run_analysis

CASE = Path("examples/synthetic_xhs")


def test_planted_problems_are_detected_without_false_high_confidence(tmp_path: Path) -> None:
    expected = yaml.safe_load((CASE / "expected_findings.yaml").read_text(encoding="utf-8"))
    result = run_analysis(
        AnalysisRequest(
            performance_path=CASE / "performance.csv",
            content_path=CASE / "content.csv",
            production_path=CASE / "production.csv",
            config_path=CASE / "metriccue.yaml",
            output_root=tmp_path,
            now=datetime(2026, 9, 12, tzinfo=UTC),
        )
    )
    findings = json.loads((result.run_dir / "evidence.json").read_text(encoding="utf-8"))
    validation = json.loads((result.run_dir / "validation.json").read_text(encoding="utf-8"))
    metrics = {item["metric"] for item in findings}
    validation_codes = {item["code"] for item in validation}
    assert set(expected["required_metrics"]).issubset(metrics)
    assert set(expected["required_validation_codes"]).issubset(validation_codes)
    assert not any(
        item["metric"] in expected["forbidden_high_confidence_metrics"]
        and item["confidence"] == "high"
        for item in findings
    )
