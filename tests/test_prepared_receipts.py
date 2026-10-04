"""Review-context binding, old-profile isolation, freshness, and host tool checks."""

import builtins
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from universal_ir.__main__ import main
from universal_ir.harness import PreparedReceiptVerifier, prepared_tool_definition
from universal_ir.inventory import ChangedDuringCapture, InventoryError, canonical, identity
from universal_ir.knowledge import inspect_knowledge
from universal_ir.preparation import prepare_knowledge
from universal_ir.prepared_receipts import BINDING, DOMAIN, FORMAT, PAYLOAD, verify_candidate_receipt
from universal_ir.receipts import POLICY, DOMAIN as OLD_DOMAIN, verify_receipt


class PreparedReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="uir-prepared-receipt-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        stamp = lambda value: value.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.config = {"version": 1, "project_id": "sample", "exclude": [], "documents": ["README.md"]}
        self.write(".uir/config/project.json", canonical(self.config) + b"\n")
        self.write("README.md", "# Project\nKeep tenants apart.\n")
        self.body = {"id": "isolation", "category": "requirement", "text": "Keep tenants apart.",
                     "scope": ["."], "origin": {"kind": "developer_statement", "host_id": "test-host",
                     "actor_id": "test-alice", "event_id": "test-event"}, "input_id": None,
                     "evidence": [], "supersedes": [], "state": "active"}
        self.candidate_path = self.base / "candidate.json"
        self.update_candidate(self.body)
        self.key = Ed25519PrivateKey.generate()
        public = self.key.public_key().public_bytes_raw()
        self.key_id = "sha256:" + hashlib.sha256(public).hexdigest()
        self.policy = {"format": POLICY, "project_id": "sample", "observed_at": stamp(self.now - timedelta(days=1)),
                       "valid_until": stamp(self.now + timedelta(days=1)), "revoked_receipts": [], "grants": [{
                           "host_id": "test-host", "actor_id": "test-alice", "key_id": self.key_id,
                           "public_key": public.hex(), "actions": ["approved"],
                           "not_before": stamp(self.now - timedelta(days=1)), "not_after": stamp(self.now + timedelta(days=1))}]}
        self.proof_path, self.policy_path = self.base / "proof.json", self.base / "policy.json"
        self.policy_path.write_bytes(canonical(self.policy) + b"\n")
        self.sign()

    def write(self, path, data):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data.encode() if isinstance(data, str) else data)
        return target

    def update_candidate(self, body):
        unsigned = {"format": "uir.knowledge.v1", "project_id": "sample", "body": body}
        self.record = dict(unsigned, record_id=identity(unsigned))
        self.candidate_path.write_bytes(canonical(self.record) + b"\n")
        self.prepared = prepare_knowledge(self.root, self.candidate_path)

    def sign(self, *, updates=None, domain=DOMAIN, key=None, key_id=None):
        origin = self.record["body"]["origin"]
        payload = {"format": PAYLOAD, "project_id": "sample", "record_id": self.record["record_id"],
                   "preparation_id": self.prepared["preparation_id"], "host_id": origin.get("host_id", "test-host"),
                   "actor_id": origin.get("actor_id", "test-alice"), "event_id": origin.get("event_id", "test-event"),
                   "action": "approved", "recorded_at": self.now.strftime("%Y-%m-%dT%H:%M:%SZ")}
        payload.update(updates or {})
        unsigned = {"format": BINDING, "algorithm": "ed25519", "key_id": key_id or self.key_id, "payload": payload}
        signed = dict(unsigned, signature=(key or self.key).sign(domain + canonical(unsigned)).hex())
        self.proof = dict(signed, receipt_id=identity(signed))
        self.proof_path.write_bytes(canonical(self.proof) + b"\n")

    def verify(self, *, preparation_id=None, policy_id=None, **options):
        return verify_candidate_receipt(self.root, self.candidate_path, self.proof_path, self.policy_path,
                                        policy_id or identity(self.policy), preparation_id or self.prepared["preparation_id"],
                                        clock=lambda: self.now, **options)

    def assert_error(self, code, call):
        with self.assertRaises(InventoryError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def host(self, **updates):
        review = {"record_id": self.record["record_id"], "candidate_path": self.candidate_path,
                  "receipt_id": self.proof["receipt_id"], "receipt_path": self.proof_path}
        config = dict(root=self.root, project_id="sample", policy_path=self.policy_path, policy_id=identity(self.policy),
                      reviews={self.prepared["preparation_id"]: review}, clock=lambda: self.now)
        config.update(updates)
        return PreparedReceiptVerifier(**config)

    def request(self, host=None, **updates):
        request = dict(preparation_id=self.prepared["preparation_id"])
        request.update(updates)
        return (host or self.host()).handle(canonical(request))

    def test_valid_external_assertion_binds_exact_record_and_review_without_writes(self):
        before = {p.relative_to(self.base): p.read_bytes() for p in self.base.rglob("*") if p.is_file()}
        result = self.verify()
        self.assertEqual(result["format"], FORMAT)
        self.assertEqual(result["verification"], "verified_under_pinned_policy")
        self.assertEqual(result["preparation_id"], self.prepared["preparation_id"])
        self.assertEqual(result["preparation"]["candidate"]["record"], self.record)
        self.assertEqual(result["acceptance"], "not_established")
        self.assertEqual(result["replay"], "not_checked")
        self.assertEqual(result["human_event_authentication"], "not_established")
        self.assertEqual(inspect_knowledge(self.root)["records"]["total"], 0)
        self.assertEqual(before, {p.relative_to(self.base): p.read_bytes() for p in self.base.rglob("*") if p.is_file()})

    def test_changed_wording_scope_and_supersession_cannot_reuse_review(self):
        original = self.prepared["preparation_id"]
        for changes in ({"text": "Different wording."}, {"scope": ["future"]}, {"supersedes": ["sha256:" + "a" * 64]}):
            with self.subTest(changes=changes):
                self.update_candidate(dict(self.body, **changes))
                self.assert_error("stale_preparation", lambda: self.verify(preparation_id=original))
                self.assert_error("receipt_subject_mismatch", self.verify)

    def test_source_add_delete_and_configuration_invalidate_same_record_review(self):
        original = self.prepared["preparation_id"]
        for name in ("new.py", "other.txt"):
            self.write(name, "manual edit\n")
            self.assert_error("stale_preparation", lambda: self.verify(preparation_id=original))
            (self.root / name).unlink()
        (self.root / "README.md").unlink()
        self.assert_error("stale_preparation", self.verify)
        self.write("README.md", "# Project\nKeep tenants apart.\n")
        self.write(".uir/config/project.json", canonical(dict(self.config, documents=[])) + b"\n")
        self.assert_error("stale_preparation", self.verify)

    def test_new_history_and_installing_candidate_invalidate_prepublication_context(self):
        self.write(f".uir/knowledge/records/isolation/{self.record['record_id'][7:]}.json", canonical(self.record) + b"\n")
        self.assert_error("stale_preparation", self.verify)
        entry = inspect_knowledge(self.root)["records"]["entries"][0]
        self.assertEqual(entry["attribution"], "unverified_attribution")
        self.assertEqual(entry["disposition"], "pending_acceptance")

    def test_correctly_signed_other_review_is_not_a_match(self):
        self.sign(updates={"preparation_id": "sha256:" + "0" * 64})
        self.assert_error("receipt_subject_mismatch", self.verify)

    def test_context_field_tampering_cannot_reuse_signature(self):
        self.sign(updates={"preparation_id": "sha256:" + "0" * 64})
        self.proof["payload"]["preparation_id"] = self.prepared["preparation_id"]
        self.proof["receipt_id"] = identity({k: v for k, v in self.proof.items() if k != "receipt_id"})
        self.proof_path.write_bytes(canonical(self.proof) + b"\n")
        self.assert_error("invalid_receipt_signature", self.verify)

    def test_old_profile_and_domain_are_not_contextual_approval(self):
        self.sign(domain=OLD_DOMAIN)
        self.assert_error("invalid_receipt_signature", self.verify)
        self.proof["format"] = "uir.signed-knowledge-receipt.v1"
        self.proof["payload"]["format"] = "uir.knowledge-receipt.v1"
        del self.proof["payload"]["preparation_id"]
        self.proof["receipt_id"] = identity({k: v for k, v in self.proof.items() if k != "receipt_id"})
        self.proof_path.write_bytes(canonical(self.proof) + b"\n")
        self.assert_error("invalid_receipt", self.verify)
        self.sign()
        self.assert_error("invalid_receipt", lambda: verify_receipt(self.record, self.proof, self.policy,
                                                                    identity(self.policy), now=self.now))

    def test_stated_action_and_ai_origin_do_not_gain_contextual_approval(self):
        self.sign(updates={"action": "stated"})
        self.assert_error("invalid_receipt", self.verify)
        manifest = self.prepared["preconditions"]
        self.update_candidate(dict(self.body, origin={"kind": "ai_interpretation", "host_id": "test-host", "method": "test", "assumptions": []},
                                   input_id=manifest["source_input_id"], evidence=[{"kind": "file", "path": "README.md",
                                   "content_id": "sha256:" + hashlib.sha256((self.root / "README.md").read_bytes()).hexdigest()}]))
        self.sign()
        self.assert_error("receipt_subject_mismatch", self.verify)

    def test_host_actor_event_record_and_project_bindings_are_exact(self):
        for field in ("host_id", "actor_id", "event_id", "project_id", "record_id"):
            value = "sha256:" + "a" * 64 if field == "record_id" else "another"
            self.sign(updates={field: value})
            self.assert_error("receipt_subject_mismatch", self.verify)

    def test_forged_key_cannot_select_new_authority(self):
        key = Ed25519PrivateKey.generate()
        key_id = "sha256:" + hashlib.sha256(key.public_key().public_bytes_raw()).hexdigest()
        self.sign(key=key, key_id=key_id)
        self.assert_error("receipt_not_authorized", self.verify)
        self.assert_error("trust_policy_mismatch", lambda: self.verify(policy_id="sha256:" + "a" * 64))

    def test_revocation_expiry_and_action_grants_apply_to_contextual_profile(self):
        self.policy["revoked_receipts"] = [self.proof["receipt_id"]]
        self.policy_path.write_bytes(canonical(self.policy) + b"\n")
        self.assert_error("receipt_revoked", self.verify)
        self.policy["revoked_receipts"] = []
        self.policy["grants"][0]["actions"] = ["stated"]
        self.policy_path.write_bytes(canonical(self.policy) + b"\n")
        self.assert_error("receipt_not_authorized", self.verify)
        expired = self.host(clock=lambda: self.now + timedelta(days=1)).handle(canonical({"preparation_id": self.prepared["preparation_id"]}))
        self.assertEqual(expired["error"]["code"], "trust_policy_not_current")

    def test_missing_optional_crypto_fails_closed_but_preparation_still_works(self):
        actual = builtins.__import__
        def unavailable(name, *args, **kwargs):
            if name.startswith("cryptography"):
                raise ImportError("unavailable")
            return actual(name, *args, **kwargs)
        with patch("builtins.__import__", side_effect=unavailable):
            self.assert_error("receipt_verifier_unavailable", self.verify)
            self.assertEqual(prepare_knowledge(self.root, self.candidate_path)["status"], "ok")

    def test_unresolved_support_and_future_scope_remain_explicit_despite_signature(self):
        self.update_candidate(dict(self.body, scope=["future"], evidence=[{"kind": "file", "path": "missing.py", "content_id": "sha256:" + "a" * 64}]))
        self.sign()
        result = self.verify()
        self.assertEqual(result["observation"]["record_evidence"], "unresolved")
        self.assertEqual(result["preparation"]["candidate"]["evaluation"]["unresolved_scope"], ["future"])
        self.assertEqual(result["acceptance"], "not_established")

    def test_ignored_store_does_not_become_complete_or_accepted(self):
        self.write(f".uir/knowledge/records/isolation/{self.record['record_id'][7:]}.json", canonical(self.record) + b"\n")
        self.write(".gitignore", ".uir/knowledge/\n")
        self.prepared = prepare_knowledge(self.root, self.candidate_path)
        self.sign()
        result = self.verify()
        self.assertFalse(result["observation"]["coverage_complete"])
        self.assertEqual(result["acceptance"], "not_established")

    def test_normalized_candidate_transport_keeps_the_same_review(self):
        self.candidate_path.write_bytes((json.dumps(self.record, indent=2) + "\n").encode())
        self.assertEqual(self.verify()["preparation_id"], self.prepared["preparation_id"])

    def test_new_host_tool_fixes_registry_pins_and_accepts_only_preparation_id(self):
        definition = prepared_tool_definition()
        self.assertEqual(set(definition["input_schema"]["properties"]), {"preparation_id"})
        self.assertEqual(self.request()["result"]["format"], FORMAT)
        with patch("universal_ir.harness.verify_candidate_receipt") as verify:
            for field in ("candidate_path", "record_id", "receipt_id", "receipt_path", "policy_id", "policy_path", "root", "clock", "approved"):
                self.assertEqual(self.request(**{field: "attacker"})["error"]["code"], "invalid_tool_request")
            verify.assert_not_called()

    def test_unknown_review_and_strict_json_fail_without_scanning(self):
        host = self.host()
        with patch("universal_ir.harness.verify_candidate_receipt") as verify:
            self.assertEqual(host.handle(canonical({"preparation_id": "sha256:" + "0" * 64}))["error"]["code"], "unknown_preparation")
            for data in (b"null", b"{}", b" " * 1025, b'"fake"', b'{"preparation_id":1,"preparation_id":2}'):
                self.assertEqual(host.handle(data)["error"]["code"], "invalid_tool_request")
            verify.assert_not_called()

    def test_nested_registry_is_copied_and_verified_content_ids_are_checked(self):
        review = {"record_id": self.record["record_id"], "candidate_path": self.candidate_path,
                  "receipt_id": self.proof["receipt_id"], "receipt_path": self.proof_path}
        registry = {self.prepared["preparation_id"]: review}
        host = self.host(reviews=registry)
        review["receipt_id"] = "sha256:" + "a" * 64
        registry.clear()
        self.assertEqual(self.request(host)["status"], "ok")
        bad = self.host(reviews={self.prepared["preparation_id"]: review})
        self.assertEqual(self.request(bad)["error"]["code"], "receipt_lookup_mismatch")

    def test_invalid_host_registry_is_not_a_model_enrollment_interface(self):
        for registry in ([], {"bad": {}}, {self.prepared["preparation_id"]: {}},
                         {self.prepared["preparation_id"]: {"record_id": "bad", "receipt_id": self.proof["receipt_id"],
                          "candidate_path": self.candidate_path, "receipt_path": self.proof_path}}):
            with self.assertRaises(InventoryError) as caught:
                self.host(reviews=registry)
            self.assertEqual(caught.exception.code, "invalid_host_configuration")

    def test_host_project_change_and_clock_failure_have_no_verified_output(self):
        self.write(".uir/config/project.json", canonical(dict(self.config, project_id="other")) + b"\n")
        with patch("universal_ir.prepared_receipts._external_bytes") as read:
            # The candidate itself is invalid under another project, before any proof can be read.
            self.assertEqual(self.request()["error"]["code"], "invalid_knowledge")
            read.assert_not_called()
        self.write(".uir/config/project.json", canonical(self.config) + b"\n")
        def broken():
            raise OSError("private detail")
        result = self.request(self.host(clock=broken))
        self.assertEqual(result["error"]["code"], "host_clock_unavailable")
        self.assertNotIn("private detail", str(result))

    def test_input_changes_reconcile_then_reject_old_review(self):
        from universal_ir import prepared_receipts
        real = prepared_receipts.prepare_knowledge
        calls = 0
        def changed(*args, **kwargs):
            nonlocal calls
            prepared = real(*args, **kwargs)
            calls += 1
            if calls == 1:
                self.write("external.txt", "changed\n")
            return prepared
        with patch("universal_ir.prepared_receipts.prepare_knowledge", side_effect=changed):
            self.assert_error("stale_preparation", self.verify)
        self.assertGreater(calls, 2)

    def test_host_transport_races_retry_and_sustained_edits_fail_closed(self):
        from universal_ir import prepared_receipts
        real = prepared_receipts._external_bytes
        calls = 0
        def changed(path, root):
            nonlocal calls
            data = real(path, root)
            calls += 1
            if calls == 2:
                self.policy_path.write_bytes(self.policy_path.read_bytes() + b" ")
            return data
        with patch("universal_ir.prepared_receipts._external_bytes", side_effect=changed):
            self.assertEqual(self.verify()["status"], "ok")
        self.assertGreater(calls, 4)
        with patch("universal_ir.prepared_receipts._external_bytes", side_effect=ChangedDuringCapture()):
            self.assert_error("unstable_inputs", self.verify)

    def test_bad_pins_transport_and_profile_fields_are_not_successes(self):
        self.assert_error("invalid_arguments", lambda: self.verify(preparation_id="bad"))
        self.assert_error("invalid_arguments", lambda: self.verify(policy_id="bad"))
        for data in (b'null\n', b'{"format":1,"format":2}\n', b'{"bad":NaN}\n', b'\xff\n'):
            self.proof_path.write_bytes(data)
            self.assert_error("invalid_receipt", self.verify)
        self.sign()
        self.proof["payload"]["extra"] = True
        self.proof_path.write_bytes(canonical(self.proof) + b"\n")
        self.assert_error("invalid_receipt", self.verify)
        self.sign()
        self.proof_path = self.root / "proof.json"
        self.assert_error("invalid_host_input", self.verify)

    def test_repeat_verification_is_not_event_consumption(self):
        first, second = self.verify(), self.verify()
        self.assertEqual(first["receipt_id"], second["receipt_id"])
        self.assertEqual(second["replay"], "not_checked")

    def test_unrepresentable_external_host_paths_return_structured_failures(self):
        for path in ("bad\x00path", "bad\ud800path", None):
            with self.subTest(path=repr(path)):
                self.proof_path = path
                self.assert_error("invalid_host_input", self.verify)

    def test_real_cli_reports_valid_and_stale_review_separately(self):
        tool = Path(__file__).resolve().parents[1]
        command = [sys.executable, "-B", "-m", "universal_ir", "verify-preparation", str(self.root), str(self.candidate_path),
                   "--receipt", str(self.proof_path), "--policy", str(self.policy_path), "--policy-id", identity(self.policy),
                   "--preparation-id", self.prepared["preparation_id"]]
        valid = subprocess.run(command, cwd=tool, capture_output=True, check=True)
        self.assertEqual(json.loads(valid.stdout)["format"], FORMAT)
        self.write("manual.py", "pass\n")
        invalid = subprocess.run(command, cwd=tool, capture_output=True)
        self.assertEqual(invalid.returncode, 2)
        self.assertFalse(invalid.stdout)
        self.assertEqual(json.loads(invalid.stderr)["error"]["code"], "stale_preparation")

    def test_unstable_cli_has_only_error_envelope(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("universal_ir.prepared_receipts._external_bytes", side_effect=ChangedDuringCapture()), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["verify-preparation", str(self.root), str(self.candidate_path), "--receipt", str(self.proof_path),
                         "--policy", str(self.policy_path), "--policy-id", identity(self.policy), "--preparation-id", self.prepared["preparation_id"]])
        self.assertEqual(code, 3)
        self.assertFalse(stdout.getvalue())
        self.assertEqual(json.loads(stderr.getvalue())["format"], FORMAT)

    def test_fictional_demo_uses_real_cli_and_keeps_fixture_unchanged(self):
        tool = Path(__file__).resolve().parents[1]
        fixture = tool / "examples/fixtures/knowledge-project"
        before = {p.relative_to(fixture): p.read_bytes() for p in fixture.rglob("*") if p.is_file()}
        result = subprocess.run([sys.executable, "-B", str(tool / "examples/prepared_receipts.py")],
                                cwd=tool, capture_output=True, check=True)
        demo = json.loads(result.stdout)
        self.assertEqual(demo["verification"]["verification"], "verified_under_pinned_policy")
        self.assertEqual(demo["changed_proposal"]["error"]["code"], "stale_preparation")
        self.assertEqual(demo["real_user_approval"], "not_demonstrated")
        self.assertEqual(demo["accepted_resolution"], "not_established")
        self.assertFalse(demo["project_writes"])
        self.assertEqual(before, {p.relative_to(fixture): p.read_bytes() for p in fixture.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
