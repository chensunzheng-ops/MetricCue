from pathlib import Path

from typer.testing import CliRunner

from metriccue.cli import app

runner = CliRunner()


def test_init_creates_templates_without_overwriting(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--directory", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "metriccue.yaml").exists()
    assert (tmp_path / "performance.csv").exists()
    assert runner.invoke(app, ["init", "--directory", str(tmp_path)]).exit_code == 2


def test_validate_returns_three_for_blocking_data(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("date,content_id\n2026-09-01,n1\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", str(path), "--json"])
    assert result.exit_code == 3
    assert "missing_required_columns" in result.stdout


def test_help_lists_public_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("init", "validate", "analyze", "findings", "report"):
        assert command in result.stdout


def test_missing_input_and_invalid_config_return_two(tmp_path: Path) -> None:
    missing = runner.invoke(app, ["validate", str(tmp_path / "missing.csv")])
    assert missing.exit_code == 2

    source = tmp_path / "performance.csv"
    source.write_text(
        "date,content_id,platform,account_id,views\n2026-09-01,n1,xhs,a1,10\n",
        encoding="utf-8",
    )
    config = tmp_path / "bad.yaml"
    config.write_text("unknown: true\n", encoding="utf-8")
    invalid = runner.invoke(app, ["validate", str(source), "--config", str(config)])
    assert invalid.exit_code == 2


def test_findings_rejects_partial_run(tmp_path: Path) -> None:
    partial = tmp_path / "run.partial"
    partial.mkdir()
    (partial / "evidence.json").write_text("[]", encoding="utf-8")

    result = runner.invoke(app, ["findings", str(partial), "--json"])

    assert result.exit_code == 2
