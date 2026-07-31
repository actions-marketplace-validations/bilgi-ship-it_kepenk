# Contributing to Kepenk

Thank you for helping build a safer layer for agentic developer tooling.

For a small first pull request, start with the [ten-minute contributor quickstart](docs/contributor-quickstart.md). It covers the development environment, baseline checks, focused change sizes, and draft pull-request expectations.

Read [`MAINTAINERS.md`](MAINTAINERS.md) for current first-response targets, triage practice, review expectations, release cadence, and the path toward additional maintainers. These are public working targets rather than guaranteed service levels.

## Before opening a pull request

1. Open or reference an issue for non-trivial changes.
2. Prefer an unassigned [`good first issue`](https://github.com/bilgi-ship-it/kepenk/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or [`help wanted`](https://github.com/bilgi-ship-it/kepenk/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) task for a first contribution.
3. Keep the core deterministic and provider-neutral.
4. Add tests for new behavior and edge cases.
5. Run:

```bash
ruff check .
mypy src/kepenk
pytest
python scripts/validate_policy_examples.py
python scripts/run_safety_demos.py
```

Documentation-only pull requests run the complete checks so examples and public claims remain tied to executable behavior.

## Commit and PR guidance

- Use focused commits.
- Describe the failure mode or workflow problem addressed.
- Call out policy-format and machine-facing changes explicitly.
- Do not include credentials, private logs, private keys, approval receipts from production, or proprietary source.
- Keep claims tied to reproducible repository evidence.
- Update compatibility and migration documentation when a machine-facing contract changes.
- State what the change deliberately does not solve.

A passing CI run is required but does not replace maintainer review. Security-sensitive changes should explain their threat model and negative tests.

Draft pull requests are welcome. Link the issue, list the verification commands, and keep unrelated work out of the same pull request.

## Adopter registry contributions

Public adopter entries follow a separate evidence process:

1. Read [the adoption guide](docs/adoption.md).
2. Add one row to the correct section of [`ADOPTERS.md`](ADOPTERS.md).
3. Link to a public repository and a stable public integration permalink.
4. Use [the adopter pull-request template](.github/PULL_REQUEST_TEMPLATE/adopter.md).
5. Confirm that the repository maintainer agrees to the listing.
6. Classify founding-team pilots separately from independent adopters.

The current independent-adoption task is [#65](https://github.com/bilgi-ship-it/kepenk/issues/65). The adopting repository must not be controlled by the Kepenk founding team.

An adopter entry may be removed when the listed maintainer asks, the evidence link disappears, or the linked repository no longer shows Kepenk use.

A registry entry records visible integration evidence. It is not a certification, partnership, endorsement, or proof that all repository actions pass through Kepenk.

## Good first contributions

Open issues carrying the [`good first issue`](https://github.com/bilgi-ship-it/kepenk/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) label are intentionally scoped for an outside contributor.

Current examples:

- [#57 — GitLab CI policy-check integration guide](https://github.com/bilgi-ship-it/kepenk/issues/57);
- [#58 — Azure Pipelines policy-check integration guide](https://github.com/bilgi-ship-it/kepenk/issues/58).

Suitable contribution areas also include:

- policy examples and policy test suites;
- Windows and PowerShell command patterns;
- documentation improvements;
- clearer validation errors;
- onboarding examples for public repositories;
- fuzz and property tests for rule matching.

Ask questions in the issue before investing in a large solution. The maintainer will keep acceptance criteria public and avoid reserving an issue indefinitely without visible progress.

See [`docs/project-evidence.md`](docs/project-evidence.md) for the project's current public adoption and contribution record. Do not convert targets or founding-team work into external-usage claims.
