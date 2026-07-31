# Contributing to Kepenk

Thank you for helping build a safer layer for agentic developer tooling.

Read [`MAINTAINERS.md`](MAINTAINERS.md) for current first-response targets, triage practice, review expectations, release cadence, and the path toward additional maintainers. These are public working targets rather than guaranteed service levels.

## Before opening a pull request

1. Open or reference an issue for non-trivial changes.
2. Keep the core deterministic and provider-neutral.
3. Add tests for new behavior and edge cases.
4. Run:

```bash
ruff check .
mypy src/kepenk
pytest
```

## Commit and PR guidance

- Use focused commits.
- Describe the failure mode or workflow problem addressed.
- Call out policy-format and machine-facing changes explicitly.
- Do not include credentials, private logs, private keys, approval receipts from production, or proprietary source.
- Keep claims tied to reproducible repository evidence.
- Update compatibility and migration documentation when a machine-facing contract changes.

A passing CI run is required but does not replace maintainer review. Security-sensitive changes should explain their threat model and negative tests.

## Adopter registry contributions

Public adopter entries follow a separate evidence process:

1. Read [the adoption guide](docs/adoption.md).
2. Add one row to the correct section of [`ADOPTERS.md`](ADOPTERS.md).
3. Link to a public repository and a stable public integration permalink.
4. Use [the adopter pull-request template](.github/PULL_REQUEST_TEMPLATE/adopter.md).
5. Confirm that the repository maintainer agrees to the listing.
6. Classify founding-team pilots separately from independent adopters.

An adopter entry may be removed when the listed maintainer asks, the evidence link disappears, or the linked repository no longer shows Kepenk use.

A registry entry records visible integration evidence. It is not a certification, partnership, or endorsement.

## Good first contributions

Open issues carrying the [`good first issue`](https://github.com/bilgi-ship-it/kepenk/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) label are intentionally scoped for an outside contributor.

Suitable contribution areas include:

- additional CI-provider integration examples;
- policy examples and policy test suites;
- Windows and PowerShell command patterns;
- documentation improvements;
- clearer validation errors;
- onboarding examples for public repositories;
- fuzz and property tests for rule matching.

Ask questions in the issue before investing in a large solution. The maintainer will keep acceptance criteria public and avoid reserving an issue indefinitely without visible progress.
