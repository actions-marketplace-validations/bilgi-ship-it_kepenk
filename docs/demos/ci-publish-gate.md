# Demo 3: block a publishing step in GitHub Actions

The workflow at [`.github/workflows/demo-publish-gate.yml`](../../.github/workflows/demo-publish-gate.yml) proves that a CI job can consume Kepenk outputs and skip a publishing step.

## Flow

1. The repository is checked out.
2. The local Kepenk action evaluates `twine upload dist/*` against [`examples/demos/ci-publish-policy.yaml`](../../examples/demos/ci-publish-policy.yaml).
3. The policy returns `approval` and exit code `75`.
4. The action step uses `continue-on-error` so the workflow can inspect its outputs.
5. The simulated publish step has this condition:

```yaml
if: steps.gate.outputs.effect == 'allow'
```

6. A final assertion verifies that the gate outcome was `failure`, the effect was `approval`, the expected rule matched, and the publish marker file was never created.

## Run it

Open the repository's **Actions** tab, choose **Demo - Publish Gate**, and run the workflow on `main`. The workflow also runs automatically when its own files change in a pull request.

## What this proves

The demo does not upload a package and does not require registry credentials. It proves the enforcement wiring: a publish step is conditional on an explicit `allow` decision, and an `approval` decision leaves that step unexecuted.

For production use, pin external actions and Kepenk to reviewed immutable commit SHAs or release tags, protect the workflow and policy files, and require environment approvals for real publishing credentials.
