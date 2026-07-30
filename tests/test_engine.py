from pathlib import Path

from kepenk.engine import PolicyEngine
from kepenk.models import Action
from kepenk.policy import load_policy


def _policy(tmp_path: Path, text: str):
    path = tmp_path / "policy.yaml"
    path.write_text(text, encoding="utf-8")
    return load_policy(path)


def test_first_matching_rule_wins(tmp_path: Path) -> None:
    policy = _policy(
        tmp_path,
        """
version: 1
default: approval
rules:
  - id: deny-push-main
    effect: deny
    reason: protected branch
    match:
      action: shell
      command_regex: 'git push.*main'
  - id: approve-push
    effect: approval
    reason: review first
    match:
      action: shell
      command_regex: 'git push'
""",
    )
    decision = PolicyEngine(policy).evaluate(Action(type="shell", command="git push origin main"))
    assert decision.effect == "deny"
    assert decision.rule_id == "deny-push-main"


def test_default_applies_when_no_rule_matches(tmp_path: Path) -> None:
    policy = _policy(tmp_path, "version: 1\ndefault: approval\nrules: []\n")
    decision = PolicyEngine(policy).evaluate(Action(type="shell", command="echo hello"))
    assert decision.effect == "approval"
    assert decision.rule_id is None


def test_path_glob_and_metadata(tmp_path: Path) -> None:
    policy = _policy(
        tmp_path,
        """
version: 1
default: deny
rules:
  - id: allow-generated-doc
    effect: allow
    reason: generated docs are safe
    match:
      action: filesystem.write
      path_glob: 'docs/generated/*'
      metadata:
        source: codex
""",
    )
    action = Action(
        type="filesystem.write",
        path="docs/generated/index.md",
        metadata={"source": "codex"},
    )
    assert PolicyEngine(policy).evaluate(action).effect == "allow"
