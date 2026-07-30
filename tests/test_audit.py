import json
from pathlib import Path

from kepenk.audit import append_decision, verify_audit
from kepenk.models import Action, Decision


def _decision() -> Decision:
    return Decision(
        effect="allow",
        reason="test",
        rule_id="allow-test",
        action=Action(type="shell", command="pytest"),
    )


def test_audit_chain_verifies(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    append_decision(path, _decision(), outcome="checked")
    append_decision(path, _decision(), outcome="execution_finished:0")
    assert verify_audit(path) == (True, 2, None)


def test_audit_tampering_is_detected(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    append_decision(path, _decision(), outcome="checked")
    event = json.loads(path.read_text(encoding="utf-8"))
    event["outcome"] = "tampered"
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    valid, count, error = verify_audit(path)
    assert not valid
    assert count == 0
    assert error is not None
