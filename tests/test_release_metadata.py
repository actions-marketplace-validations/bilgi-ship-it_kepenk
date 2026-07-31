from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "0.4.0"
RELEASE_TAG = f"v{RELEASE_VERSION}"


def test_release_metadata_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    release_notes = (ROOT / "docs/releases/v0.4.0.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    adoption = (ROOT / "docs/adoption.md").read_text(encoding="utf-8")
    evidence = (ROOT / "docs/project-evidence.md").read_text(encoding="utf-8")
    application = (ROOT / "docs/openai-application-plan.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")

    assert project["name"] == "kepenk-gate"
    assert project["version"] == RELEASE_VERSION
    assert f"## [{RELEASE_VERSION}] - 2026-07-31" in changelog
    assert release_notes.startswith(f"# Kepenk {RELEASE_TAG}\n")
    assert f"/releases/tag/{RELEASE_TAG}" in readme
    assert f"/archive/refs/tags/{RELEASE_TAG}.zip" in readme
    assert f"/archive/refs/tags/{RELEASE_TAG}.zip" in adoption
    assert f"`{RELEASE_TAG}` tag" in adoption
    assert f"Current verified release: [`{RELEASE_TAG}`]" in evidence
    assert "Five tagged GitHub releases" in evidence
    assert f"verified `{RELEASE_TAG}`" in application
    assert f"tagged `{RELEASE_TAG}` GitHub Release" in roadmap
    assert "kepenk validate-adoption" in release_notes
