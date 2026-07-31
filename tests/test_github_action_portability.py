from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_composite_action_does_not_require_consumer_python_files() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    steps = action["runs"]["steps"]
    setup = next(step for step in steps if step.get("name") == "Set up Python")

    assert setup["uses"].startswith("actions/setup-python@")
    assert setup["with"]["python-version"] == "3.11"
    assert "cache" not in setup["with"]
    assert "cache-dependency-path" not in setup["with"]


def test_composite_action_installs_from_its_own_directory() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    steps = action["runs"]["steps"]
    install = next(step for step in steps if step.get("name") == "Install Kepenk")

    assert "$GITHUB_ACTION_PATH" in install["run"]
