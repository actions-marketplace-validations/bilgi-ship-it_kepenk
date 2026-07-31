# Signed approval receipts

Signed approval receipts are portable proof that a configured Ed25519 private key approved one exact Kepenk policy decision and one exact structured action for a limited time and replay context.

This document defines the threat model and receipt format before implementation.

## Security goal

A verifier with the expected public key, policy, action, nonce, and current time can determine locally and deterministically whether:

- the receipt has a valid Ed25519 signature;
- the signer used the private key corresponding to the expected public key;
- the receipt was issued for the same semantic policy;
- the receipt was issued for the exact structured action and current policy decision;
- the receipt is currently valid;
- the receipt belongs to the expected nonce or replay context.

Receipt generation and receipt verification are separate from command execution. Neither operation launches the proposed action.

## Non-goals

A valid receipt does not prove:

- the legal or real-world identity of the person controlling the key;
- that a human personally reviewed the action;
- that the host, repository, checkout, or runner is trustworthy;
- that the receipt has not already been consumed elsewhere;
- that operating-system permissions, credentials, branch protections, or network controls permit the action;
- that an action should proceed when another security control says no.

A receipt proves only possession of the configured private key at signing time and agreement with the signed payload.

## Threat model

### Action mutation

Changing any structured action field after signing must invalidate verification. This includes `type`, `command`, `path`, `host`, `repository`, and metadata.

### Policy mutation

Changing the semantic policy must invalidate verification. The receipt binds a SHA-256 digest of Kepenk's canonical parsed policy representation, not raw YAML bytes. Formatting and comments may change without changing the digest; rule content, ordering, effects, reasons, matchers, default effect, audit path, or policy version change the digest.

### Decision mutation

The signed payload includes the complete decision effect, rule ID, and reason. Verification reevaluates the expected action against the current policy and requires an exact match. Receipts may be created only for an `approval` decision. A `deny` decision can never be converted into an approval receipt.

### Expiry

Every receipt has `issued_at` and `expires_at` UTC timestamps. Verification rejects an expired receipt, a receipt issued unreasonably in the future, an invalid interval, or a lifetime longer than the supported maximum.

### Replay

Every receipt has a required caller-provided `nonce`. Verification requires the expected nonce and rejects a different value. The nonce should identify a trusted, unique request or workflow execution, such as a protected run ID plus an action sequence number.

Kepenk does not maintain a global used-receipt database. A consumer that needs one-time use must atomically record consumed nonces or receipt digests in its own trusted state. Reusing the same nonce in the same trust domain defeats replay separation and is an integration error.

### Wrong or substituted key

The envelope includes a key ID derived from the raw public key. Verification calculates the expected key ID and requires an exact match before checking the signature. A receipt signed by another key is rejected.

### Unknown fields and algorithm confusion

Receipt version 1 accepts a fixed set of fields. Unknown or missing fields are rejected. The algorithm value must be exactly `Ed25519`; no algorithm negotiation or fallback is performed.

### Key disclosure

Private keys are loaded only from an explicit PEM file. They are never accepted as command-line values, environment variables, policy fields, action metadata, or receipt fields. Kepenk does not print, log, or write private-key bytes.

The private-key file remains the operator's responsibility. Use restricted file permissions, a secrets manager or protected runner storage, key rotation, and limited signing access. Public keys may be distributed to verifiers.

## Standard primitive

Version 1 uses Ed25519 as specified by RFC 8032. The implementation uses the `cryptography` library's Ed25519 sign and verify interfaces and standard PEM key serialization.

## Canonical policy identity

Kepenk constructs this semantic policy object before hashing:

```json
{
  "version": 1,
  "default": "approval",
  "audit_path": ".kepenk/audit.jsonl",
  "rules": [
    {
      "id": "require-push-approval",
      "effect": "approval",
      "reason": "Remote changes require approval.",
      "match": {
        "action": "shell",
        "command_regex": "(^|\\s)git\\s+push(\\s|$)"
      }
    }
  ]
}
```

