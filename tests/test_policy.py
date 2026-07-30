from pathlib import Path

import pytest

from kepenk.errors import PolicyError
from kepenk.policy import load_policy


def test_duplicate_rule_ids_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "policy.yaml"
    path.write_text(
        """
version: 1
rules:
  - id: repeated
    effect: allow
    match: {action: shell}
  - id: repeated
    effect: deny
    match: {action: shell}
""",
        encoding="utf-8",
    )
    with pytest.raises(PolicyError, match="duplicate rule id"):
        load_policy(path)


def test_unknown_match_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "policy.yaml"
    path.write_text(
        """
version: 1
rules:
  - id: invalid
    effect: allow
    match: {magic: true}
""",
        encoding="utf-8",
    )
    with pytest.raises(PolicyError, match="unsupported match keys"):
        load_policy(path)
