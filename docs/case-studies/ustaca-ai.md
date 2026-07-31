# Ustaca AI founding-team pilot

**Classification:** founding-team pilot — not independent adoption  
**Repository:** [`bilgi-ship-it/ustaca-ai`](https://github.com/bilgi-ship-it/ustaca-ai)  
**Verified:** 2026-07-31  
**Kepenk version:** `v0.3.0`

This case study records one public and reproducible Kepenk integration maintained by the Kepenk founding account. It demonstrates an integration path and visible test evidence. It is not a production-security certification, user-count claim, independent-adoption claim, or third-party endorsement.

## Repository context

Ustaca AI is a public npm/Turborepo monorepo containing Next.js applications, shared TypeScript packages, and infrastructure definitions. The repository does not expose Python project metadata such as `pyproject.toml` or `requirements.txt`.

That makes it a useful public consumer test for two Kepenk requirements:

1. the composite GitHub Action must work in a non-Python repository;
2. v0.3 repository-scoped policy rules and declarative policy tests must work outside the Kepenk source repository.

## Protected actions

The pilot policy is scoped to the explicit repository context `bilgi-ship-it/ustaca-ai`.

| Proposed action | Expected decision | Rule |
|---|---|---|
| `npm run lint` | `allow` | `allow-lint` |
| `npm run typecheck` | `allow` | `allow-typecheck` |
| `npm run build` | `allow` | `allow-local-build` |
| `npm install example-package` | `approval` | `require-dependency-change-approval` |
| `git push origin main` | `approval` | `require-remote-git-change-approval` |
| `npm publish` | `deny` | `deny-public-package-publish` |
| `npm run lint` without repository context | policy default `approval` | no matched rule |
| unmatched command with repository context | policy default `approval` | no matched rule |

Rules use `repository_glob: bilgi-ship-it/ustaca-ai`. Kepenk does not discover or authenticate this value. The protected workflow supplies `${{ github.repository }}` explicitly. A caller able to control the value could misrepresent it, so the surrounding workflow definition and repository permissions remain part of the security boundary.

## Public implementation

- [Repository policy](https://github.com/bilgi-ship-it/ustaca-ai/blob/main/.kepenk/policy.yaml)
- [Eight-case policy regression suite](https://github.com/bilgi-ship-it/ustaca-ai/blob/main/.kepenk/policy.tests.yaml)
- [GitHub Actions workflow](https://github.com/bilgi-ship-it/ustaca-ai/blob/main/.github/workflows/kepenk-policy.yml)
- [Pilot documentation](https://github.com/bilgi-ship-it/ustaca-ai/blob/main/.kepenk/README.md)
- [v0.3.0 upgrade pull request](https://github.com/bilgi-ship-it/ustaca-ai/pull/4)
- [Successful public workflow run](https://github.com/bilgi-ship-it/ustaca-ai/actions/runs/30632303510)

## Workflow sequence

The public workflow performs these steps:

1. checks out the Ustaca AI repository;
2. invokes `bilgi-ship-it/kepenk@v0.3.0` in validation mode;
3. runs the complete declarative policy suite with `kepenk test`;
4. evaluates a lint command with the explicit repository context and requires `allow`;
5. evaluates a dependency-install command and requires `approval` plus the expected non-success Action outcome;
6. evaluates package publication and requires `deny` plus the expected non-success Action outcome;
7. asserts the returned effects and matched rule IDs.

Approval and deny checks use `continue-on-error: true` only so a later assertion step can inspect the expected failed Action outcome. No dependency installation, package publication, deployment, Git push, or destructive command is executed by the workflow.

## Reproduce the decision tests locally

From a checkout of the public Ustaca AI repository:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install \
  "https://github.com/bilgi-ship-it/kepenk/archive/refs/tags/v0.3.0.zip"

kepenk --policy .kepenk/policy.yaml test \
  --tests .kepenk/policy.tests.yaml
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

The suite should report eight passing cases. Test cases are evaluated only; they do not execute the proposed commands and do not append test results to the policy audit chain.

A single explicit check can be reproduced with:

```bash
kepenk --policy .kepenk/policy.yaml check \
  --action shell \
  --repository bilgi-ship-it/ustaca-ai \
  --command "npm run lint"
```

The expected result is `allow` through `allow-lint`. Omitting `--repository` should produce the conservative policy-default `approval` result because repository-scoped rules do not match missing context.

## What the evidence shows

The public evidence shows that:

- the v0.3.0 composite Action installs in a repository without Python project metadata;
- the policy loads successfully;
- the versioned policy suite produces the expected eight decisions;
- repository context is carried through the GitHub Action;
- representative allow, approval, and deny decisions and rule IDs are asserted;
- approval and deny prevent the Action step from succeeding normally;
- no proposed side-effecting action is executed by the policy workflow.

## What the evidence does not show

The pilot does not prove that:

- an independent maintainer adopted Kepenk;
- the wider Ustaca application is production-ready or secured by Kepenk;
- all commands, tools, APIs, credentials, or deployment paths pass through Kepenk;
- repository context authenticates a checkout;
- Kepenk is a sandbox or can stop direct execution that bypasses the wrapper;
- the policy is universally suitable for another repository;
- a passing CI workflow is a security audit or certification.

The integration must still be combined with protected workflow definitions, branch rules, least-privilege credentials, isolated runners, normal code review, and operating-system controls.

## Maintenance and removal

The pilot is maintained by the same GitHub account that maintains Kepenk. It is listed separately from independent adopters in [`ADOPTERS.md`](../../ADOPTERS.md). The entry should be updated or removed when the linked evidence no longer shows the documented integration.
