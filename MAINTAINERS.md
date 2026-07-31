# Kepenk maintenance policy

Kepenk is currently maintained by [`@bilgi-ship-it`](https://github.com/bilgi-ship-it).

This document describes public working targets for the current single-maintainer phase. They are goals for transparency and planning, not contractual service-level guarantees. Availability, security incidents, travel, health, and project capacity may affect them.

## First-response targets

| Request | Target first response |
|---|---:|
| Private security advisory | 3 business days |
| Pull request | 7 calendar days |
| Bug report | 7 calendar days |
| Feature or integration proposal | 14 calendar days |
| Adopter-registry submission or removal | 7 calendar days |

A first response may confirm receipt, request reproducible information, classify risk, identify a duplicate, explain that more review is needed, or provide a decision. It does not promise that the work will be completed within the same period.

Private vulnerabilities must use GitHub Security Advisories as described in [`SECURITY.md`](SECURITY.md). Do not use public issues for exploitable policy bypasses, audit or receipt forgery, private-key disclosure, or command-execution vulnerabilities.

## Triage practice

New public issues are reviewed for:

1. reproducibility and affected version;
2. security and compatibility impact;
3. whether the request belongs in the deterministic core, an integration, documentation, or an external tool;
4. whether a smaller testable change can satisfy the need;
5. labels, acceptance criteria, and roadmap placement.

When possible, decisions and reasoning remain in public issues or pull requests. Private security details stay private until coordinated disclosure is appropriate.

## Pull-request review

A review checks:

- deterministic and fail-closed behavior;
- tests for expected behavior and failure modes;
- compatibility-contract impact;
- absence of secrets, private source, and unsupported claims;
- documentation and migration guidance for machine-facing changes;
- Ubuntu and Windows CI status;
- clean wheel and source-distribution verification.

Small focused pull requests are preferred. Maintainers may ask contributors to split unrelated changes. A passing CI run is required but does not replace human review.

## Release cadence

Kepenk uses a GitHub-first release process.

- Security and serious correctness fixes may receive a patch release as soon as a verified fix is ready.
- Normal features are grouped into a minor release when the documented scope is coherent, tested, and useful to adopters.
- During active development, the project targets at least one public maintenance update each calendar month. An update may be a release, roadmap note, issue-triage summary, or explicit statement that no release is ready.
- PyPI publication remains optional and separate from the verified GitHub Release.

Every release should have a tagged source commit, release notes, verified wheel and source distribution, clean-install checks, and an issue or workflow record showing completion.

## Measuring the targets

Evidence is taken from public GitHub timestamps:

- issue creation to the first maintainer comment, label, assignment, linked pull request, close decision, or other visible triage action;
- pull-request creation to the first maintainer review, comment, requested change, merge, or close decision;
- release tag and GitHub Release timestamps;
- private security timing is not published before disclosure.

The project does not claim a response-rate percentage until enough public requests exist to calculate one honestly. Missed targets should be acknowledged in the relevant thread rather than removed from the record.

## Decision authority and future maintainers

The current primary maintainer has final merge and release responsibility. Technical decisions should be explained publicly and tied to tests, compatibility, security, and adopter needs rather than personal preference.

A contributor may be considered for maintainer access after sustained, reviewed contributions across code, tests, documentation, issue triage, or release work. Access is granted gradually and may be limited to specific responsibilities. The project will update this document when additional maintainers are appointed.

## Contributor conduct

Follow [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md). Good-faith disagreement is welcome; harassment, fabricated evidence, credential sharing, and pressure to bypass review or security controls are not.
