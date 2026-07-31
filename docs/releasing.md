# Release process

Kepenk releases must be reproducible, installable from both wheel and source distribution, and reviewed before publishing.

## Package name

The provisional PyPI distribution name is `kepenk-gate`. Search-engine results and a `404` response are not proof that a PyPI namespace can be reserved or that the maintainer has publishing permission. Confirm ownership or availability directly in the PyPI account before the first upload. If the name is unavailable, change `[project].name` before tagging and rebuild every artifact.

Run the public-state preflight before release work:

```bash
python scripts/check_pypi_state.py
python scripts/check_pypi_state.py --repository testpypi --json
```

The preflight has deliberately limited claims:

- `not_found`: no public project listing was returned; availability remains unconfirmed;
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

1. builds one wheel and one source distribution;
2. runs `twine check` on both;
3. creates separate clean virtual environments;
4. installs each artifact independently;
5. verifies the CLI, starter policy creation, and a policy decision.

The same check runs in the CI `package` job.

## First release checklist

1. Confirm the PyPI distribution name and project ownership.
2. Configure a narrowly scoped PyPI Trusted Publisher or equivalent release credential.
3. Ensure all CI jobs are green on the exact release commit.
4. Run the public-state preflight against PyPI and TestPyPI.
5. Update `CHANGELOG.md` with the actual release date and final contents.
6. Run the automated artifact check from a clean checkout.
7. Create and push annotated tag `v0.1.0` from the verified commit.
8. Create a GitHub release from the tag using `docs/releases/v0.1.0.md`.
9. Publish the already-verified artifacts exactly once.
10. Install the public package in a fresh environment and repeat the CLI smoke test.

## Rollback limitations

PyPI artifacts are immutable in normal release practice and an existing version must not be overwritten. If a release is incomplete or faulty:

1. stop further uploads for that version;
2. document the failure;
3. fix the repository;
4. increment the package version;
5. rebuild and verify new artifacts;
6. publish a new release.

Yanking a release can discourage new installation, but it does not erase artifacts already downloaded or used. Never treat yanking as a full rollback.

## Current publishing state

The repository prepares and verifies release artifacts, but it does not publish automatically. This avoids requiring a package token before the PyPI project and trusted-publishing relationship are configured.
