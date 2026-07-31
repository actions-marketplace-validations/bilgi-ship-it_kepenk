# SARIF audit export

Kepenk can convert an existing verified audit chain into deterministic SARIF 2.1.0. The exporter is offline and does not contact GitHub or another hosted service.

By default, only `deny` decisions become SARIF results. Approval-required decisions can be included explicitly as warnings.

## Export to standard output

```bash
kepenk --policy kepenk.yaml export-sarif \
  --audit .kepenk/audit.jsonl
```

The command writes one SARIF JSON document to standard output.

```bash
kepenk --policy kepenk.yaml export-sarif \
  --audit .kepenk/audit.jsonl \
  > kepenk.sarif
```

## Export to a file

```bash
kepenk --policy kepenk.yaml export-sarif \
  --audit .kepenk/audit.jsonl \
  --output reports/kepenk.sarif
```

Parent directories are created when needed. No status text is written to standard output when `--output` is used.

## Include approval-required decisions

```bash
kepenk --policy kepenk.yaml export-sarif \
  --audit .kepenk/audit.jsonl \
  --output reports/kepenk.sarif \
  --include-approval
```

Mapping:

| Kepenk effect | Default export | SARIF level |
|---|---:|---|
| `allow` | never | none |
| `approval` | only with `--include-approval` | `warning` |
| `deny` | yes | `error` |

Each result includes the matched rule ID, policy reason, action type, audit outcome, and one-based audit event index. A default decision uses a generated rule ID such as `kepenk/default-approval`.

## Integrity behavior

The exporter verifies every `previous_hash` link and `event_hash` before producing output. A missing, malformed, or tampered audit file fails closed with exit code `64`. No partial SARIF document is written to standard output.

A hash-valid event must also contain the expected audit decision structure. Structurally malformed events are refused rather than silently skipped.

## Redaction and privacy

The following fields are not exported:

- command text;
- host;
- repository context;
- metadata keys and values;
- timestamps and event hashes.

The policy reason and rule ID are exported because they explain the finding. Do not place credentials, customer data, tokens, or other secrets in rule IDs or policy reasons.

An action path becomes a SARIF location only when it is a safe relative path. Absolute POSIX paths, Windows drive paths, parent traversal, network paths, and URI schemes are omitted. Kepenk does not attempt to rewrite an unsafe path into a safer-looking value.

SARIF export is a reporting transformation. It does not grant approval, execute an action, modify the audit log, or replace the original hash-chain verification.

## GitHub Actions upload example

The core exporter contains no GitHub-specific behavior. A workflow may generate the file and pass it to GitHub's SARIF upload action:

```yaml
permissions:
  contents: read
  security-events: write

steps:
  - uses: actions/checkout@<reviewed-commit>

  - name: Install Kepenk
    run: >-
      python -m pip install
      "https://github.com/bilgi-ship-it/kepenk/archive/refs/tags/<verified-tag>.zip"

  - name: Export denied actions
    run: >-
      kepenk --policy kepenk.yaml export-sarif
      --audit .kepenk/audit.jsonl
      --output reports/kepenk.sarif
      --include-approval

  - name: Upload SARIF
    uses: github/codeql-action/upload-sarif@<reviewed-commit>
    with:
      sarif_file: reports/kepenk.sarif
```

Pin third-party actions to reviewed immutable commits in production. Upload permissions, retention, visibility, and code-scanning availability are controlled by the hosting platform, not by Kepenk.

## Programmatic use

```python
from kepenk.sarif import build_sarif, write_sarif

report = build_sarif(".kepenk/audit.jsonl", include_approval=True)
write_sarif(
    ".kepenk/audit.jsonl",
    "reports/kepenk.sarif",
    include_approval=True,
)
```

Both functions refuse an invalid chain. `build_sarif` returns a Python mapping; `write_sarif` returns the rendered JSON and optionally writes it to a selected file.
