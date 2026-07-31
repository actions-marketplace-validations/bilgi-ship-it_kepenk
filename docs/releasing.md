# Release process

Kepenk releases must be reproducible, installable from both wheel and source distribution, and reviewed before publishing.

## Package name

The PyPI distribution name is `kepenk-gate`. The maintainer confirmed its availability on 2026-07-31 before finalizing v0.1.0. Reconfirm authenticated ownership or publishing permission immediately before every upload; search results and a public `404` response alone are not proof that publishing will be accepted.

Run the public-state preflight before release work:

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

1. builds one wheel and one source distribution;
2. runs `twine check` on both;
3. creates separate clean virtual environments;
4. installs each artifact independently;
5. verifies the CLI, starter policy creation, and a policy decision.

The same check runs in the CI `package` job.

## PyPI Trusted Publisher setup

The production workflow is `.github/workflows/publish-pypi.yml`. It uses GitHub OIDC and does not require a stored PyPI API token.

For a new PyPI project, create a pending GitHub publisher from the PyPI account **Publishing** page with these exact values:

- PyPI project name: `kepenk-gate`
- GitHub owner: `bilgi-ship-it`
- GitHub repository: `kepenk`
- Workflow filename: `publish-pypi.yml`
- Environment name: `pypi`

If the PyPI project already exists, add the same publisher from the project's **Publishing** page instead.

After the publisher is configured:

1. Open the repository's **Actions** page.
2. Select **Publish to PyPI**.
3. Choose **Run workflow** on the `main` branch.
4. Enter the exact confirmation `PUBLISH-v0.1.0`.
5. Run the workflow once.

The workflow:

1. rejects any other confirmation text;
2. checks out the immutable `v0.1.0` tag and verifies its exact commit SHA;
3. refuses to publish when `0.1.0` already exists on public PyPI;
4. reruns lint, strict typing, tests, package builds, metadata checks, clean installs, and CLI smoke tests;
5. passes immutable artifacts to a separate publishing job;
6. grants `id-token: write` only to that publishing job;
7. installs `kepenk-gate==0.1.0` from public PyPI after upload;
8. closes release issue #5 only after the public installation and CLI smoke tests succeed.

## First release checklist

1. Confirm the PyPI distribution name and project ownership.
2. Configure the PyPI Trusted Publisher using the exact values above.
3. Ensure all CI jobs are green on the exact release commit.
4. Run the public-state preflight against PyPI and TestPyPI.
5. Update `CHANGELOG.md` with the actual release date and final contents.
6. Run the automated artifact check from a clean checkout.
7. Create and push annotated tag `v0.1.0` from the verified commit.
8. Create a GitHub release from the tag using `docs/releases/v0.1.0.md`.
9. Run **Publish to PyPI** with the exact confirmation.
10. Confirm that the workflow verifies installation from public PyPI and closes issue #5.

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

The annotated `v0.1.0` tag and GitHub Release are complete, and the verified wheel and source distribution are attached. The guarded PyPI Trusted Publishing workflow is prepared. PyPI publication requires the publisher configuration above and one explicit manual workflow run.
