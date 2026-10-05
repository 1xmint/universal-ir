"""Fictional software authenticator: exercise signatures, never claim consent."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from universal_ir.inventory import InventoryError, canonical, identity
from universal_ir.preparation import prepare_knowledge
from universal_ir.webauthn_review import WebAuthnReview, encode


def demonstrate():
    with TemporaryDirectory(prefix="uir-webauthn-demo-") as directory:
        base = Path(directory)
        root = base / "project"
        config = root / ".uir/config"
        config.mkdir(parents=True)
        (config / "project.json").write_bytes(canonical({"version": 1, "project_id": "fictional-passkey-demo", "exclude": [], "documents": []}) + b"\n")
        source = root / "README.md"
        source.write_bytes(b"# Fictional project\nKeep tenants apart.\n")
        unsigned = {"format": "uir.knowledge.v1", "project_id": "fictional-passkey-demo", "body": {
            "id": "isolation", "category": "requirement", "text": "Keep tenants apart.", "scope": ["."],
            "origin": {"kind": "developer_statement", "host_id": "fictional-host", "actor_id": "fictional-alice", "event_id": "fictional-event"},
            "input_id": None, "evidence": [], "supersedes": [], "state": "active"}}
        candidate = base / "candidate.json"
        candidate.write_bytes(canonical(dict(unsigned, record_id=identity(unsigned))) + b"\n")
        prepared = prepare_knowledge(root, candidate)
        key = ec.generate_private_key(ec.SECP256R1())
        point = key.public_key().public_numbers()
        credential = {"id": encode(b"fictional-credential"), "public_key_x": encode(point.x.to_bytes(32, "big")),
                      "public_key_y": encode(point.y.to_bytes(32, "big")), "user_handle": encode(b"fictional-alice"), "sign_count": 0}
        review = WebAuthnReview(root=root, candidate_path=candidate, preparation_id=prepared["preparation_id"],
                               project_id="fictional-passkey-demo", host_id="fictional-host", actor_id="fictional-alice",
                               event_id="fictional-event", rp_id="localhost", origin="http://localhost:8765", credential=credential,
                               clock=lambda: datetime.now(timezone.utc))
        browser = review.options()
        client = canonical({"type": "webauthn.get", "challenge": browser["options"]["publicKey"]["challenge"],
                            "origin": "http://localhost:8765", "crossOrigin": False})
        authenticator = hashlib.sha256(b"localhost").digest() + bytes([5]) + b"\x00" * 4
        signature = key.sign(authenticator + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
        assertion = canonical({"id": credential["id"], "rawId": credential["id"], "type": "public-key", "response": {
            "clientDataJSON": encode(client), "authenticatorData": encode(authenticator), "signature": encode(signature), "userHandle": None}})
        before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        verified = review.verify(assertion)
        preserved = before == {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        source.write_bytes(b"# Fictional project\nManual source change.\n")
        try:
            review.verify(assertion)
        except InventoryError as error:
            rejected = error.code
        else:
            raise AssertionError("Stale review unexpectedly verified.")
        return {"status": "ok", "verification": verified["verification"], "preparation_id": prepared["preparation_id"],
                "source_change_rejected": rejected, "verification_preserved_files": preserved,
                "real_user_demonstrated": False, "enrollment_demonstrated": False, "browser_ceremony_demonstrated": False,
                "acceptance": "not_established", "model_calls": 0}


if __name__ == "__main__":
    print(json.dumps(demonstrate(), indent=2))
