from pathlib import Path

from kepenk.engine import PolicyEngine
from kepenk.models import Action
from kepenk.policy import load_policy

POLICY_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "powershell"
    / "kepenk.yaml"
)


def _engine() -> PolicyEngine:
    return PolicyEngine(load_policy(POLICY_PATH))


def test_destructive_windows_deletes_are_denied() -> None:
    engine = _engine()
    commands = [
        'pwsh -NoProfile -Command "Remove-Item C:\\work -Recurse -Force"',
        "pwsh -Command 'ri C:\\temp -r -Force'",
        "cmd /c rd C:\\work /s /q",
    ]

    for command in commands:
        decision = engine.evaluate(Action(type="shell", command=command))
        assert decision.effect == "deny"


def test_remote_or_publish_actions_require_approval() -> None:
    engine = _engine()
    commands = [
        "git push origin main",
        'pwsh -NoProfile -Command "Publish-Module -Path .\\dist"',
        "dotnet nuget push package.nupkg --source nuget.org",
        "npm publish",
    ]

    for command in commands:
        decision = engine.evaluate(Action(type="shell", command=command))
        assert decision.effect == "approval"


def test_tests_and_read_only_inspection_are_allowed() -> None:
    engine = _engine()
    commands = [
        'pwsh -NoProfile -Command "Invoke-Pester"',
        "dotnet test",
        'pwsh -NoProfile -Command "Get-ChildItem src"',
        'pwsh -NoProfile -Command "Get-Content README.md"',
        "git status --short",
    ]

    for command in commands:
        decision = engine.evaluate(Action(type="shell", command=command))
        assert decision.effect == "allow"


def test_non_recursive_remove_item_uses_default_approval() -> None:
    decision = _engine().evaluate(
        Action(type="shell", command='pwsh -Command "Remove-Item .\\build.log"')
    )
    assert decision.effect == "approval"
