# Kepenk public project evidence

**Snapshot date:** 2026-07-31

This document keeps application, outreach, and adoption claims tied to public evidence. It should be updated rather than supplemented with estimates.

## Project identity

- Repository: [`bilgi-ship-it/kepenk`](https://github.com/bilgi-ship-it/kepenk)
- License: Apache-2.0
- Current verified release: [`v0.3.0`](https://github.com/bilgi-ship-it/kepenk/releases/tag/v0.3.0)
- Maintainer: [`@bilgi-ship-it`](https://github.com/bilgi-ship-it)
- Package name: `kepenk-gate`
- Positioning: provider-neutral, local-first approval and audit gate for AI coding agents

## Tagged release history

Four tagged GitHub releases are publicly recorded:

1. `v0.1.0` — deterministic policy gate, safe runner, audit chain, CLI, schema, Codex and GitHub Action foundations;
2. `v0.2.0` — JSONL, policy packs, demonstrations, pre-commit, MCP and compatibility contract;
3. `v0.2.1` — GitHub Action portability fix for non-Python consumer repositories;
4. `v0.3.0` — policy regression suites, repository context, SARIF export and Ed25519 approval receipts.

The v0.3.0 annotated tag resolves to the verified release source commit. Published wheel and source distributions were downloaded from the GitHub Release, installed into clean environments, and smoke-tested before the release issue was closed.

## Active maintenance evidence

Public maintenance work includes:

- issue-based feature and release tracking;
- pull requests with full continuous integration before merge;
- Ubuntu and Windows testing on Python 3.11 and 3.13;
- strict type checking, linting, demonstrations, policy tests and clean package installation;
- public [`SECURITY.md`](../SECURITY.md), [`CHANGELOG.md`](../CHANGELOG.md), [`MAINTAINERS.md`](../MAINTAINERS.md) and compatibility guidance;
- documented first-response targets, triage practice and release cadence;
- verified release automation pinned to an exact source commit.

## Maintainer-workflow relevance

Kepenk addresses repeatable open-source maintenance tasks:

- evaluate proposed agent actions as `allow`, `approval` or `deny`;
- preserve local tamper-evident decision records;
- validate policies and expected decisions in CI;
- gate shell, Git, package, release and infrastructure workflows;
- expose decisions through CLI, JSONL, GitHub Actions, pre-commit and MCP;
- export redacted denied decisions to SARIF;
- create and verify short-lived signed approval receipts without executing the action.

Kepenk is a policy layer, not a sandbox. Its documentation consistently keeps operating-system isolation, credentials, protected workflows and code review inside the surrounding security boundary.

## Public usage and adoption evidence

Current evidence is deliberately separated by ownership:

- verified founding-team pilots: **1** — [`bilgi-ship-it/ustaca-ai`](case-studies/ustaca-ai.md);
- verified independent adopters: **0**;
- recorded outside contributors: **0**.

The Ustaca AI pilot proves that Kepenk v0.3.0 installs and runs in a public npm/Turborepo repository without Python project metadata. It exercises policy validation, an eight-case regression suite, explicit repository context and representative allow, approval and deny outputs.

The pilot does not count as independent adoption and is not presented as a production-security certification.

## Open external contribution paths

The repository keeps visible, unassigned work for outside contributors:

- [GitLab CI integration guide — #57](https://github.com/bilgi-ship-it/kepenk/issues/57);
- [Azure Pipelines integration guide — #58](https://github.com/bilgi-ship-it/kepenk/issues/58);
- [OpenTelemetry-compatible redacted audit export — #59](https://github.com/bilgi-ship-it/kepenk/issues/59).

The first two are documentation-focused `good first issue` tasks. The third starts with a reviewed privacy and field-mapping design.

## Metrics policy

Kepenk does not include telemetry or automatic user counting. Stars, forks, downloads, installations, contributors and adopter counts must be read from public sources at the time of use. Do not substitute goals, repository views, founding-team use or unverified mentions for independent adoption.

## OpenAI Codex for Open Source readiness

The repository now has public evidence for active maintenance, release management, security and code-quality processes, and a clear maintainer-workflow use case. A truthful application can be submitted without claiming independent adoption.

The application becomes materially stronger after one independent public adopter or one reviewed outside contribution. Private application fields must never be committed here:

- email associated with the applicant's ChatGPT account;
- OpenAI Organization ID;
- any private account, billing or credential information.

See [`openai-application-plan.md`](openai-application-plan.md) for the form-ready text and remaining private inputs.
