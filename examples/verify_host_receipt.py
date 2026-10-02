"""Fictional offline host signing demo; ephemeral key, no real user approval."""

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from universal_ir.inventory import canonical, identity, parse_json
from universal_ir.knowledge import inspect_knowledge
from universal_ir.receipts import BINDING, DOMAIN, POLICY


def run_demo():
    tool = Path(__file__).resolve().parents[1]
    root = tool / "examples/fixtures/knowledge-project"
    records = [parse_json(path.read_bytes()) for path in (root / ".uir/knowledge/records/retention").glob("*.json")]
    record = next(item for item in records if not item["body"]["supersedes"])
    origin = record["body"]["origin"]
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = lambda value: value.strftime("%Y-%m-%dT%H:%M:%SZ")
    # This scripted host is trusted only within the fictional demonstration.
    # A real host must obtain authenticated user action outside model tools.
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes_raw()
    key_id = "sha256:" + hashlib.sha256(public).hexdigest()
    payload = {"format": "uir.knowledge-receipt.v1", "project_id": record["project_id"],
               "record_id": record["record_id"], **{field: origin[field] for field in ("host_id", "event_id", "actor_id")},
               "action": "approved", "recorded_at": stamp(now)}
    unsigned = {"format": BINDING, "algorithm": "ed25519", "key_id": key_id, "payload": payload}
    signed = dict(unsigned, signature=key.sign(DOMAIN + canonical(unsigned)).hex())
    proof = dict(signed, receipt_id=identity(signed))
    policy = {"format": POLICY, "project_id": record["project_id"], "observed_at": stamp(now - timedelta(minutes=1)),
              "valid_until": stamp(now + timedelta(minutes=10)), "revoked_receipts": [], "grants": [{
                  "host_id": origin["host_id"], "actor_id": origin["actor_id"], "key_id": key_id,
                  "public_key": public.hex(), "actions": ["approved"],
                  "not_before": stamp(now - timedelta(minutes=1)), "not_after": stamp(now + timedelta(minutes=10))}]}
    with TemporaryDirectory(prefix="uir-fictional-host-") as scratch:
        receipt_path, policy_path = Path(scratch) / "receipt.json", Path(scratch) / "policy.json"
        receipt_path.write_bytes(canonical(proof) + b"\n")
        policy_path.write_bytes(canonical(policy) + b"\n")
        command = [sys.executable, "-B", "-m", "universal_ir", "verify-receipt", str(root), record["record_id"],
                   "--receipt", str(receipt_path), "--policy", str(policy_path), "--policy-id", identity(policy)]
        valid = subprocess.run(command, cwd=tool, capture_output=True, check=True)
        proof["signature"] = "00" * 64
        proof["receipt_id"] = identity({name: value for name, value in proof.items() if name != "receipt_id"})
        receipt_path.write_bytes(canonical(proof) + b"\n")
        invalid = subprocess.run(command, cwd=tool, capture_output=True, check=False)
        failure = json.loads(invalid.stderr)
        if invalid.returncode != 2 or invalid.stdout or failure["error"]["code"] != "invalid_receipt_signature":
            raise RuntimeError("Tampered demonstration receipt was not rejected as expected.")
    default = inspect_knowledge(root, selected_id="retention", full=True)
    if any(item["attribution"] != "unverified_attribution" for item in default["records"]["entries"]):
        raise RuntimeError("Default knowledge inspection incorrectly promoted the fictional claims.")
    return {"format": "uir.fictional-host-demo.v1", "status": "ok", "approval_source": "scripted_fictional_event",
            "valid_receipt": json.loads(valid.stdout), "tampered_signature": failure["error"]["code"],
            "default_attribution": "unverified_attribution", "private_key_persisted": False,
            "real_user_integration": "not_demonstrated"}


if __name__ == "__main__":
    print(json.dumps(run_demo(), ensure_ascii=True, indent=2, allow_nan=False))
