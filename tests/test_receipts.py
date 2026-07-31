from __future__ import annotations

import copy
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from kepenk.cli import EXIT_USAGE
from kepenk.cli import main as cli_main
from kepenk.models import Action
from kepenk.policy import load_policy
from kepenk.receipts import (
    MAX_RECEIPT_LIFETIME_SECONDS,
    ReceiptError,
    create_approval_receipt,
    generate_receipt_key_pair,
    load_receipt,
    load_receipt_private_key,
    load_receipt_public_key,
    policy_sha256,
    receipt_sha256,
    verify_approval_receipt,
    write_receipt,
)

ISSUED_AT = datetime(2026, 7, 31, 12, 0, 0, tzinfo=UTC)


def _policy_data(
    audit_path: Path,
    *,
    effect: str = "approval",
    reason: str = "Push requires approval",
) -> dict[str, Any]:
    return {
        "version": 1,
        "default": "deny",
        "audit": {"path": str(audit_path)},
        "rules": [
            {
                "id": "require-push-approval",
                "effect": effect,
                "reason": reason,
                "match": {
                    "action": "shell",
                    "repository_glob": "example/project",
                    "command_regex": r"^git push origin main$",
                },
            },
            {
                "id": "allow-status",
                "effect": "allow",
                "reason": "Status is read only",
                "match": {"action": "shell", "command_regex": r"^git status$"},
            },
        ],
    }


def _write_policy(
    tmp_path: Path,
    *,
    name: str = "kepenk.yaml",
    effect: str = "approval",
    reason: str = "Push requires approval",
    formatted: bool = False,
) -> Path:
    path = tmp_path / name
    data = _policy_data(tmp_path / "audit.jsonl", effect=effect, reason=reason)
    rendered = yaml.safe_dump(data, sort_keys=formatted, indent=4 if formatted else 2)
    if formatted:
        rendered = "# semantic formatting change only\n" + rendered
    path.write_text(rendered, encoding="utf-8")
    return path


def _action(**changes: Any) -> Action:
    values: dict[str, Any] = {
        "type": "shell",
        "command": "git push origin main",
        "path": None,
        "host": None,
        "repository": "example/project",
        "metadata": {"workflow": "release", "attempt": 1},
    }
    values.update(changes)
    return Action(**values)


def _bundle(tmp_path: Path):
    policy = load_policy(_write_policy(tmp_path))
    private_key = Ed25519PrivateKey.generate()
    action = _action()
    receipt = create_approval_receipt(
        policy,
        action,
        private_key,
        nonce="run-123/action-1",
        expires_in=600,
        now=ISSUED_AT,
    )
    return policy, private_key, action, receipt


def test_valid_receipt_binds_all_security_inputs(tmp_path: Path) -> None:
    policy, private_key, action, receipt = _bundle(tmp_path)

    result = verify_approval_receipt(
        receipt,
        policy,
        action,
        private_key.public_key(),
        nonce="run-123/action-1",
        now=ISSUED_AT + timedelta(seconds=30),
    )

    assert result["valid"] is True
    assert result["algorithm"] == "Ed25519"
    assert result["decision"] == {
        "effect": "approval",
        "reason": "Push requires approval",
        "rule_id": "require-push-approval",
    }
    assert result["action"] == action.to_dict()
    assert result["policy_sha256"] == policy_sha256(policy)
    assert result["receipt_sha256"] == receipt_sha256(receipt)
    assert len(result["receipt_sha256"]) == 64


