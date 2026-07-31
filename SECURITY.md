# Security Policy

## Supported versions

Kepenk is currently alpha software. Only the latest release receives fixes.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could enable policy bypass, command injection, audit forgery, receipt forgery, signature bypass, private-key disclosure, replay across trusted workflow contexts, or unsafe execution.

Report privately through GitHub Security Advisories. Include:

- affected version or commit
- reproduction steps
- expected and actual behavior
- security impact
- suggested mitigation, if available

Do not include production private keys, tokens, credentials, customer data, or unredacted private audit logs in a report. Create a temporary test key and minimal reproduction instead.

## Security boundaries

Kepenk is a policy and approval layer, not a sandbox. It cannot contain a compromised process or prevent direct execution that bypasses the Kepenk wrapper. Deploy it together with least privilege, isolated environments, protected secrets, and operating-system controls.

Repository context is caller-provided data rather than authentication. SARIF output is a redacted report rather than the source audit chain.

A signed approval receipt proves possession of the configured Ed25519 private key for the signed payload. It does not prove human identity, checkout identity, one-time use, or permission from another security control. Receipt consumers that require single use must atomically record consumed nonces or receipt digests in trusted state.

Keep receipt private keys outside the repository and restrict signing access. Kepenk's default examples place private keys under `.kepenk/`, which is ignored by this repository, but each consuming repository must verify its own ignore rules and secret-management controls. Rotate a key immediately when disclosure is suspected and stop trusting receipts issued by the compromised key.
