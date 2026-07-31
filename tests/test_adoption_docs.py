from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_adopter_registry_starts_honestly_empty() -> None:
    registry = _read("ADOPTERS.md")

    assert "## Independent adopters" in registry
    assert "## Founding-team pilots" in registry
    assert "No verified independent adopters are listed yet" in registry
    assert "No public founding-team pilot is listed yet" in registry
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


def test_readme_and_contributing_link_to_adoption_flow() -> None:
    readme = _read("README.md")
    contributing = _read("CONTRIBUTING.md")

    for target in (
        "docs/adoption.md",
        "ADOPTERS.md",
        "docs/case-study-template.md",
        ".github/PULL_REQUEST_TEMPLATE/adopter.md",
    ):
        assert target in readme

    assert "docs/adoption.md" in contributing
    assert "ADOPTERS.md" in contributing
    assert ".github/PULL_REQUEST_TEMPLATE/adopter.md" in contributing
