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
