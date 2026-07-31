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
    return PolicyEngine(policy).evaluate(Action(type="shell", command=command)).effect


@pytest.mark.parametrize(
    ("policy_name", "command", "expected"),
    [
        ("database-migrations.yaml", "alembic current", "allow"),
        ("database-migrations.yaml", "alembic upgrade head", "approval"),
        ("database-migrations.yaml", 'psql -c "DROP TABLE users"', "deny"),
        ("filesystem-cleanup.yaml", "find . -type f -print", "allow"),
        ("filesystem-cleanup.yaml", "rm -rf build", "approval"),
        ("filesystem-cleanup.yaml", "sudo rm -rf /", "deny"),
        ("read-only-repository-inspection.yaml", "git status", "allow"),
        (
            "read-only-repository-inspection.yaml",
            "git push origin main",
            "deny",
        ),
        (
            "read-only-repository-inspection.yaml",
            "python -m pytest",
            "deny",
        ),
        ("ci-cd-release.yaml", "kubectl get deployments", "allow"),
        ("ci-cd-release.yaml", "kubectl apply -f deploy.yaml", "approval"),
        (
            "ci-cd-release.yaml",
            "kubectl delete namespace production",
            "deny",
        ),
    ],
)
def test_final_policy_pack_batch(
    policy_name: str,
    command: str,
    expected: str,
) -> None:
    assert _decision(policy_name, command) == expected
