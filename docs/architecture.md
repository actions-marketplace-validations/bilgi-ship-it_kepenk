# Architecture

Kepenk separates policy from execution.

```text
Agent or automation
        |
        v
 Structured Action
        |
        v
  PolicyEngine  ----> Decision: allow / approval / deny
        |                          |
        |                          v
        +--------------------> Audit chain
                                   |
                                   v
                         Optional safe runner
```

## Trust model

The policy engine is deterministic and does not call a language model. It assumes the caller routes actions through Kepenk. Direct execution outside the wrapper is outside the security boundary.

## Rule order

Rules are evaluated from top to bottom and the first match wins. This makes policy behavior easy to explain and review. More specific deny rules should appear before broad allow rules.

## Audit chain

Each JSONL event contains `previous_hash` and `event_hash`. The event hash is SHA-256 over the previous hash and canonical event payload. This detects deletion, reordering, and modification inside a retained chain, but does not replace signed remote logging.
