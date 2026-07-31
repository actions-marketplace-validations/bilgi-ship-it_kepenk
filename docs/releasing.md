# Release process

Kepenk releases must be reproducible, installable from both wheel and source distribution, and reviewed before publishing.

Every v0.x release must also be checked against the [v0.x integration compatibility contract](compatibility-v0.md). A change to a declared stable surface requires updated regression tests, release notes, and migration guidance; it must not be hidden inside an ordinary patch release.

## Package name

The distribution name is `kepenk-gate`. Reconfirm authenticated ownership or publishing permission immediately before every PyPI upload; search results and a public `404` response alone are not proof that publishing will be accepted.

Run the public-state preflight before PyPI work:

```bash
python scripts/check_pypi_state.py
python scripts/check_pypi_state.py --repository testpypi --json
```

The preflight has deliberately limited claims:

- `not_found`: no public project listing was returned; availability remains unconfirmed by the script;
- `exists`: the project exists and publishing ownership must be checked manually;
- `version_published=true`: the version must not be reused or overwritten;
- network or malformed-response errors fail explicitly.

This check does not authenticate to PyPI and cannot prove ownership.

## Automated artifact check

Run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[release]"
python scripts/verify_release_artifacts.py
```

On Windows PowerShell, activate with `.\.venv\Scripts\Activate.ps1`.

The artifact script:

1. reads the exact package version from `pyproject.toml`;
2. builds one wheel and one source distribution;
3. runs `twine check` on both;
4. creates separate clean virtual environments;
5. installs each artifact independently;
6. verifies installed `kepenk-gate` metadata matches the release version;
7. smoke-tests `kepenk`, `kepenk-pre-commit`, and `kepenk-mcp`;
8. creates a starter policy and evaluates a representative action.

The same check runs in the CI `package` job. The normal test matrix also runs compatibility, MCP, protocol, policy-pack, pre-commit, and safety-demo tests.

## Two-stage GitHub Release

A release tag must point to the exact commit whose package metadata, changelog, README, and release notes were verified. Kepenk therefore uses two stages:

1. merge a release-preparation PR containing the version bump, changelog, release notes, and verification changes;
2. record the resulting immutable merge SHA;
3. add a dedicated `release-vX.Y.Z.yml` workflow on a later main commit, pinned to that release SHA;
4. let the workflow check out the pinned SHA, rerun quality and artifact verification, create the annotated tag, create the GitHub Release, upload the wheel and source distribution, verify asset names, and close the release issue.

The release workflow commit itself is intentionally not the tag target. This prevents a workflow-only change from altering the verified source release.

## PyPI Trusted Publisher setup

PyPI publication is separate from the GitHub Release and must remain an explicit maintainer action. The existing `.github/workflows/publish-pypi.yml` is pinned to the immutable v0.1.0 release and must not be repurposed silently for a different version.

For a future version-specific PyPI workflow, configure or reconfirm a pending GitHub publisher from the PyPI account **Publishing** page with these values:

- PyPI project name: `kepenk-gate`
- GitHub owner: `bilgi-ship-it`
- GitHub repository: `kepenk`
- exact workflow filename for that version
- environment name: `pypi`

The publishing workflow must:

1. require exact version-specific confirmation text;
2. check out an immutable tag and verify its exact commit SHA;
3. refuse an already-published version;
4. rerun lint, strict typing, tests, artifact builds, metadata checks, clean installs, and CLI smoke tests;
5. pass immutable artifacts to a separate publishing job;
6. grant `id-token: write` only to that publishing job;
7. verify installation from public PyPI after upload;
8. close a PyPI-specific issue only after public installation succeeds.

## Release checklist

1. Review every changed machine-facing surface against `docs/compatibility-v0.md`.
2. For a deprecation or breaking change, update `CHANGELOG.md`, release notes, migration guidance, and compatibility regression tests.
3. Set the exact version in `pyproject.toml`.
4. Update `CHANGELOG.md`, README release links, and `docs/releases/vX.Y.Z.md`.
5. Ensure all CI jobs are green on the exact release-preparation commit.
6. Run the automated artifact check from a clean checkout.
7. Merge the release-preparation PR and record its immutable SHA.
8. Add a dedicated release workflow pinned to that SHA.
9. Verify the workflow creates the annotated tag and GitHub Release with exactly one wheel and one source distribution.
10. Install an attached artifact in a clean environment and rerun CLI smoke tests.
11. Run a guarded PyPI workflow only when publishing is separately intended, configured, and authorized.

## Rollback limitations

Published package artifacts are immutable in normal release practice and an existing version must not be overwritten. If a release is incomplete or faulty:

1. stop further uploads for that version;
2. document the failure;
3. fix the repository;
4. increment the package version;
5. rebuild and verify new artifacts;
6. publish a new release.

Yanking a PyPI release can discourage new installation, but it does not erase artifacts already downloaded or used. Never treat yanking as a full rollback.

## Current publishing state

The annotated `v0.1.0` tag and GitHub Release are complete. The v0.2.0 GitHub release is tracked in issue #33 and uses the same pinned-SHA release method. Public PyPI publication remains separate and optional.
