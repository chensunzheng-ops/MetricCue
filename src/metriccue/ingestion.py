from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from metriccue.config import MetricCueConfig

DATE_COLUMNS = {
    "date",
    "published_at",
    "idea_started_at",
    "brief_completed_at",
    "draft_completed_at",
    "review_started_at",
    "review_completed_at",
    "scheduled_at",
}


@dataclass(frozen=True)
class InputTables:
    performance: pd.DataFrame
    content: pd.DataFrame | None = None
    production: pd.DataFrame | None = None


def _read(path: Path, config: MetricCueConfig) -> pd.DataFrame:
    frame = pd.read_csv(path, encoding="utf-8")
    reverse_mapping = {source: canonical for canonical, source in config.columns.items()}
    frame = frame.rename(columns=reverse_mapping)
    for column in DATE_COLUMNS.intersection(frame.columns):
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    return frame


def read_inputs(
    performance_path: Path,
    content_path: Path | None,
    production_path: Path | None,
    config: MetricCueConfig,
) -> InputTables:
    return InputTables(
        performance=_read(performance_path, config),
        content=None if content_path is None else _read(content_path, config),
        production=None if production_path is None else _read(production_path, config),
    )
