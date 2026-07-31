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
        ("npm-package-maintenance.yaml", "npm test", "allow"),
        ("npm-package-maintenance.yaml", "npm publish", "approval"),
        ("npm-package-maintenance.yaml", "npm unpublish kepenk-demo", "deny"),
        ("pypi-release-maintenance.yaml", "python -m twine check dist/*", "allow"),
        ("pypi-release-maintenance.yaml", "twine upload dist/*", "approval"),
        (
            "pypi-release-maintenance.yaml",
            "twine upload --repository-url http://packages.example dist/*",
            "deny",
        ),
        ("terraform-infrastructure.yaml", "terraform validate", "allow"),
        ("terraform-infrastructure.yaml", "terraform apply plan.tfplan", "approval"),
        ("terraform-infrastructure.yaml", "terraform apply -auto-approve", "deny"),
    ],
)
def test_second_policy_pack_batch(
    policy_name: str,
    command: str,
    expected: str,
) -> None:
    assert _decision(policy_name, command) == expected
