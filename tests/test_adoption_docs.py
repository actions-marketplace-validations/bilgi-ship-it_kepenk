from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_adopter_registry_separates_independent_and_founding_team_projects() -> None:
    registry = _read("ADOPTERS.md")

    assert "## Independent adopters" in registry
    assert "## Founding-team pilots" in registry
    assert "No verified independent adopters are listed yet" in registry
    assert "bilgi-ship-it/ustaca-ai" in registry
    assert (
        "Kepenk v0.4.0 GitHub Action, repository context, policy tests, "
        "and offline evidence validation"
        in registry
    )
    assert "docs/case-studies/ustaca-ai.md" in registry
    assert ".kepenk/adoption.json" in registry
    assert "2026-07-31" in registry
    assert "do not count as independent adoption" in registry
    assert "| Repository | Evidence | Integration | Maintainer | Verified |" in registry
    assert "Stars, forks, downloads" in registry


def test_adoption_guide_has_short_path_and_evidence_rules() -> None:
    guide = _read("docs/adoption.md")

    assert "## First decision in five commands" in guide
    assert "## Verification checklist" in guide
    assert "## Submit adoption evidence" in guide
    assert "Founding-team pilots and independent adopters" in guide
    assert "ADOPTERS.md" in guide


def test_adopter_submission_assets_exist() -> None:
    case_study = _read("docs/case-study-template.md")
    template = _read(".github/PULL_REQUEST_TEMPLATE/adopter.md")

    assert "Public repository" in case_study
    assert "Public integration link" in case_study
    assert "independent adopter or founding-team pilot" in case_study
    assert "Public evidence permalink" in template
    assert "I maintain this repository" in template
    assert "Founding-team work is not presented as independent adoption" in template


def test_ustaca_ai_case_study_is_reproducible_and_honestly_classified() -> None:
    case_study = _read("docs/case-studies/ustaca-ai.md")

    assert "founding-team pilot — not independent adoption" in case_study
    assert "Kepenk version:** `v0.4.0`" in case_study
    assert "Eight-case policy regression suite" in case_study
    assert "Version-1 adoption manifest" in case_study
    assert "Successful public workflow run" in case_study
    assert "actions/runs/30642673639" in case_study
    assert "The policy suite should report eight passing cases" in case_study
    assert 'adoption evidence should return `"valid": true`' in case_study
    assert "What the evidence does not show" in case_study
    assert "production-security certification" in case_study
    assert "does not prove that" in case_study
    assert "does not prove ownership, identity, URL availability" in case_study


def test_adoption_evidence_guide_links_real_founding_team_validation() -> None:
    guide = _read("docs/adoption-evidence.md")

    assert '"kepenk_version": "v0.4.0"' in guide
    assert "ustaca-ai/blob/main/.kepenk/adoption.json" in guide
    assert "actions/runs/30642673639" in guide
    assert "founding-team evidence rather than independent adoption" in guide


def test_readme_and_contributing_link_to_adoption_flow() -> None:
    readme = _read("README.md")
    contributing = _read("CONTRIBUTING.md")

    for target in (
        "docs/adoption.md",
        "ADOPTERS.md",
        "docs/case-study-template.md",
        "docs/case-studies/ustaca-ai.md",
        ".github/PULL_REQUEST_TEMPLATE/adopter.md",
    ):
        assert target in readme

    assert "docs/adoption.md" in contributing
    assert "ADOPTERS.md" in contributing
    assert ".github/PULL_REQUEST_TEMPLATE/adopter.md" in contributing
