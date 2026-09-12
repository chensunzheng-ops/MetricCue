import json
from pathlib import Path
from typing import Annotated

import typer

from metriccue.config import load_config
from metriccue.ingestion import read_inputs
from metriccue.pipeline import AnalysisRequest, run_analysis
from metriccue.reporting import write_report
from metriccue.validation import has_blocking_issues, validate_inputs

app = typer.Typer(help="Evidence-first diagnostics for content operations data.")


@app.command()
def init(directory: Annotated[Path, typer.Option("--directory")] = Path(".")) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    targets = [directory / "metriccue.yaml", directory / "performance.csv"]
    if any(path.exists() for path in targets):
        typer.echo("Refusing to overwrite existing templates.", err=True)
        raise typer.Exit(2)
    targets[0].write_text(
        "data:\n  counter_mode: cumulative\n  timezone: Asia/Shanghai\nanalysis:\n  current_window_days: 7\n  baseline_window_days: 28\n  minimum_contents: 10\n",
        encoding="utf-8",
    )
    targets[1].write_text(
        "date,content_id,platform,account_id,impressions,views\n", encoding="utf-8"
    )
    typer.echo(str(directory.resolve()))


@app.command()
def validate(
    performance: Path, config: Path | None = None, json_output: bool = typer.Option(False, "--json")
) -> None:
    loaded = load_config(config)
    issues = validate_inputs(read_inputs(performance, None, None, loaded), loaded)
    if json_output:
        typer.echo(
            json.dumps([item.model_dump(mode="json") for item in issues], ensure_ascii=False)
        )
    else:
        for issue in issues:
            typer.echo(f"[{issue.severity.value}] {issue.code}: {issue.message}")
    if has_blocking_issues(issues):
        raise typer.Exit(3)


@app.command()
def analyze(
    performance: Path,
    output: Annotated[Path, typer.Option("--output")] = Path("runs"),
    content: Path | None = None,
    production: Path | None = None,
    config: Path | None = None,
) -> None:
    result = run_analysis(AnalysisRequest(performance, output, content, production, config))
    typer.echo(str(result.run_dir.resolve()))
    if result.blocking:
        raise typer.Exit(3)
    if result.finding_count == 0:
        raise typer.Exit(4)


@app.command()
def findings(run_dir: Path, json_output: bool = typer.Option(False, "--json")) -> None:
    text = (run_dir / "evidence.json").read_text(encoding="utf-8")
    typer.echo(text if json_output else f"{len(json.loads(text))} findings")


@app.command("report")
def report_command(run_dir: Path, format_name: str = typer.Option("markdown", "--format")) -> None:
    if format_name != "markdown":
        typer.echo("Only markdown is supported in v0.1.0.", err=True)
        raise typer.Exit(2)
    try:
        typer.echo(str(write_report(run_dir).resolve()))
    except (OSError, ValueError, KeyError) as exc:
        typer.echo(f"Report generation failed: {exc}", err=True)
        raise typer.Exit(5) from exc


if __name__ == "__main__":
    app()
