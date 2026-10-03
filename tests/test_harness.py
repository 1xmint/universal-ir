"""Adversarial tool requests, fixed host bindings, freshness, and preservation."""

from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from universal_ir.harness import FORMAT, HarnessVerifier, tool_definition
from universal_ir.inventory import InventoryError, canonical, identity, parse_json
from universal_ir.knowledge import inspect_knowledge
from universal_ir.receipts import BINDING, DOMAIN, POLICY


class HarnessTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="uir-harness-test-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.now = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)
        stamp = lambda value: value.strftime("%Y-%m-%dT%H:%M:%SZ")
        body = {"id": "isolation", "category": "requirement", "text": "Keep tenants apart.",
                "scope": ["."], "origin": {"kind": "developer_statement", "host_id": "test-host",
                "actor_id": "test-alice", "event_id": "test-event"}, "input_id": None,
                "evidence": [], "supersedes": [], "state": "active"}
        unsigned = {"format": "uir.knowledge.v1", "project_id": "test-project", "body": body}
        self.record = dict(unsigned, record_id=identity(unsigned))
        config_path = self.root / ".uir/config/project.json"
        config_path.parent.mkdir(parents=True)
        self.config = {"version": 1, "project_id": "test-project", "exclude": [], "documents": []}
        config_path.write_bytes(canonical(self.config) + b"\n")
        self.record_path = self.root / ".uir/knowledge/records/isolation" / (self.record["record_id"][7:] + ".json")
        self.record_path.parent.mkdir(parents=True)
        self.record_path.write_bytes(canonical(self.record) + b"\n")
        key = Ed25519PrivateKey.generate()
        public = key.public_key().public_bytes_raw()
        key_id = "sha256:" + hashlib.sha256(public).hexdigest()
        payload = {"format": "uir.knowledge-receipt.v1", "project_id": "test-project",
                   "record_id": self.record["record_id"], "host_id": "test-host", "actor_id": "test-alice",
                   "event_id": "test-event", "action": "approved", "recorded_at": stamp(self.now)}
        signed = {"format": BINDING, "algorithm": "ed25519", "key_id": key_id, "payload": payload}
        signed["signature"] = key.sign(DOMAIN + canonical(signed)).hex()
        self.proof = dict(signed, receipt_id=identity(signed))
        self.policy = {"format": POLICY, "project_id": "test-project",
                       "observed_at": stamp(self.now - timedelta(days=1)),
                       "valid_until": stamp(self.now + timedelta(days=1)), "revoked_receipts": [], "grants": [{
                           "host_id": "test-host", "actor_id": "test-alice", "key_id": key_id,
                           "public_key": public.hex(), "actions": ["approved"],
                           "not_before": stamp(self.now - timedelta(days=1)),
                           "not_after": stamp(self.now + timedelta(days=1))}]}
        self.proof_path, self.policy_path = self.base / "proof.json", self.base / "policy.json"
        self.proof_path.write_bytes(canonical(self.proof) + b"\n")
        self.policy_path.write_bytes(canonical(self.policy) + b"\n")
        self.arguments = {"record_id": self.record["record_id"], "receipt_id": self.proof["receipt_id"]}
        self.configuration = {"root": self.root, "project_id": "test-project", "policy_path": self.policy_path,
                              "policy_id": identity(self.policy),
                              "receipt_paths": {self.proof["receipt_id"]: self.proof_path}, "clock": lambda: self.now}
        self.host = HarnessVerifier(**self.configuration)

    def call(self, arguments=None, host=None):
        return (host or self.host).handle(canonical(self.arguments if arguments is None else arguments))

    def assert_failure(self, code, result):
        self.assertEqual(result["format"], FORMAT)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["code"], code)
        self.assertNotIn("result", result)

    def test_fixed_host_policy_project_and_clock_produce_real_verification(self):
        result = self.call()
        self.assertEqual(result["status"], "ok")
        verified = result["result"]
        self.assertEqual(verified["trust_policy_id"], self.configuration["policy_id"])
        self.assertEqual(verified["project_id"], self.configuration["project_id"])
        self.assertEqual(verified["receipt_id"], self.arguments["receipt_id"])
        self.assertEqual(verified["verified_at"], self.now.isoformat())
        self.assertEqual(verified["acceptance"], "not_established")
        self.assertEqual(verified["replay"], "not_checked")

    def test_schema_is_narrow_and_returned_metadata_is_independent(self):
        definition = tool_definition()
        self.assertEqual(definition["name"], "uir_verify_receipt")
        schema = definition["input_schema"]
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["properties"]), {"record_id", "receipt_id"})
        schema["properties"]["policy_id"] = {"type": "string"}
        self.assertNotIn("policy_id", tool_definition()["input_schema"]["properties"])

    def test_authority_and_command_substitution_fail_before_any_scan(self):
        with patch("universal_ir.harness.verify_project_receipt") as verify:
            for field in ("root", "project_id", "policy_path", "policy_id", "receipt_path", "clock",
                          "actor_id", "event_id", "action", "approved", "command", "public_key"):
                with self.subTest(field=field):
                    self.assert_failure("invalid_tool_request", self.call(dict(self.arguments, **{field: "attacker"})))
            verify.assert_not_called()

    def test_strict_bounded_json_is_checked_without_reading_project(self):
        key = self.arguments["record_id"]
        invalid = [b"{}", b"[]", b"null", b"{", b"\xff", b" " * 1025, {"record_id": key},
                   canonical(dict(self.arguments, record_id=None)), canonical(dict(self.arguments, receipt_id="../../policy")),
                   b'{"record_id":NaN,"receipt_id":"' + key.encode() + b'"}',
                   ('{"record_id":"' + key + '","record_id":"' + key + '","receipt_id":"' + key + '"}').encode(),
                   ('{"record_id":"' + key + '","receipt_id":"\\ud800"}').encode(),
                   canonical(dict(self.arguments, record_id=key + "\n"))]
        with patch("universal_ir.harness.verify_project_receipt") as verify:
            for request in invalid:
                with self.subTest(request=str(request)[:100]):
                    self.assert_failure("invalid_tool_request", self.host.handle(request))
            verify.assert_not_called()

    def test_unknown_receipt_does_not_discover_model_supplied_files(self):
        with patch("universal_ir.harness.verify_project_receipt") as verify:
            self.assert_failure("unknown_receipt", self.call(dict(self.arguments, receipt_id="sha256:" + "0" * 64)))
            verify.assert_not_called()

    def test_exact_request_byte_limit_is_accepted(self):
        request = canonical(self.arguments)
        self.assertEqual(self.host.handle(request + b" " * (1024 - len(request)))["status"], "ok")

    def test_original_registry_mutation_cannot_rebind_existing_host(self):
        self.configuration["receipt_paths"].clear()
        self.configuration["policy_id"] = "sha256:" + "0" * 64
        self.assertEqual(self.call()["status"], "ok")

    def test_registered_filename_does_not_establish_receipt_identity(self):
        wrong_id = "sha256:" + "a" * 64
        host = HarnessVerifier(**dict(self.configuration, receipt_paths={wrong_id: self.proof_path}))
        self.assert_failure("receipt_lookup_mismatch", self.call(dict(self.arguments, receipt_id=wrong_id), host))

    def test_registered_receipt_replacement_does_not_bypass_signature_or_lookup(self):
        forged = dict(self.proof, signature="00" * 64)
        forged["receipt_id"] = identity({name: value for name, value in forged.items() if name != "receipt_id"})
        self.proof_path.write_bytes(canonical(forged) + b"\n")
        self.assert_failure("invalid_receipt_signature", self.call())
        self.assert_failure("unknown_receipt", self.call(dict(self.arguments, receipt_id=forged["receipt_id"])))

    def test_missing_registered_input_is_not_recovered_from_project_files(self):
        self.proof_path.unlink()
        (self.root / "receipt.json").write_bytes(canonical(self.proof) + b"\n")
        self.assert_failure("invalid_host_input", self.call())

    def test_detected_repeated_input_changes_return_only_failure(self):
        with patch("universal_ir.receipts.inspect_knowledge", side_effect=InventoryError("unstable_inputs", "changed")):
            self.assert_failure("unstable_inputs", self.call())

    def test_record_identity_is_not_interchangeable(self):
        other = "sha256:" + "a" * 64
        self.assert_failure("unknown_knowledge", self.call(dict(self.arguments, record_id=other)))

    def test_configuration_project_change_fails_before_host_files_are_read(self):
        self.record_path.unlink()
        config = dict(self.config, project_id="different-project")
        (self.root / ".uir/config/project.json").write_bytes(canonical(config) + b"\n")
        with patch("universal_ir.receipts._external_bytes") as read:
            self.assert_failure("host_project_mismatch", self.call())
            read.assert_not_called()

    def test_policy_updates_require_host_reconfiguration_and_pinned_revocation_is_enforced(self):
        policy = dict(self.policy, revoked_receipts=[self.proof["receipt_id"]])
        self.policy_path.write_bytes(canonical(policy) + b"\n")
        self.assert_failure("trust_policy_mismatch", self.call())
        revoked_host = HarnessVerifier(**dict(self.configuration, policy_id=identity(policy)))
        self.assert_failure("receipt_revoked", self.call(host=revoked_host))

    def test_expiry_and_failed_or_invalid_host_clock_fail_closed(self):
        expired = HarnessVerifier(**dict(self.configuration, clock=lambda: self.now + timedelta(days=1)))
        self.assert_failure("trust_policy_not_current", self.call(host=expired))
        invalid = HarnessVerifier(**dict(self.configuration, clock=lambda: "model-time"))
        self.assert_failure("invalid_verification_time", self.call(host=invalid))

        def broken():
            raise OSError("private host detail")

        failed = HarnessVerifier(**dict(self.configuration, clock=broken))
        result = self.call(host=failed)
        self.assert_failure("host_clock_unavailable", result)
        self.assertNotIn("private host detail", str(result))

    def test_host_transport_errors_do_not_disclose_paths_to_model(self):
        with patch("universal_ir.harness.verify_project_receipt",
                   side_effect=InventoryError("unreadable_input", str(self.policy_path))):
            result = self.call()
        self.assert_failure("unreadable_input", result)
        self.assertNotIn(str(self.policy_path), str(result))

    def test_source_edits_refresh_observation_and_default_claims_remain_unverified(self):
        before = self.call()["result"]
        (self.root / "new.py").write_bytes(b"print('external edit')\n")
        after = self.call()["result"]
        self.assertNotEqual(before["observation"]["snapshot"], after["observation"]["snapshot"])
        self.assertFalse(after["observation"]["atomic"])
        view = inspect_knowledge(self.root, full=True)
        self.assertEqual(view["records"]["entries"][0]["attribution"], "unverified_attribution")

    def test_success_failure_and_retries_never_write_source_or_host_inputs(self):
        before = {path.relative_to(self.base): path.read_bytes() for path in self.base.rglob("*") if path.is_file()}
        first, second = self.call(), self.call()
        self.assertEqual(first["result"]["receipt_id"], second["result"]["receipt_id"])
        self.assertEqual(second["result"]["replay"], "not_checked")
        self.assert_failure("invalid_tool_request", self.call(dict(self.arguments, approved=True)))
        after = {path.relative_to(self.base): path.read_bytes() for path in self.base.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_bad_host_configuration_fails_without_exposing_tool(self):
        for update in ({"project_id": ""}, {"project_id": "\ud800"}, {"policy_id": "bad"},
                       {"receipt_paths": []}, {"clock": "model-clock"}, {"root": None}, {"root": "bad\x00path"},
                       {"policy_path": "\ud800"},
                       {"receipt_paths": {"bad": self.proof_path}}):
            with self.subTest(update=str(update)):
                with self.assertRaises(InventoryError) as caught:
                    HarnessVerifier(**dict(self.configuration, **update))
                self.assertEqual(caught.exception.code, "invalid_host_configuration")

    def test_real_fictional_walkthrough_rejects_authority_substitution(self):
        tool = Path(__file__).resolve().parents[1]
        demo = subprocess.run([sys.executable, "-B", "examples/verify_host_receipt.py"],
                              cwd=tool, capture_output=True, check=True)
        report = parse_json(demo.stdout)
        self.assertEqual(report["approval_source"], "scripted_fictional_event")
        self.assertEqual(report["real_user_integration"], "not_demonstrated")
        self.assertEqual(report["harness"]["valid_receipt"]["status"], "ok")
        self.assertEqual(report["harness"]["authority_substitution"], "invalid_tool_request")
        self.assertEqual(report["harness"]["unknown_receipt"], "unknown_receipt")


if __name__ == "__main__":
    unittest.main()
