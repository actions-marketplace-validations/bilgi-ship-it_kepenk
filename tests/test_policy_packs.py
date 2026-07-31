from __future__ import annotations

from pathlib import Path

import pytest

from kepenk.engine import PolicyEngine
from kepenk.models import Action
from kepenk.policy import load_policy

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "examples" / "policies"


def _decision(policy_name: str, command: str) -> str:
    policy = load_policy(POLICY_DIR / policy_name)
    engine = PolicyEngine(policy)
    return engine.evaluate(Action(type="shell", command=command)).effect


@pytest.mark.parametrize(
    ("policy_name", "command", "expected"),
    [
        ("python-development.yaml", "python -m pytest", "allow"),
        ("python-development.yaml", "python -m pip install requests", "approval"),
        ("python-development.yaml", "sudo rm -rf /", "deny"),
        ("git-maintenance.yaml", "git status", "allow"),
        ("git-maintenance.yaml", "git push origin main", "approval"),
        ("git-maintenance.yaml", "git push --force origin main", "deny"),
        ("docker-maintenance.yaml", "docker ps", "allow"),
        ("docker-maintenance.yaml", "docker build -t app .", "approval"),
        ("docker-maintenance.yaml", "docker volume rm app-data", "deny"),
    ],
)
def test_policy_pack_decisions(policy_name: str, command: str, expected: str) -> None:
    assert _decision(policy_name, command) == expected


def test_every_policy_pack_loads() -> None:
    policies = sorted(POLICY_DIR.glob("*.yaml"))
    assert policies
    for policy_path in policies:
        assert load_policy(policy_path).version == 1
