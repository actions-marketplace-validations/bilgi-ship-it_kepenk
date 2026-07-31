from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "0.2.1"
RELEASE_TAG = f"v{RELEASE_VERSION}"


def test_release_metadata_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    release_notes = (ROOT / "docs/releases/v0.2.1.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    adoption = (ROOT / "docs/adoption.md").read_text(encoding="utf-8")

    assert project["name"] == "kepenk-gate"
    assert project["version"] == RELEASE_VERSION
    assert f"## [{RELEASE_VERSION}] - 2026-07-31" in changelog
    assert release_notes.startswith(f"# Kepenk {RELEASE_TAG}\n")
    assert f"/releases/tag/{RELEASE_TAG}" in readme
    assert f"/archive/refs/tags/{RELEASE_TAG}.zip" in readme
    assert f"/archive/refs/tags/{RELEASE_TAG}.zip" in adoption