The object is encoded as UTF-8 JSON with sorted keys and compact separators, then hashed with SHA-256. Rule order remains significant because Kepenk uses first-match-wins evaluation.

## Receipt format version 1

```json
{
  "version": 1,
  "algorithm": "Ed25519",
  "key_id": "sha256:<64 lowercase hexadecimal characters>",
  "payload": {
    "issued_at": "2026-07-31T12:00:00Z",
    "expires_at": "2026-07-31T12:10:00Z",
    "nonce": "workflow-123/action-1",
    "policy_sha256": "<64 lowercase hexadecimal characters>",
    "decision": {
      "effect": "approval",
      "reason": "Remote changes require approval.",
      "rule_id": "require-push-approval"
    },
    "action": {
      "type": "shell",
      "command": "git push origin main",
      "path": null,
      "host": null,
      "repository": "example/project",
      "metadata": {}
    }
  },
  "signature": "<unpadded base64url Ed25519 signature>"
}
```

The signed bytes are the canonical JSON encoding of the envelope without the `signature` field:

```json
{
  "version": 1,
  "algorithm": "Ed25519",
  "key_id": "...",
  "payload": {"...": "..."}
}
```

The signature is unpadded base64url. Verification rejects invalid encoding and requires the Ed25519 signature length expected by the cryptographic implementation.

## Time rules

- timestamps use UTC with a terminal `Z`;
- `expires_at` must be later than `issued_at`;
- the maximum lifetime is 24 hours;
- the CLI defaults to a 10-minute lifetime;
- verification permits at most 60 seconds of future clock skew for `issued_at`;
- an expired receipt fails closed.

## CLI design

### Generate keys

```bash
kepenk generate-receipt-key \
  --private-key .kepenk/approval-private.pem \
  --public-key .kepenk/approval-public.pem
```

The command refuses to overwrite existing files unless `--force` is supplied. On POSIX systems the private key is written with owner-only permissions. The public key uses SubjectPublicKeyInfo PEM; the private key uses unencrypted PKCS8 PEM. Operators needing encrypted or hardware-backed keys should provision them separately and may use the programmatic verification interface where appropriate.

### Create a receipt

```bash
kepenk --policy kepenk.yaml create-receipt \
  --private-key .kepenk/approval-private.pem \
  --nonce workflow-123/action-1 \
  --expires-in 600 \
  --action shell \
  --repository example/project \
  --command "git push origin main" \
  --output .kepenk/receipts/workflow-123-action-1.json
```

Generation reevaluates the action and refuses every effect except `approval`. It does not execute the action and does not append the receipt or key to the audit log.

### Verify a receipt

```bash
kepenk --policy kepenk.yaml verify-receipt \
  --receipt .kepenk/receipts/workflow-123-action-1.json \
  --public-key .kepenk/approval-public.pem \
  --nonce workflow-123/action-1 \
  --action shell \
  --repository example/project \
  --command "git push origin main"
```

Verification loads the current policy, rebuilds the expected action and decision, checks policy identity, nonce, time, key ID, and signature, then returns success without executing the action.

## Exit behavior

- `0`: key generation, receipt creation, or receipt verification succeeded;
- `64`: invalid key, receipt, policy, action, nonce, time, signature, or file operation;
- no receipt command returns `allow`, grants execution, or launches a child process.

## Compatibility

Receipt format version 1 is experimental during the v0.3 line. Patch releases will not reinterpret an existing field or accept an invalid v1 signature. Additive CLI options may be introduced. A breaking envelope or canonicalization change requires a new integer receipt version and migration guidance; version 1 verification must remain available for an overlap period when technically and securely practical.

## Integration boundary

A safe consuming workflow should:

1. construct the canonical action through trusted code;
2. obtain a unique nonce from protected workflow state;
3. evaluate the action and request a receipt only for `approval`;
4. verify with an independently configured public key immediately before execution;
5. atomically mark the nonce or receipt digest as consumed when one-time use is required;
6. execute through a separate least-privilege path only after every surrounding control also succeeds.