def test_policy_digest_is_semantic_and_mutation_is_rejected(tmp_path: Path) -> None:
    original = load_policy(_write_policy(tmp_path, name="original.yaml"))
    same = load_policy(_write_policy(tmp_path, name="same.yaml", formatted=True))
    mutated = load_policy(
        _write_policy(tmp_path, name="mutated.yaml", reason="Changed approval reason")
    )
    assert policy_sha256(original) == policy_sha256(same)
    assert policy_sha256(original) != policy_sha256(mutated)

    private_key = Ed25519PrivateKey.generate()
    action = _action()
    receipt = create_approval_receipt(
        original,
        action,
        private_key,
        nonce="policy-mutation",
        now=ISSUED_AT,
    )
    with pytest.raises(ReceiptError, match="policy digest"):
        verify_approval_receipt(
            receipt,
            mutated,
            action,
            private_key.public_key(),
            nonce="policy-mutation",
            now=ISSUED_AT + timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "mutated",
    [
        _action(type="deployment"),
        _action(command="git push origin other"),
        _action(path="src/release.py"),
        _action(host="git.example.com"),
        _action(repository="other/project"),
        _action(metadata={"workflow": "release", "attempt": 2}),
    ],
)
def test_action_mutation_is_rejected(tmp_path: Path, mutated: Action) -> None:
    policy, private_key, _expected, receipt = _bundle(tmp_path)
    with pytest.raises(ReceiptError, match="structured action"):
        verify_approval_receipt(
            receipt,
            policy,
            mutated,
            private_key.public_key(),
            nonce="run-123/action-1",
            now=ISSUED_AT + timedelta(seconds=1),
        )


def test_replay_context_wrong_key_expiry_and_future_time_are_rejected(
    tmp_path: Path,
) -> None:
    policy, private_key, action, receipt = _bundle(tmp_path)

    cases = [
        (
            "nonce",
            private_key.public_key(),
            "another-run",
            ISSUED_AT + timedelta(seconds=1),
        ),
        (
            "key ID",
            Ed25519PrivateKey.generate().public_key(),
            "run-123/action-1",
            ISSUED_AT + timedelta(seconds=1),
        ),
        (
            "expired",
            private_key.public_key(),
            "run-123/action-1",
            ISSUED_AT + timedelta(seconds=600),
        ),
        (
            "future",
            private_key.public_key(),
            "run-123/action-1",
            ISSUED_AT - timedelta(seconds=61),
        ),
    ]
    for message, public_key, nonce, now in cases:
        with pytest.raises(ReceiptError, match=message):
            verify_approval_receipt(
                receipt,
                policy,
                action,
                public_key,
                nonce=nonce,
                now=now,
            )


def test_signed_envelope_mutations_and_unsigned_receipts_fail(tmp_path: Path) -> None:
    policy, private_key, action, receipt = _bundle(tmp_path)

    bad_signature = copy.deepcopy(receipt)
    first = bad_signature["signature"][0]
    bad_signature["signature"] = (
        ("A" if first != "A" else "B") + bad_signature["signature"][1:]
    )

    bad_payload = copy.deepcopy(receipt)
    bad_payload["payload"]["decision"]["reason"] = "Mutated reason"

    bad_algorithm = copy.deepcopy(receipt)
    bad_algorithm["algorithm"] = "none"

    unknown = copy.deepcopy(receipt)
    unknown["extra"] = True

    unsigned = copy.deepcopy(receipt)
    unsigned["signature"] = ""

    for value in (bad_signature, bad_payload, bad_algorithm, unknown, unsigned):
        with pytest.raises(ReceiptError):
            verify_approval_receipt(
                value,
                policy,
                action,
                private_key.public_key(),
                nonce="run-123/action-1",
                now=ISSUED_AT + timedelta(seconds=1),
            )


