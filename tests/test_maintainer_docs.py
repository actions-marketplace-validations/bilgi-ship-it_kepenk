from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_maintainer_policy_has_targets_boundaries_and_measurement() -> None:
    policy = _read("MAINTAINERS.md")

    assert "@bilgi-ship-it" in policy
    assert "not contractual service-level guarantees" in policy
    assert "Private security advisory" in policy
    assert "Pull request" in policy
    assert "Bug report" in policy
    assert "Release cadence" in policy
    assert "Measuring the targets" in policy
    assert "GitHub Security Advisories" in policy
    assert "does not claim a response-rate percentage" in policy


def test_readme_contributing_and_roadmap_link_maintenance_policy() -> None:
    readme = _read("README.md")
    contributing = _read("CONTRIBUTING.md")
    roadmap = _read("ROADMAP.md")

    assert "MAINTAINERS.md" in readme
    assert "MAINTAINERS.md" in contributing
    assert "documented maintainer response and release cadence" in roadmap
    assert "[#55]" in roadmap
