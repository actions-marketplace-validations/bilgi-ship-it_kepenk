from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_and_contributing_surface_external_entry_points() -> None:
    readme = _read("README.md")
    contributing = _read("CONTRIBUTING.md")
    quickstart = _read("docs/contributor-quickstart.md")

    for target in (
        "docs/contributor-quickstart.md",
        "docs/project-evidence.md",
        "issues/57",
        "issues/58",
        "issues/59",
        "issues/65",
    ):
        assert target in readme

    assert "docs/contributor-quickstart.md" in contributing
    assert "issues/65" in contributing
    assert "good first issue" in quickstart
    assert "help wanted" in quickstart
    assert "Draft pull requests are welcome" in contributing
    assert "not a sandbox" in readme


def test_public_evidence_keeps_ownership_counts_separate() -> None:
    evidence = _read("docs/project-evidence.md")

    assert "Four tagged GitHub releases" in evidence
    assert "verified founding-team pilots: **1**" in evidence
    assert "verified independent adopters: **0**" in evidence
    assert "recorded outside contributors: **0**" in evidence
    assert "another founding-team repository cannot satisfy it" in evidence
    assert "issues/65" in evidence
    assert "does not include telemetry" in evidence


def test_openai_application_drafts_fit_form_limits() -> None:
    plan = _read("docs/openai-application-plan.md")
    drafts = re.findall(r"^> (.+)$", plan, flags=re.MULTILINE)

    assert len(drafts) == 3
    assert all(0 < len(draft) <= 500 for draft in drafts)
    assert "Current draft: 366 characters" in plan
    assert "Current draft: 383 characters" in plan
    assert "Current draft: 378 characters" in plan
    assert "email associated with the applicant's ChatGPT account" in plan
    assert "OpenAI Organization ID" in plan
    assert "must not be committed" in plan
    assert "zero verified independent adopters" in plan
    assert "zero recorded outside contributors" in plan