def test_only_approval_can_be_signed_and_lifetime_is_bounded(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.generate()
    for effect in ("allow", "deny"):
        policy = load_policy(_write_policy(tmp_path, name=f"{effect}.yaml", effect=effect))
        with pytest.raises(ReceiptError, match=f"got {effect}"):
            create_approval_receipt(
                policy,
                _action(),
                private_key,
                nonce=effect,
                now=ISSUED_AT,
            )

    policy = load_policy(_write_policy(tmp_path, name="approval.yaml"))
    for invalid in (0, -1, MAX_RECEIPT_LIFETIME_SECONDS + 1):
        with pytest.raises(ReceiptError, match="expires_in"):
            create_approval_receipt(
                policy,
                _action(),
                private_key,
                nonce="lifetime",
                expires_in=invalid,
                now=ISSUED_AT,
            )


def test_key_and_receipt_files_are_strict_private_and_not_logged(tmp_path: Path) -> None:
    private_path = tmp_path / "keys" / "private.pem"
    public_path = tmp_path / "keys" / "public.pem"
    key_id = generate_receipt_key_pair(private_path, public_path)
    private_key = load_receipt_private_key(private_path)
    public_key = load_receipt_public_key(public_path)
    assert key_id.startswith("sha256:")
    assert private_key.public_key().public_bytes_raw() == public_key.public_bytes_raw()
    assert b"BEGIN PRIVATE KEY" in private_path.read_bytes()
    assert b"BEGIN PUBLIC KEY" in public_path.read_bytes()
    if os.name == "posix":
        assert private_path.stat().st_mode & 0o777 == 0o600

    policy = load_policy(_write_policy(tmp_path))
    action = _action()
    receipt = create_approval_receipt(
        policy,
        action,
        private_key,
        nonce="file-test",
        now=ISSUED_AT,
    )
    receipt_path = tmp_path / "receipts" / "approval.json"
    write_receipt(receipt, receipt_path)
    assert load_receipt(receipt_path) == receipt
    assert private_key.private_bytes_raw() not in receipt_path.read_bytes()
    assert not (tmp_path / "audit.jsonl").exists()
    if os.name == "posix":
        assert receipt_path.stat().st_mode & 0o777 == 0o600

    with pytest.raises(ReceiptError, match="already exists"):
        generate_receipt_key_pair(private_path, public_path)
    with pytest.raises(ReceiptError, match="must be different"):
        generate_receipt_key_pair(tmp_path / "same.pem", tmp_path / "same.pem")
    with pytest.raises(ReceiptError, match="already exists"):
        write_receipt(receipt, receipt_path)

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b"x" * 1_048_577)
    with pytest.raises(ReceiptError, match="exceeds"):
        load_receipt(oversized)


def test_cli_key_create_verify_are_separate_from_execution(tmp_path: Path, capsys) -> None:
    policy_path = _write_policy(tmp_path)
    private_path = tmp_path / "private.pem"
    public_path = tmp_path / "public.pem"
    receipt_path = tmp_path / "approval.json"

    assert (
        cli_main(
            [
                "generate-receipt-key",
                "--private-key",
                str(private_path),
                "--public-key",
                str(public_path),
            ]
        )
        == 0
    )
    key_output = json.loads(capsys.readouterr().out)
    assert key_output["created"] is True
    assert "BEGIN PRIVATE KEY" not in json.dumps(key_output)

    action_args = [
        "--action",
        "shell",
        "--command",
        "git push origin main",
        "--repository",
        "example/project",
        "--metadata",
        "workflow=release",
    ]
    assert (
        cli_main(
            [
                "--policy",
                str(policy_path),
                "create-receipt",
                "--private-key",
                str(private_path),
                "--nonce",
                "cli-run/action-1",
                "--output",
                str(receipt_path),
                *action_args,
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == ""
    assert not (tmp_path / "audit.jsonl").exists()

    assert (
        cli_main(
            [
                "--policy",
                str(policy_path),
                "verify-receipt",
                "--receipt",
                str(receipt_path),
                "--public-key",
                str(public_path),
                "--nonce",
                "cli-run/action-1",
                *action_args,
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["valid"] is True
    assert not (tmp_path / "audit.jsonl").exists()

    assert (
        cli_main(
            [
                "--policy",
                str(policy_path),
                "verify-receipt",
                "--receipt",
                str(receipt_path),
                "--public-key",
                str(public_path),
                "--nonce",
                "another-run/action-1",
                *action_args,
            ]
        )
        == EXIT_USAGE
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "nonce" in captured.err
