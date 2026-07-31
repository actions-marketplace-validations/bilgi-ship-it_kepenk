from __future__ import annotations

import json
from pathlib import Path

from kepenk.cli import EXIT_USAGE, _parser
from kepenk.receipts import (
    DEFAULT_RECEIPT_LIFETIME_SECONDS,
    MAX_RECEIPT_LIFETIME_SECONDS,
    RECEIPT_ALGORITHM,
    RECEIPT_VERSION,
)

ROOT = Path(__file__).resolve().parents[1]


def test_receipt_v1_schema_contract() -> None:
    schema = json.loads(
        (ROOT / "schemas/kepenk-approval-receipt-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["properties"]["version"]["const"] == RECEIPT_VERSION == 1
    assert schema["properties"]["algorithm"]["const"] == RECEIPT_ALGORITHM == "Ed25519"
    assert set(schema["required"]) == {
        "version",
        "algorithm",
        "key_id",
        "payload",
        "signature",
    }
    assert set(schema["$defs"]["payload"]["required"]) == {
        "issued_at",
        "expires_at",
        "nonce",
        "policy_sha256",
        "decision",
        "action",
    }
    assert set(schema["$defs"]["decision"]["required"]) == {
        "effect",
        "reason",
        "rule_id",
    }
    assert schema["$defs"]["decision"]["properties"]["effect"]["const"] == "approval"
    assert set(schema["$defs"]["action"]["required"]) == {
        "type",
        "command",
        "path",
        "host",
        "repository",
        "metadata",
    }
    assert schema["properties"]["signature"]["minLength"] == 86
    assert schema["properties"]["signature"]["maxLength"] == 86


def test_receipt_cli_contract_is_separate_from_run() -> None:
    parser = _parser()

    generated = parser.parse_args(
        [
            "generate-receipt-key",
            "--private-key",
            "private.pem",
            "--public-key",
            "public.pem",
        ]
    )
    created = parser.parse_args(
        [
            "--policy",
            "kepenk.yaml",
            "create-receipt",
            "--private-key",
            "private.pem",
            "--nonce",
            "run-1/action-1",
            "--action",
            "shell",
            "--command",
            "git push origin main",
        ]
    )
    verified = parser.parse_args(
        [
            "--policy",
            "kepenk.yaml",
            "verify-receipt",
            "--receipt",
            "receipt.json",
            "--public-key",
            "public.pem",
            "--nonce",
            "run-1/action-1",
            "--action",
            "shell",
            "--command",
            "git push origin main",
        ]
    )
    run = parser.parse_args(["run", "--", "python", "-V"])

    assert generated.subcommand == "generate-receipt-key"
    assert created.subcommand == "create-receipt"
    assert created.expires_in == DEFAULT_RECEIPT_LIFETIME_SECONDS == 600
    assert verified.subcommand == "verify-receipt"
    assert run.subcommand == "run"
    assert not hasattr(run, "receipt")
    assert MAX_RECEIPT_LIFETIME_SECONDS == 86_400
    assert EXIT_USAGE == 64
