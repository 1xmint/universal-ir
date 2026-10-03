"""Explicit-policy verification of host-signed receipts; no signer or writer."""

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re

from .inventory import (
    ChangedDuringCapture, InventoryError, _is_link, _read_file, canonical,
    _token, identity, parse_json,
)
from .knowledge import DIGEST, RECORD_FORMAT, STORE, inspect_knowledge, validate_record


FORMAT = "uir.receipt-verification.v1"
BINDING = "uir.signed-knowledge-receipt.v1"
POLICY = "uir.host-trust.v1"
DOMAIN = b"Universal IR host receipt v1\x00"
MAX_INPUT_BYTES = 1024 * 1024
UTC_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")


def _fail(code, message):
    raise InventoryError(code, message)


def _shape(value, names, code):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        _fail(code, "Object has missing or unsupported fields.")


def _text(value, code):
    if not isinstance(value, str) or not value.strip():
        _fail(code, "Identifiers must be nonempty UTF-8 strings.")
    try:
        value.encode("utf-8")
    except UnicodeError:
        _fail(code, "Identifiers must be representable as UTF-8.")


def _digest(value, code):
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        _fail(code, "Expected sha256 and 64 lowercase hexadecimal digits.")


def _hex(value, length, code):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{" + str(length * 2) + r"}", value):
        _fail(code, "Invalid lowercase hexadecimal byte encoding.")
    return bytes.fromhex(value)


def _time(value, code):
    if not isinstance(value, str) or not UTC_TIME.fullmatch(value):
        _fail(code, "Timestamps require UTC YYYY-MM-DDTHH:MM:SSZ.")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        _fail(code, "Invalid UTC calendar timestamp.")


def validate_policy(policy, expected_id):
    code = "invalid_trust_policy"
    _digest(expected_id, code)
    _shape(policy, "format project_id observed_at valid_until grants revoked_receipts", code)
    if policy["format"] != POLICY:
        _fail(code, "Unsupported trust policy format.")
    _text(policy["project_id"], code)
    observed, until = _time(policy["observed_at"], code), _time(policy["valid_until"], code)
    if until <= observed:
        _fail(code, "Policy validity interval must be nonempty.")
    if not isinstance(policy["grants"], list) or not isinstance(policy["revoked_receipts"], list):
        _fail(code, "Grants and revoked receipts must be lists.")
    seen = set()
    for grant in policy["grants"]:
        _shape(grant, "host_id actor_id key_id public_key actions not_before not_after", code)
        for field in ("host_id", "actor_id"):
            _text(grant[field], code)
        _digest(grant["key_id"], code)
        key = _hex(grant["public_key"], 32, code)
        if "sha256:" + hashlib.sha256(key).hexdigest() != grant["key_id"]:
            _fail(code, "Key identity does not match public key bytes.")
        actions = grant["actions"]
        if not isinstance(actions, list) or not actions or any(action not in ("stated", "approved") for action in actions):
            _fail(code, "Grant actions must be stated and/or approved.")
        if len(set(actions)) != len(actions):
            _fail(code, "Grant actions must be unique.")
        if _time(grant["not_before"], code) >= _time(grant["not_after"], code):
            _fail(code, "Key issuance interval must be nonempty.")
        grant_id = (grant["host_id"], grant["actor_id"], grant["key_id"])
        if grant_id in seen:
            _fail(code, "Duplicate host/actor/key grant.")
        seen.add(grant_id)
    for receipt in policy["revoked_receipts"]:
        _digest(receipt, code)
    if len(set(policy["revoked_receipts"])) != len(policy["revoked_receipts"]):
        _fail(code, "Revoked receipt identities must be unique.")
    if identity(policy) != expected_id:
        _fail("trust_policy_mismatch", "Policy does not match the host-pinned identity.")
    return policy


