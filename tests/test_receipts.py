from __future__ import annotations

import copy
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from kepenk.cli import EXIT_USAGE, main as cli_main
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


def _policy_data(*, push_effect: str = "approval", reason: str = "Push requires approval"):
    return {
        "version": 1,
        "default": "deny",
        "audit": {"path": ".kepenk/audit.jsonl"},
        "rules": [
            {
                "id": "require-push-approval",
                "effect": push_effect,
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
                "match": {
                    "action": "shell",
                    "command_regex": r"^git status$",
                },
            },
        ],
    }


def _write_policy(
    tmp_path: Path,
    *,
    name: str = "kepenk.yaml",
    push_effect: str = "approval",
    reason: str = "Push requires approval",
    formatted: bool = False,
) -> Path:
    path = tmp_path / name
    data = _policy_data(push_effect=push_effect, reason=reason)
    if formatted:
        path.write_text(
            "# same semantic policy with different formatting\n"
            + yaml.safe_dump(data, sort_keys=True, indent=4),
            encoding="utf-8",
        )
    else:
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _approval_action(**changes) -> Action:
    values = {
        "type": "shell",
        "command": "git push origin main",
        "path": None,
        "host": None,
        "repository": "example/project",
        "metadata": {"workflow": "release", "attempt": 1},
    }
    values.update(changes)
    return Action(**values)


def _create(tmp_path: Path):
    policy = load_policy(_write_policy(tmp_path))
    private_key = Ed25519PrivateKey.generate()
    action = _approval_action()
    receipt = create_approval_receipt(
        policy,
        action,
        private_key,
        nonce="run-123/action-1",
        expires_in=600,
        now=ISSUED_AT,
    )
    return policy, private_key, action, receipt


def test_valid_receipt_binds_policy_action_decision_time_nonce_and_key(tmp_path: Path) -> None:
    policy, private_key, action, receipt = _create(tmp_path)

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


def test_policy_digest_is_semantic_and_detects_policy_mutation(tmp_path: Path) -> None:
    first = load_policy(_write_policy(tmp_path, name="first.yaml"))
    same = load_policy(_write_policy(tmp_path, name="same.yaml", formatted=True))
    mutated = load_policy(
        _write_policy(tmp_path, name="mutated.yaml", reason="Changed approval reason")
    )

    assert policy_sha256(first) == policy_sha256(same)
    assert policy_sha256(first) != policy_sha256(mutated)

    private_key = Ed25519PrivateKey.generate()
    action = _approval_action()
    receipt = create_approval_receipt(
        first,
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
    "mutated_action",
    [
        _approval_action(command="git push origin other"),
        _approval_action(repository="other/project"),
        _approval_action(path="src/release.py"),
        _approval_action(host="git.example.com"),
        _approval_action(metadata={"workflow": "release", "attempt": 2}),
        _approval_action(type="deployment"),
    ],
)
def test_action_mutation_is_rejected(tmp_path: Path, mutated_action: Action) -> None:
    policy, private_key, _action, receipt = _create(tmp_path)

    with pytest.raises(ReceiptError, match="structured action|current policy decision"):
        verify_approval_receipt(
            receipt,
            policy,
            mutated_action,
            private_key.public_key(),
            nonce="run-123/action-1",
            now=ISSUED_AT + timedelta(seconds=1),
        )


def test_wrong_nonce_wrong_key_expiry_and_future_issuance_fail_closed(tmp_path: Path) -> None:
    policy, private_key, action, receipt = _create(tmp_path)

    with pytest.raises(ReceiptError, match="nonce"):
        verify_approval_receipt(
            receipt,
            policy,
            action,
            private_key.public_key(),
            nonce="run-999/action-1",
            now=ISSUED_AT + timedelta(seconds=1),
        )

    wrong_key = Ed25519PrivateKey.generate()
    with pytest.raises(ReceiptError, match="key ID"):
        verify_approval_receipt(
            receipt,
            policy,
            action,
            wrong_key.public_key(),
            nonce="run-123/action-1",
            now=ISSUED_AT + timedelta(seconds=1),
        )

    with pytest.raises(ReceiptError, match="expired"):
        verify_approval_receipt(
            receipt,
            policy,
            action,
            private_key.public_key(),
            nonce="run-123/action-1",
            now=ISSUED_AT + timedelta(seconds=600),
        )

    with pytest.raises(ReceiptError, match="future"):
        verify_approval_receipt(
            receipt,
            policy,
            action,
            private_key.public_key(),
            nonce="run-123/action-1",
            now=ISSUED_AT - timedelta(seconds=61),
        )


def test_signature_payload_and_envelope_mutation_fail_closed(tmp_path: Path) -> None:
    policy, private_key, action, receipt = _create(tmp_path)

    mutations = []

    signature = copy.deepcopy(receipt)
    signature["signature"] = "A" + signature["signature"][1:]
    mutations.append(signature)

    payload = copy.deepcopy(receipt)
    payload["payload"]["decision"]["reason"] = "Mutated reason"
    mutations.append(payload)

    algorithm = copy.deepcopy(receipt)
    algorithm["algorithm"] = "none"
    mutations.append(algorithm)

    unknown = copy.deepcopy(receipt)
    unknown["extra"] = True
    mutations.append(unknown)

    unsigned = copy.deepcopy(receipt)
    unsigned["signature"] = ""
    mutations.append(unsigned)

    for mutated in mutations:
        with pytest.raises(ReceiptError):
            verify_approval_receipt(
                mutated,
                policy,
                action,
                private_key.public_key(),
                nonce="run-123/action-1",
                now=ISSUED_AT + timedelta(seconds=1),
            )


