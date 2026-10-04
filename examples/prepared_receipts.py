"""Fictional prepared review through the real CLI and host-fixed tool."""

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from universal_ir.harness import PreparedReceiptVerifier
from universal_ir.inventory import canonical, identity
from universal_ir.knowledge import inspect_knowledge
from universal_ir.preparation import prepare_knowledge
from universal_ir.prepared_receipts import BINDING, PAYLOAD, signing_bytes
from universal_ir.receipts import POLICY


def run_demo():
    tool = Path(__file__).resolve().parents[1]
    root = tool / "examples/fixtures/knowledge-project"
    before = inspect_knowledge(root, selected_id="retention", full=True)
    heads = before["groups"]["entries"][0]["heads"]
    body = {"id": "retention", "category": "requirement", "text": "Retain archived tasks for 60 days.",
            "scope": ["."], "origin": {"kind": "developer_statement", "host_id": "fictional-host",
            "actor_id": "fictional-alice", "event_id": "scripted-review"}, "input_id": None,
            "evidence": [], "supersedes": heads, "state": "active"}
    unsigned = {"format": "uir.knowledge.v1", "project_id": before["project_id"], "body": body}
    record = dict(unsigned, record_id=identity(unsigned))
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = lambda time: time.strftime("%Y-%m-%dT%H:%M:%SZ")
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes_raw()
    key_id = "sha256:" + hashlib.sha256(public).hexdigest()
    policy = {"format": POLICY, "project_id": before["project_id"], "observed_at": stamp(now - timedelta(days=1)),
              "valid_until": stamp(now + timedelta(days=1)), "revoked_receipts": [], "grants": [{
                  "host_id": "fictional-host", "actor_id": "fictional-alice", "key_id": key_id,
                  "public_key": public.hex(), "actions": ["approved"],
                  "not_before": stamp(now - timedelta(days=1)), "not_after": stamp(now + timedelta(days=1))}]}
    with TemporaryDirectory(prefix="uir-fictional-prepared-receipt-") as scratch:
        candidate_path, proof_path, policy_path = [Path(scratch) / name for name in ("candidate.json", "proof.json", "policy.json")]
        candidate_path.write_bytes(canonical(record) + b"\n")
        prepared = prepare_knowledge(root, candidate_path)
        payload = {"format": PAYLOAD, "project_id": before["project_id"], "record_id": record["record_id"],
                   "preparation_id": prepared["preparation_id"], **body["origin"], "action": "approved", "recorded_at": stamp(now)}
        del payload["kind"]
        envelope = {"format": BINDING, "algorithm": "ed25519", "key_id": key_id, "payload": payload}
        signed = dict(envelope, signature=key.sign(signing_bytes(envelope)).hex())
        proof = dict(signed, receipt_id=identity(signed))
        proof_path.write_bytes(canonical(proof) + b"\n")
        policy_path.write_bytes(canonical(policy) + b"\n")
        command = [sys.executable, "-B", "-m", "universal_ir", "verify-preparation", str(root), str(candidate_path),
                   "--receipt", str(proof_path), "--policy", str(policy_path), "--policy-id", identity(policy),
                   "--preparation-id", prepared["preparation_id"]]
        verified = json.loads(subprocess.run(command, cwd=tool, capture_output=True, check=True).stdout)
        host = PreparedReceiptVerifier(root=root, project_id=before["project_id"], policy_path=policy_path,
                                       policy_id=identity(policy), reviews={prepared["preparation_id"]: {
                                           "record_id": record["record_id"], "candidate_path": candidate_path,
                                           "receipt_id": proof["receipt_id"], "receipt_path": proof_path}}, clock=lambda: now)
        request = canonical({"preparation_id": prepared["preparation_id"]})
        hosted = host.handle(request)
        if hosted["status"] != "ok":
            raise RuntimeError("Fictional host failed exact prepared review verification.")
        changed = dict(unsigned, body=dict(body, text="Retain archived tasks for 90 days."))
        candidate_path.write_bytes(canonical(dict(changed, record_id=identity(changed))) + b"\n")
        stale = subprocess.run(command, cwd=tool, capture_output=True)
        rejected = host.handle(request)
        if stale.returncode != 2 or stale.stdout or json.loads(stale.stderr)["error"]["code"] != "stale_preparation" or rejected["error"]["code"] != "stale_preparation":
            raise RuntimeError("Changed proposal reused the fictional review.")
    after = inspect_knowledge(root, selected_id="retention", full=True)
    if any(before[field] != after[field] for field in ("snapshot", "records", "groups")):
        raise RuntimeError("Fictional verification changed the project.")
    return {"format": "uir.fictional-prepared-receipt-demo.v1", "status": "ok", "verification": verified,
            "host_result": hosted, "changed_proposal": rejected, "stored_heads_unchanged": heads,
            "project_writes": False, "real_user_approval": "not_demonstrated", "accepted_resolution": "not_established"}


if __name__ == "__main__":
    print(json.dumps(run_demo(), ensure_ascii=True, indent=2, allow_nan=False))