def validate_receipt(receipt):
    code = "invalid_receipt"
    _shape(receipt, "format algorithm key_id payload signature receipt_id", code)
    if receipt["format"] != BINDING or receipt["algorithm"] != "ed25519":
        _fail(code, "Unsupported receipt binding or algorithm.")
    _digest(receipt["key_id"], code)
    _digest(receipt["receipt_id"], code)
    _hex(receipt["signature"], 64, code)
    payload = receipt["payload"]
    _shape(payload, "format project_id record_id host_id event_id actor_id action recorded_at", code)
    if payload["format"] != "uir.knowledge-receipt.v1" or payload["action"] not in ("stated", "approved"):
        _fail(code, "Unsupported receipt payload or action.")
    for field in ("project_id", "host_id", "event_id", "actor_id"):
        _text(payload[field], code)
    _digest(payload["record_id"], code)
    _time(payload["recorded_at"], code)
    without_id = {key: value for key, value in receipt.items() if key != "receipt_id"}
    if identity(without_id) != receipt["receipt_id"]:
        _fail(code, "Receipt identity does not match its contents.")
    return receipt


def signing_bytes(receipt):
    """Fixed domain and canonical signed fields; no signature or ID hash cycle."""
    return DOMAIN + canonical({field: receipt[field] for field in ("format", "algorithm", "key_id", "payload")})


def verify_receipt(record, receipt, policy, expected_policy_id, *, now):
    """Verify under a caller-pinned policy, not authority chosen by model records."""
    validate_policy(policy, expected_policy_id)
    validate_receipt(receipt)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() != timezone.utc.utcoffset(now):
        _fail("invalid_verification_time", "Verification requires a trusted, timezone-aware UTC time.")
    now = now.astimezone(timezone.utc)
    if not _time(policy["observed_at"], "invalid_trust_policy") <= now < _time(policy["valid_until"], "invalid_trust_policy"):
        _fail("trust_policy_not_current", "Trust policy is expired or not yet current; refresh through the host.")
    # Validate the entire record, not just the untrusted record_id string.
    if not isinstance(record, dict) or not isinstance(record.get("body"), dict):
        _fail("invalid_knowledge", "Verification needs a complete knowledge record.")
    path = f"{STORE}/{record['body'].get('id')}/{str(record.get('record_id'))[7:]}.json"
    validate_record(record, policy["project_id"], path)
    origin = record["body"]["origin"]
    payload = receipt["payload"]
    if origin["kind"] != "developer_statement":
        _fail("receipt_subject_mismatch", "This binding verifies developer statements only.")
    if payload["project_id"] != policy["project_id"] or payload["record_id"] != record["record_id"] or any(
        payload[field] != origin[field] for field in ("host_id", "event_id", "actor_id")
    ):
        _fail("receipt_subject_mismatch", "Receipt does not bind this exact project, record, host, event, and actor.")
    if receipt["receipt_id"] in policy["revoked_receipts"]:
        _fail("receipt_revoked", "Host policy revokes this receipt.")
    grant = next((item for item in policy["grants"] if item["host_id"] == payload["host_id"] and
                  item["actor_id"] == payload["actor_id"] and item["key_id"] == receipt["key_id"]), None)
    if grant is None or payload["action"] not in grant["actions"]:
        _fail("receipt_not_authorized", "Host/actor/key/action is not authorized by the pinned policy.")
    issued = _time(payload["recorded_at"], "invalid_receipt")
    if issued > now or not _time(grant["not_before"], "invalid_trust_policy") <= issued < _time(grant["not_after"], "invalid_trust_policy"):
        _fail("receipt_time_not_authorized", "Receipt is future-dated or outside the permitted key issuance interval.")
    try:
        from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        _fail("receipt_verifier_unavailable", "Install the optional pinned requirements-receipts.txt dependencies.")
    try:
        public = Ed25519PublicKey.from_public_bytes(bytes.fromhex(grant["public_key"]))
        public.verify(bytes.fromhex(receipt["signature"]), signing_bytes(receipt))
    except InvalidSignature:
        _fail("invalid_receipt_signature", "Signature does not verify under the authorized host key.")
    except UnsupportedAlgorithm:
        _fail("receipt_verifier_unavailable", "The installed crypto backend does not support Ed25519.")
    return {"format": FORMAT, "status": "ok", "verification": "verified_under_pinned_policy",
            "receipt_id": receipt["receipt_id"], "trust_policy_id": expected_policy_id,
            "key_id": receipt["key_id"], **{field: payload[field] for field in
             ("project_id", "record_id", "host_id", "event_id", "actor_id", "action", "recorded_at")},
            "verified_at": now.isoformat(), "acceptance": "not_established", "replay": "not_checked",
            "trust_observation": {"observed_at": policy["observed_at"], "valid_until": policy["valid_until"],
                                  "live_revocation": False}}