def test_receipts_can_only_be_created_for_approval_and_lifetime_is_bounded(
    tmp_path: Path,
) -> None:
    private_key = Ed25519PrivateKey.generate()

    allow_policy = load_policy(_write_policy(tmp_path, name="allow.yaml", push_effect="allow"))
    with pytest.raises(ReceiptError, match="got allow"):
        create_approval_receipt(
            allow_policy,
            _approval_action(),
            private_key,
            nonce="allow",
            now=ISSUED_AT,
        )

    deny_policy = load_policy(_write_policy(tmp_path, name="deny.yaml", push_effect="deny"))
    with pytest.raises(ReceiptError, match="got deny"):
        create_approval_receipt(
            deny_policy,
            _approval_action(),
            private_key,
            nonce="deny",
            now=ISSUED_AT,
        )

    approval_policy = load_policy(_write_policy(tmp_path, name="approval.yaml"))
    for invalid in (0, -1, MAX_RECEIPT_LIFETIME_SECONDS + 1):
        with pytest.raises(ReceiptError, match="expires_in"):
            create_approval_receipt(
                approval_policy,
                _approval_action(),
                private_key,
                nonce="lifetime",
                expires_in=invalid,
                now=ISSUED_AT,
            )


def test_key_generation_uses_expected_formats_permissions_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
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

    with pytest.raises(ReceiptError, match="already exists"):
        generate_receipt_key_pair(private_path, public_path)
    with pytest.raises(ReceiptError, match="must be different"):
        generate_receipt_key_pair(tmp_path / "same.pem", tmp_path / "same.pem")


def test_receipt_file_is_private_sized_strict_and_does_not_touch_audit(tmp_path: Path) -> None:
    policy, private_key, action, receipt = _create(tmp_path)
    receipt_path = tmp_path / "receipts" / "approval.json"
    write_receipt(receipt, receipt_path)

    loaded = load_receipt(receipt_path)
    assert loaded == receipt
    if os.name == "posix":
        assert receipt_path.stat().st_mode & 0o777 == 0o600
    assert not (tmp_path / ".kepenk" / "audit.jsonl").exists()

    private_pem = private_key.private_bytes_raw()
    rendered = receipt_path.read_bytes()
    assert private_pem not in rendered

    with pytest.raises(ReceiptError, match="already exists"):
        write_receipt(receipt, receipt_path)

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b"x" * 1_048_577)
    with pytest.raises(ReceiptError, match="exceeds"):
        load_receipt(oversized)

    verify_approval_receipt(
        loaded,
        policy,
        action,
        private_key.public_key(),
        nonce="run-123/action-1",
        now=ISSUED_AT + timedelta(seconds=1),
    )


def test_cli_key_create_verify_are_separate_from_execution_and_audit(
    tmp_path: Path,
    capsys,
) -> None:
    policy_path = _write_policy(tmp_path)
    private_path = tmp_path / "private.pem"
    public_path = tmp_path / "public.pem"
    receipt_path = tmp_path / "approval.json"

    key_code = cli_main(
        [
            "generate-receipt-key",
            "--private-key",
            str(private_path),
            "--public-key",
            str(public_path),
        ]
    )
    key_output = json.loads(capsys.readouterr().out)
    assert key_code == 0
    assert key_output["created"] is True
    assert "PRIVATE KEY" not in json.dumps(key_output)

    create_code = cli_main(
        [
            "--policy",
            str(policy_path),
            "create-receipt",
            "--private-key",
            str(private_path),
            "--nonce",
            "cli-run/action-1",
            "--action",
            "shell",
            "--command",
            "git push origin main",
            "--repository",
            "example/project",
            "--metadata",
            "workflow=release",
            "--metadata",
            "attempt=1",
            "--output",
            str(receipt_path),
        ]
    )
    assert create_code == 0
    assert capsys.readouterr().out == ""
    assert receipt_path.exists()
    assert not (tmp_path / ".kepenk" / "audit.jsonl").exists()

    verify_code = cli_main(
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
            "--action",
            "shell",
            "--command",
            "git push origin main",
            "--repository",
            "example/project",
            "--metadata",
            "workflow=release",
            "--metadata",
            "attempt=1",
        ]
    )
    verified = json.loads(capsys.readouterr().out)
    assert verify_code == 0
    assert verified["valid"] is True
    assert not (tmp_path / ".kepenk" / "audit.jsonl").exists()

    wrong_nonce_code = cli_main(
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
            "--action",
            "shell",
            "--command",
            "git push origin main",
            "--repository",
            "example/project",
            "--metadata",
            "workflow=release",
            "--metadata",
            "attempt=1",
        ]
    )
    captured = capsys.readouterr()
    assert wrong_nonce_code == EXIT_USAGE
    assert captured.out == ""
    assert "nonce" in captured.err
