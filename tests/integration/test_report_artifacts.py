import json
from pathlib import Path

from metriccue.reporting import write_report


def test_report_reads_saved_evidence_and_writes_nonempty_svg(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (run / "evidence.json").write_text(
        json.dumps(
            [
                {
                    "finding_id": "views_down_001",
                    "level": "signal",
                    "metric": "views",
                    "direction": "down",
                    "current_value": 70,
                    "baseline_value": 100,
                    "absolute_change": -30,
                    "relative_change": -0.3,
                    "sample_size": 14,
                    "confidence": "medium",
                    "segment": {},
                    "evidence": ["decline"],
                    "limitations": [],
                }
            ]
        ),
        encoding="utf-8",
    )
    (run / "validation.json").write_text("[]", encoding="utf-8")
    path = write_report(run)
    svg = run / "charts" / "finding_changes.svg"
    assert path.exists() and "views_down_001" in path.read_text(encoding="utf-8")
    assert svg.exists() and "<svg" in svg.read_text(encoding="utf-8")
    assert "NaN" not in svg.read_text(encoding="utf-8")


def test_empty_evidence_does_not_write_blank_chart(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (run / "evidence.json").write_text("[]", encoding="utf-8")
    (run / "validation.json").write_text("[]", encoding="utf-8")
    write_report(run)
    assert not (run / "charts" / "finding_changes.svg").exists()
