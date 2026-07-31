# Contribute to Kepenk in ten minutes

This path is for a first external contributor who wants a small, reviewable change without learning the whole codebase first.

## 1. Choose an open task

Start with an unassigned [`good first issue`](https://github.com/bilgi-ship-it/kepenk/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or [`help wanted`](https://github.com/bilgi-ship-it/kepenk/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) issue.

Comment before starting so the intended scope stays visible. An issue comment is not a permanent reservation; another contributor may continue when there is no visible progress.

## 2. Fork, clone, and create a branch

```bash
git clone https://github.com/YOUR-USERNAME/kepenk.git
cd kepenk
git checkout -b docs/short-description
```

Use a focused branch name such as `docs/gitlab-example`, `test/repository-matcher`, or `fix/validation-message`.

## 3. Create a development environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,release]"
```

Windows PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

Kepenk supports Python 3.11 through 3.13. Continuous integration runs on Ubuntu and Windows.

## 4. Run the baseline checks

```bash
ruff check .
mypy src/kepenk
pytest
python scripts/validate_policy_examples.py
python scripts/run_safety_demos.py
```

Documentation-only pull requests still run the complete checks. This prevents examples and public claims from drifting away from executable behavior.

## 5. Make one small change

Good first pull requests normally change one concern:

- one CI-provider integration guide;
- one policy example and its expected-decision suite;
- one validation message plus regression tests;
- one documentation correction with a test that preserves the link or safety boundary;
- one Windows or PowerShell example with explicit limitations.

Do not include secrets, private logs, production approval receipts, proprietary source, or unsupported adoption and security claims.

## 6. Validate the changed surface

For policy changes:

```bash
kepenk validate --policy path/to/policy.yaml
kepenk --policy path/to/policy.yaml test --tests path/to/policy.tests.yaml
```

For a CLI or integration change, add positive and negative tests. Security-sensitive behavior should include fail-closed, malformed-input, and bypass attempts.

## 7. Open a draft pull request

A draft pull request is welcome before the work is complete. Include:

- the linked issue;
- what problem the change solves;
- what the change deliberately does not solve;
- commands used for verification;
- compatibility or security effects;
- screenshots only when they add information that text cannot show.

The maintainer targets a first pull-request response within seven calendar days. This is a public working target, not a guaranteed service level.

## What a successful first contribution looks like

A useful first contribution is small, reproducible, honest about limitations, and easy to review. It does not need to add a major feature. Documentation, tests, examples, and clearer failures are core open-source maintenance work.

Read [`CONTRIBUTING.md`](../CONTRIBUTING.md), [`MAINTAINERS.md`](../MAINTAINERS.md), and [`SECURITY.md`](../SECURITY.md) before working on larger or security-sensitive changes.
