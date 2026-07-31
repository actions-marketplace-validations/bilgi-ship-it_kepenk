# Offline adoption evidence manifests

Kepenk adoption evidence version 1 is a small JSON document that records one public integration in a consistent, reviewable shape.

The manifest is optional. It supports the consent-based adopter registry; it does not replace a registry pull request, public evidence review, or maintainer confirmation.

## Validate a manifest

```bash
kepenk validate-adoption --evidence .kepenk/adoption.json
```

Machine-readable output:

```bash
kepenk validate-adoption \
  --evidence .kepenk/adoption.json \
  --json
```

The command works without a `kepenk.yaml` policy because adoption evidence is separate from action policy evaluation.

A valid manifest exits `0`. Missing, malformed, unsupported, private-host-shaped, inconsistent, or unconsented evidence exits `64`.

## Version 1 fields

| Field | Meaning |
|---|---|
| `version` | Integer `1` |
| `classification` | `independent_adopter` or `founding_team_pilot` |
| `repository` | Public owner/name-style repository slug |
| `repository_url` | Public HTTPS repository URL whose path ends with the slug |
| `maintainer` | Public maintainer handle |
| `maintainer_url` | Public HTTPS maintainer profile or identity page |
| `maintainer_consent` | Must be literal `true` |
| `integration` | `github_action`, `pre_commit`, `cli`, `jsonl`, `mcp`, or `other` |
| `kepenk_version` | Tagged semantic version such as `v0.3.0` |
| `evidence_url` | Public HTTPS URL inside the declared repository |
| `verified_on` | Valid `YYYY-MM-DD` date |

Unknown fields are rejected. Duplicate JSON keys are rejected. Files larger than 64 KiB are rejected.

The JSON Schema is [`schemas/kepenk-adoption-evidence-v1.schema.json`](../schemas/kepenk-adoption-evidence-v1.schema.json).

## Example

The public Ustaca AI founding-team pilot is represented in [`examples/adoption/ustaca-ai.json`](../examples/adoption/ustaca-ai.json):

```json
{
  "version": 1,
  "classification": "founding_team_pilot",
  "repository": "bilgi-ship-it/ustaca-ai",
  "repository_url": "https://github.com/bilgi-ship-it/ustaca-ai",
  "maintainer": "bilgi-ship-it",
  "maintainer_url": "https://github.com/bilgi-ship-it",
  "maintainer_consent": true,
  "integration": "github_action",
  "kepenk_version": "v0.3.0",
  "evidence_url": "https://github.com/bilgi-ship-it/ustaca-ai/tree/main/.kepenk",
  "verified_on": "2026-07-31"
}
```

Validate the checked-in example:

```bash
kepenk validate-adoption \
  --evidence examples/adoption/ustaca-ai.json
```

## Independent adopter workflow

An independent public repository may:

1. add `.kepenk/adoption.json` using classification `independent_adopter`;
2. point `evidence_url` to its public policy, workflow, hook, adapter, or integration documentation;
3. run `kepenk validate-adoption --evidence .kepenk/adoption.json` in CI;
4. open a Kepenk registry pull request using the adopter template;
5. include a permalink to the manifest and the underlying integration evidence.

The repository must not be controlled by the Kepenk founding team to qualify as independent adoption.

## Privacy and security boundary

Validation is deliberately offline. Kepenk does not:

- fetch any URL;
- contact GitHub, GitLab, another forge, or a telemetry service;
- count users, installations, stars, forks, downloads, or repositories;
- prove repository ownership or maintainer identity;
- prove that a URL currently exists or is public;
- prove that every repository action passes through Kepenk;
- certify production security;
- transform a founding-team repository into independent adoption.

The validator rejects obvious local, loopback, private-IP, credential-bearing, query-bearing, and fragment-bearing URLs. This is input hardening, not a network-reachability or ownership check.

Human registry review must still confirm classification, public evidence, maintainer consent, and the absence of unsupported claims or sensitive data.

## Compatibility

Version 1 is experimental during the v0.4 line. Patch releases will not silently reinterpret existing fields or accept `maintainer_consent: false`. A breaking field or classification change requires a new integer manifest version and migration guidance.
