# Contributing to Kepenk

Thank you for helping build a safer layer for agentic developer tooling.

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
- Do not include credentials, private logs, or proprietary source.
- Keep claims tied to reproducible repository evidence.

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

- additional policy examples and policy test suites
- Windows and PowerShell command patterns
- documentation improvements
- clearer validation errors
- onboarding examples for public repositories
- fuzz and property tests for rule matching