def _external_bytes(path, root):
    """Read explicit host inputs outside source boundaries; reject path links."""
    path = Path(os.path.abspath(path))
    try:
        for part in (path, *path.parents):
            if _is_link(part):
                _fail("invalid_host_input", "Host input paths cannot cross a link or junction.")
        if path.resolve().is_relative_to(root):
            _fail("invalid_host_input", "Select host policy and receipt inputs outside the inspected project.")
        if not path.is_file():
            _fail("invalid_host_input", "Host inputs must be existing regular files.")
        digest, size, token = _read_file(path)
        if size > MAX_INPUT_BYTES:
            _fail("invalid_host_input", "Host inputs are limited to 1 MiB each.")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            if _token(os.fstat(stream.fileno())) != token:
                raise ChangedDuringCapture()
            data = stream.read(MAX_INPUT_BYTES + 1)
            if _token(os.fstat(stream.fileno())) != token:
                raise ChangedDuringCapture()
        if len(data) > MAX_INPUT_BYTES or "sha256:" + hashlib.sha256(data).hexdigest() != digest or _read_file(path) != (digest, size, token):
            raise ChangedDuringCapture()
        return data, digest, token
    except FileNotFoundError as error:
        raise ChangedDuringCapture() from error
    except OSError as error:
        _fail("unreadable_input", f"Cannot read explicit host input: {error}")


def _parse_host(data, code):
    try:
        return parse_json(data)
    except (ValueError, UnicodeError) as error:
        _fail(code, f"Invalid host JSON: {error}")


def verify_project_receipt(root, record_id, receipt_path, policy_path, expected_policy_id, *,
                           expected_project_id=None, clock=None):
    """CLI adapter core: current record plus coherently read explicit host inputs."""
    _digest(record_id, "invalid_arguments")
    _digest(expected_policy_id, "invalid_arguments")
    if expected_project_id is not None:
        _text(expected_project_id, "invalid_arguments")
    for _ in range(3):
        try:
            before = inspect_knowledge(root, full=True)
            if expected_project_id is not None and before["project_id"] != expected_project_id:
                _fail("host_project_mismatch", "Project identity differs from trusted host configuration.")
            resolved_root = Path(before["observation"]["root"])
            proof = _external_bytes(receipt_path, resolved_root)
            policy = _external_bytes(policy_path, resolved_root)
            after = inspect_knowledge(root, full=True)
            if before["snapshot"] != after["snapshot"] or proof != _external_bytes(receipt_path, resolved_root) or policy != _external_bytes(policy_path, resolved_root):
                continue
            if expected_project_id is not None and after["project_id"] != expected_project_id:
                _fail("host_project_mismatch", "Project identity differs from trusted host configuration.")
            entry = next((item for item in after["records"]["entries"] if item["record_id"] == record_id), None)
            if entry is None:
                _fail("unknown_knowledge", "Selected record has no included revision in this project.")
            record = {"format": RECORD_FORMAT, "project_id": after["project_id"],
                      "record_id": entry["record_id"], "body": entry["body"]}
            result = verify_receipt(record, _parse_host(proof[0], "invalid_receipt"),
                                    _parse_host(policy[0], "invalid_trust_policy"), expected_policy_id,
                                    now=clock() if clock is not None else datetime.now(timezone.utc))
            result["observation"] = {"snapshot": after["snapshot"], "root": str(resolved_root),
                                     "record_evidence": entry["evidence_status"], "coverage_complete": after["coverage"]["complete"],
                                     "atomic": False, "freshness": "matching_inspections_and_host_input_reads"}
            return result
        except ChangedDuringCapture:
            continue
    _fail("unstable_inputs", "Project or host inputs changed repeatedly; retry when stable.")
