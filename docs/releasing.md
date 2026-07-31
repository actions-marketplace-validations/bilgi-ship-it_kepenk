# Release process

Kepenk releases must be reproducible, installable from both wheel and source distribution, and reviewed before publishing.

## Package name

The provisional PyPI distribution name is `kepenk-gate`. Search-engine results are not proof that a PyPI namespace is available. Confirm ownership or availability directly in PyPI before the first upload. If the name is unavailable, change `[project].name` before tagging and rebuild every artifact.

## Automated release check

Run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[release]"
python scripts/verify_release_artifacts.py
```

The script:

1. builds one wheel and one source distribution;
2. runs `twine check` on both;
3. creates separate clean virtual environments;
4. installs each artifact independently;
5. verifies the CLI, starter policy creation, and a policy decision.

The same check runs in the CI `package` job.

## First release checklist

1. Confirm the PyPI distribution name and project ownership.
2. Ensure all CI jobs are green on `main`.
3. Update `CHANGELOG.md` with the release date and final contents.
4. Run the automated release check from a clean checkout.
5. Create and push the annotated tag `v0.1.0`.
6. Create a GitHub release from the tag with the changelog notes.
7. Publish with a PyPI Trusted Publisher or a narrowly scoped publishing credential.
8. Install the public package in a fresh environment and repeat the CLI smoke test.
9. Do not overwrite an existing version; increment the version for every retry.

## Current publishing state

The repository prepares and verifies release artifacts, but it does not publish automatically. This avoids requiring a package token before the PyPI project and trusted-publishing relationship are configured.
