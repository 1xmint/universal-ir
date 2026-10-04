"""Verify external proposals and their exact review base; no signer or writer."""

from datetime import datetime, timezone
from pathlib import Path

from .inventory import ChangedDuringCapture, canonical
from .preparation import prepare_knowledge
from .receipts import (
    _digest, _external_bytes, _fail, _parse_host, _text, _validate_receipt,
    _verify_assertion, validate_policy,
)


FORMAT = "uir.preparation-receipt-verification.v1"
BINDING = "uir.signed-preparation-receipt.v1"
PAYLOAD = "uir.preparation-receipt.v1"
DOMAIN = b"Universal IR preparation receipt v1\x00"


def validate_prepared_receipt(receipt):
    return _validate_receipt(receipt, binding=BINDING, payload_format=PAYLOAD,
                             extra_field="preparation_id", actions=("approved",))


def signing_bytes(receipt):
    """Distinct fixed domain binds the candidate AND its prepared context."""
    return DOMAIN + canonical({field: receipt[field] for field in ("format", "algorithm", "key_id", "payload")})


def verify_candidate_receipt(root, candidate_path, receipt_path, policy_path, expected_policy_id,
                             expected_preparation_id, *, expected_project_id=None, clock=None):
    """Re-prepare actual source/candidate inputs; never trust a submitted preview."""
    _digest(expected_policy_id, "invalid_arguments")
    _digest(expected_preparation_id, "invalid_arguments")
    if expected_project_id is not None:
        _text(expected_project_id, "invalid_arguments")
    for _ in range(3):
        try:
            before = prepare_knowledge(root, candidate_path)
            if expected_project_id is not None and before["project_id"] != expected_project_id:
                _fail("host_project_mismatch", "Project identity differs from trusted host configuration.")
            resolved_root = Path(before["observation"]["root"])
            proof = _external_bytes(receipt_path, resolved_root)
            policy_input = _external_bytes(policy_path, resolved_root)
            after = prepare_knowledge(root, candidate_path)
            if before["preparation_id"] != after["preparation_id"] or before["observation"]["candidate_content_id"] != after["observation"]["candidate_content_id"]:
                continue
            if proof != _external_bytes(receipt_path, resolved_root) or policy_input != _external_bytes(policy_path, resolved_root):
                continue
            if expected_project_id is not None and after["project_id"] != expected_project_id:
                _fail("host_project_mismatch", "Project identity differs from trusted host configuration.")
            if after["preparation_id"] != expected_preparation_id:
                _fail("stale_preparation", "Current candidate or review context differs from the pinned preparation.")
            receipt = validate_prepared_receipt(_parse_host(proof[0], "invalid_receipt"))
            policy = validate_policy(_parse_host(policy_input[0], "invalid_trust_policy"), expected_policy_id)
            if receipt["payload"]["preparation_id"] != expected_preparation_id:
                _fail("receipt_subject_mismatch", "Receipt does not bind the exact pinned preparation.")
            result = _verify_assertion(after["candidate"]["record"], receipt, policy, expected_policy_id,
                                       now=clock() if clock is not None else datetime.now(timezone.utc),
                                       signed_bytes=signing_bytes(receipt))
            result.update(format=FORMAT, preparation_id=expected_preparation_id, preparation=after,
                          human_event_authentication="not_established")
            result["observation"] = {"snapshot": after["snapshot"], "root": str(resolved_root),
                                     "candidate_content_id": after["observation"]["candidate_content_id"],
                                     "record_evidence": after["candidate"]["evaluation"]["evidence_status"],
                                     "coverage_complete": after["coverage"]["complete"], "atomic": False,
                                     "freshness": "matching_preparations_and_host_input_reads"}
            return result
        except ChangedDuringCapture:
            continue
    _fail("unstable_inputs", "Project, candidate, or host inputs changed repeatedly; retry when stable.")
