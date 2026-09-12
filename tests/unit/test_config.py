from pathlib import Path

import pytest

from metriccue.config import load_config


def test_load_config_applies_documented_defaults(tmp_path: Path) -> None:
    path = tmp_path / "metriccue.yaml"
    path.write_text("data:\n  timezone: Asia/Shanghai\n", encoding="utf-8")

    config = load_config(path)

    assert config.data.timezone == "Asia/Shanghai"
    assert config.data.counter_mode == "cumulative"
    assert config.analysis.current_window_days == 7
    assert config.analysis.baseline_window_days == 28
    assert config.analysis.minimum_contents == 10


def test_unknown_config_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "metriccue.yaml"
    path.write_text("analysis:\n  mystery: true\n", encoding="utf-8")

    with pytest.raises(ValueError, match="mystery"):
        load_config(path)
