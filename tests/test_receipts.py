"""Host binding, tampering, revocation, freshness, and CLI failure checks."""

from contextlib import redirect_stderr, redirect_stdout
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from universal_ir.__main__ import main
from universal_ir.inventory import InventoryError, canonical, identity
from universal_ir.knowledge import inspect_knowledge
from universal_ir.receipts import (
    BINDING, DOMAIN, FORMAT, POLICY, validate_policy, validate_receipt,
    verify_project_receipt, verify_receipt,
)


def stamp(value):
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.key = Ed25519PrivateKey.generate()
        public = self.key.public_key().public_bytes_raw()
        self.key_id = "sha256:" + hashlib.sha256(public).hexdigest()
        self.body = {"id": "tenant-isolation", "category": "requirement", "text": "Keep tenants apart.",
                     "scope": ["."], "origin": {"kind": "developer_statement", "host_id": "test-harness",
                     "actor_id": "test-alice", "event_id": "event-1"}, "input_id": None,
                     "evidence": [], "supersedes": [], "state": "active"}
        self.record = self.make_record(self.body)
        self.policy = {"format": POLICY, "project_id": "test-project",
                       "observed_at": stamp(self.now - timedelta(days=1)),
                       "valid_until": stamp(self.now + timedelta(days=1)),
                       "revoked_receipts": [], "grants": [{
                           "host_id": "test-harness", "actor_id": "test-alice", "key_id": self.key_id,
                           "public_key": public.hex(), "actions": ["stated", "approved"],
                           "not_before": stamp(self.now - timedelta(days=30)),
                           "not_after": stamp(self.now + timedelta(days=30))}]}
        self.receipt = self.sign(self.record)
        temporary = TemporaryDirectory(prefix="uir-receipt-test-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()
        config = self.root / ".uir/config/project.json"
        config.parent.mkdir(parents=True)
        config.write_bytes(canonical({"version": 1, "project_id": "test-project", "exclude": [], "documents": []}) + b"\n")
        self.store_record(self.record)
        self.proof_path, self.policy_path = self.base / "receipt.json", self.base / "policy.json"
        self.save_inputs()

    def make_record(self, body):
        unsigned = {"format": "uir.knowledge.v1", "project_id": "test-project", "body": copy.deepcopy(body)}
        return dict(unsigned, record_id=identity(unsigned))

    def sign(self, record, *, key=None, key_id=None, payload_updates=None, domain=DOMAIN):
        origin = record["body"]["origin"]
        payload = {"format": "uir.knowledge-receipt.v1", "project_id": record["project_id"],
                   "record_id": record["record_id"], "host_id": origin.get("host_id", "test-harness"),
                   "actor_id": origin.get("actor_id", "test-alice"), "event_id": origin.get("event_id", "event-1"),
                   "action": "approved", "recorded_at": stamp(self.now)}
        payload.update(payload_updates or {})
        unsigned = {"format": BINDING, "algorithm": "ed25519", "key_id": key_id or self.key_id, "payload": payload}
        signed = dict(unsigned, signature=(key or self.key).sign(domain + canonical(unsigned)).hex())
        return dict(signed, receipt_id=identity(signed))

    def rehash(self, receipt):
        receipt["receipt_id"] = identity({key: value for key, value in receipt.items() if key != "receipt_id"})
        return receipt

    def store_record(self, record):
        path = self.root / ".uir/knowledge/records" / record["body"]["id"] / (record["record_id"][7:] + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical(record) + b"\n")
        return path

    def save_inputs(self):
        self.proof_path.write_bytes(canonical(self.receipt) + b"\n")
        self.policy_path.write_bytes(canonical(self.policy) + b"\n")

    def verify(self, *, record=None, receipt=None, policy=None, expected=None, now=None):
        policy = self.policy if policy is None else policy
        return verify_receipt(self.record if record is None else record, self.receipt if receipt is None else receipt,
                              policy, expected or identity(policy), now=self.now if now is None else now)

    def project_verify(self):
        return verify_project_receipt(self.root, self.record["record_id"], self.proof_path,
                                      self.policy_path, identity(self.policy))

    def assert_error(self, code, call):
        with self.assertRaises(InventoryError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def test_valid_receipt_binds_exact_host_actor_event_and_record(self):
        result = self.verify()
        self.assertEqual(result["verification"], "verified_under_pinned_policy")
        self.assertEqual(result["trust_policy_id"], identity(self.policy))
        self.assertEqual(result["record_id"], self.record["record_id"])
        self.assertEqual(result["receipt_id"], self.receipt["receipt_id"])
        self.assertEqual(result["actor_id"], "test-alice")
        self.assertEqual(result["acceptance"], "not_established")
        self.assertEqual(result["trust_observation"]["observed_at"], self.policy["observed_at"])
        self.assertFalse(result["trust_observation"]["live_revocation"])

    def test_changed_wording_scope_or_transition_needs_new_exact_approval(self):
        for updates in ({"text": "A changed requirement."}, {"scope": ["future"]},
                        {"supersedes": ["sha256:" + "a" * 64]}):
            with self.subTest(updates=updates):
                body = dict(self.body, **updates)
                changed = self.make_record(body)
                self.assert_error("receipt_subject_mismatch", lambda: self.verify(record=changed))

    def test_unvalidated_record_id_string_is_not_enough(self):
        forged = copy.deepcopy(self.record)
        forged["body"]["text"] = "Altered without updating the digest."
        self.assert_error("invalid_knowledge", lambda: self.verify(record=forged))

    def test_signed_other_actor_host_or_event_does_not_bind_record(self):
        for field in ("actor_id", "host_id", "event_id", "project_id", "record_id"):
            with self.subTest(field=field):
                value = "sha256:" + "a" * 64 if field == "record_id" else "other"
                signed = self.sign(self.record, payload_updates={field: value})
                self.assert_error("receipt_subject_mismatch", lambda: self.verify(receipt=signed))

    def test_payload_signature_and_domain_tampering_rejected(self):
        altered = copy.deepcopy(self.receipt)
        altered["payload"]["action"] = "stated"
        self.rehash(altered)
        self.assert_error("invalid_receipt_signature", lambda: self.verify(receipt=altered))
        forged = self.rehash(dict(self.receipt, signature="00" * 64))
        self.assert_error("invalid_receipt_signature", lambda: self.verify(receipt=forged))
        wrong_domain = self.sign(self.record, domain=b"another protocol\x00")
        self.assert_error("invalid_receipt_signature", lambda: self.verify(receipt=wrong_domain))

    def test_self_selected_key_and_key_id_substitution_rejected(self):
        attacker = Ed25519PrivateKey.generate()
        key_id = "sha256:" + hashlib.sha256(attacker.public_key().public_bytes_raw()).hexdigest()
        signed = self.sign(self.record, key=attacker, key_id=key_id)
        self.assert_error("receipt_not_authorized", lambda: self.verify(receipt=signed))
        signed = self.sign(self.record, key=attacker)
        self.assert_error("invalid_receipt_signature", lambda: self.verify(receipt=signed))

    def test_policy_pin_cannot_be_replaced_by_receipt_or_repository(self):
        changed = copy.deepcopy(self.policy)
        changed["grants"] = []
        self.assert_error("trust_policy_mismatch", lambda: self.verify(policy=changed, expected=identity(self.policy)))
        injected = dict(self.receipt, trust_policy=self.policy)
        self.assert_error("invalid_receipt", lambda: self.verify(receipt=injected))

    def test_actor_and_action_grants_are_explicit(self):
        for field, value in (("actor_id", "other"), ("host_id", "other"), ("actions", ["stated"])):
            policy = copy.deepcopy(self.policy)
            policy["grants"][0][field] = value
            self.assert_error("receipt_not_authorized", lambda: self.verify(policy=policy))

    def test_receipt_and_key_revocation_are_observed_policy_relative(self):
        revoked = dict(self.policy, revoked_receipts=[self.receipt["receipt_id"]])
        self.assert_error("receipt_revoked", lambda: self.verify(policy=revoked))
        revoked = dict(self.policy, grants=[])
        self.assert_error("receipt_not_authorized", lambda: self.verify(policy=revoked))
        # An older still-current policy cannot know about newer offline revocations.
        self.assertEqual(self.verify()["trust_policy_id"], identity(self.policy))

    def test_key_rotation_retains_explicitly_trusted_historical_receipts(self):
        issued = self.now - timedelta(days=2)
        signed = self.sign(self.record, payload_updates={"recorded_at": stamp(issued)})
        policy = copy.deepcopy(self.policy)
        policy["grants"][0]["not_after"] = stamp(self.now - timedelta(days=1))
        self.assertEqual(self.verify(policy=policy, receipt=signed)["verification"], "verified_under_pinned_policy")

    def test_policy_validity_and_trusted_clock_boundaries(self):
        for now in (self.now + timedelta(days=1), self.now - timedelta(days=2)):
            self.assert_error("trust_policy_not_current", lambda: self.verify(now=now))
        self.assert_error("invalid_verification_time", lambda: self.verify(now=self.now.replace(tzinfo=None)))

    def test_receipt_issuance_interval_and_future_time(self):
        for issued in (self.now + timedelta(seconds=1), self.now - timedelta(days=31), self.now + timedelta(days=30)):
            signed = self.sign(self.record, payload_updates={"recorded_at": stamp(issued)})
            self.assert_error("receipt_time_not_authorized", lambda: self.verify(receipt=signed))
        policy = copy.deepcopy(self.policy)
        policy["grants"][0]["not_before"] = stamp(self.now)
        self.assertEqual(self.verify(policy=policy)["verification"], "verified_under_pinned_policy")
        policy["grants"][0]["not_after"] = stamp(self.now)
        policy["grants"][0]["not_before"] = stamp(self.now - timedelta(seconds=1))
        self.assert_error("receipt_time_not_authorized", lambda: self.verify(policy=policy))

    def test_strict_receipt_shapes_encoding_and_calendar(self):
        changes = [lambda r: r.update(approved=True), lambda r: r.update(algorithm="hmac"),
                   lambda r: r.update(signature="FF" * 64), lambda r: r.update(signature="00"),
                   lambda r: r["payload"].update(recorded_at="2026-02-30T00:00:00Z"),
                   lambda r: r["payload"].update(recorded_at="2026-10-02T00:00:00+00:00"),
                   lambda r: r["payload"].update(action="accept-all"),
                   lambda r: r["payload"].update(actor_id="\ud800")]
        for change in changes:
            with self.subTest(change=change):
                receipt = copy.deepcopy(self.receipt)
                change(receipt)
                self.assert_error("invalid_receipt", lambda: validate_receipt(receipt))
        damaged = dict(self.receipt, receipt_id="sha256:" + "0" * 64)
        self.assert_error("invalid_receipt", lambda: validate_receipt(damaged))

    def test_strict_policy_shapes_keys_and_duplicates(self):
        changes = [lambda p: p.update(allow_all=True), lambda p: p.update(grants=True),
                   lambda p: p["grants"].append(copy.deepcopy(p["grants"][0])),
                   lambda p: p["grants"][0].update(public_key="00" * 32),
                   lambda p: p["grants"][0].update(actions=["approved", "approved"]),
                   lambda p: p.update(valid_until=p["observed_at"]),
                   lambda p: p.update(revoked_receipts=["sha256:" + "a" * 64] * 2)]
        for change in changes:
            with self.subTest(change=change):
                policy = copy.deepcopy(self.policy)
                change(policy)
                self.assert_error("invalid_trust_policy", lambda: validate_policy(policy, identity(policy)))

    def test_model_interpretation_is_not_promoted_by_developer_receipt(self):
        body = copy.deepcopy(self.body)
        body["origin"] = {"kind": "ai_interpretation", "host_id": "test-harness", "method": "test", "assumptions": []}
        body["input_id"] = "sha256:" + "a" * 64
        body["evidence"] = [{"kind": "record", "record_id": self.record["record_id"]}]
        record = self.make_record(body)
        signed = self.sign(record)
        self.assert_error("receipt_subject_mismatch", lambda: self.verify(record=record, receipt=signed))

    def test_repeated_verification_is_not_replayed_acceptance(self):
        first, second = self.verify(), self.verify()
        self.assertEqual(first["receipt_id"], second["receipt_id"])
        self.assertEqual(second["replay"], "not_checked")
        changed = self.make_record(dict(self.body, text="Different statement with the same claimed event."))
        result = self.verify(record=changed, receipt=self.sign(changed))
        self.assertEqual(result["acceptance"], "not_established")
        # A future host/writer event registry must reject conflicting event reuse.
        self.assertEqual(result["event_id"], first["event_id"])

    def test_optional_dependency_failure_is_explicit(self):
        import builtins
        original = builtins.__import__

        def without_crypto(name, *args, **kwargs):
            if name.startswith("cryptography"):
                raise ImportError("unavailable")
            return original(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=without_crypto):
            self.assert_error("receipt_verifier_unavailable", self.verify)
            self.assertEqual(inspect_knowledge(self.root)["summary"]["revisions"], 1)

    def test_unsupported_backend_has_no_verified_result(self):
        from cryptography.exceptions import UnsupportedAlgorithm
        with patch("cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey.from_public_bytes",
                   side_effect=UnsupportedAlgorithm("unsupported")):
            self.assert_error("receipt_verifier_unavailable", self.verify)

    def test_fictional_host_demo_uses_real_cli_without_changing_fixture(self):
        tool = Path(__file__).resolve().parents[1]
        root = tool / "examples/fixtures/knowledge-project"
        before = {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}
        process = subprocess.run([sys.executable, "-B", str(tool / "examples/verify_host_receipt.py")],
                                 cwd=tool, capture_output=True, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        output = json.loads(process.stdout)
        self.assertEqual(output["approval_source"], "scripted_fictional_event")
        self.assertEqual(output["valid_receipt"]["verification"], "verified_under_pinned_policy")
        self.assertEqual(output["valid_receipt"]["acceptance"], "not_established")
        self.assertEqual(output["tampered_signature"], "invalid_receipt_signature")
        self.assertEqual(output["real_user_integration"], "not_demonstrated")
        self.assertFalse(output["private_key_persisted"])
        self.assertEqual(before, {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()})

    def test_project_cli_preserves_source_and_default_unverified_view(self):
        before = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        arguments = [sys.executable, "-B", "-m", "universal_ir", "verify-receipt", str(self.root), self.record["record_id"],
                     "--receipt", str(self.proof_path), "--policy", str(self.policy_path), "--policy-id", identity(self.policy)]
        process = subprocess.run(arguments, capture_output=True, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["format"], FORMAT)
        self.assertFalse(result["observation"]["atomic"])
        self.assertEqual(before, {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob("*") if path.is_file()})
        self.assertEqual(inspect_knowledge(self.root)["records"]["entries"][0]["attribution"], "unverified_attribution")

    def test_matching_receipt_does_not_prove_implementation_or_current_evidence(self):
        source = self.root / "code.py"
        source.write_bytes(b"original\n")
        body = copy.deepcopy(self.body)
        body["evidence"] = [{"kind": "file", "path": "code.py", "content_id": "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()}]
        self.record = self.make_record(body)
        self.store_record(self.record)
        self.receipt = self.sign(self.record)
        self.save_inputs()
        source.write_bytes(b"different\n")
        result = self.project_verify()
        self.assertEqual(result["verification"], "verified_under_pinned_policy")
        self.assertEqual(result["observation"]["record_evidence"], "changed")
        self.assertEqual(result["acceptance"], "not_established")

    def test_repository_controlled_host_inputs_are_rejected(self):
        for selected in ("policy", "receipt"):
            inside = self.root / (selected + ".json")
            inside.write_bytes(canonical(self.policy if selected == "policy" else self.receipt) + b"\n")
            if selected == "policy":
                self.policy_path = inside
            else:
                self.proof_path = inside
            self.assert_error("invalid_host_input", self.project_verify)
            self.proof_path, self.policy_path = self.base / "receipt.json", self.base / "policy.json"

    def test_input_size_directory_missing_file_and_malformed_json(self):
        self.policy_path.write_bytes(b" " * (1024 * 1024 + 1))
        self.assert_error("invalid_host_input", self.project_verify)
        for data in (b'{"format":1,"format":2}\n', b'{"bad":NaN}\n', b"\xff\n"):
            self.policy_path.write_bytes(data)
            self.assert_error("invalid_trust_policy", self.project_verify)
        self.policy_path = self.base
        self.assert_error("invalid_host_input", self.project_verify)
        self.policy_path = self.base / "missing.json"
        self.assert_error("invalid_host_input", self.project_verify)

    def test_unknown_and_ignored_records_do_not_gain_attribution(self):
        wanted = self.record["record_id"]
        self.record = dict(self.record, record_id="sha256:" + "0" * 64)
        self.assert_error("unknown_knowledge", self.project_verify)
        self.record["record_id"] = wanted
        (self.root / ".gitignore").write_bytes(b".uir/knowledge/\n")
        self.assert_error("unknown_knowledge", self.project_verify)

    def test_external_input_reconciliation_and_repeated_edits_fail_closed(self):
        from universal_ir import receipts
        read = receipts._external_bytes
        calls = 0

        def once(path, root):
            nonlocal calls
            data = read(path, root)
            calls += 1
            if calls == 2:
                self.policy_path.write_bytes(self.policy_path.read_bytes() + b" ")
            return data

        with patch("universal_ir.receipts._external_bytes", side_effect=once):
            self.assertEqual(self.project_verify()["verification"], "verified_under_pinned_policy")
        self.assertGreater(calls, 4)

        def always(path, root):
            data = read(path, root)
            self.policy_path.write_bytes(self.policy_path.read_bytes() + b" ")
            return data

        with patch("universal_ir.receipts._external_bytes", side_effect=always):
            self.assert_error("unstable_inputs", self.project_verify)

    def test_host_input_symlinks_rejected(self):
        link = self.base / "linked.json"
        try:
            link.symlink_to(self.policy_path)
        except OSError:
            self.skipTest("Creating symlinks is unavailable.")
        self.policy_path = link
        self.assert_error("invalid_host_input", self.project_verify)

    def test_host_input_disappearing_between_hash_and_open_reconciles(self):
        original = os.open
        calls = 0

        def disappears(path, *args, **kwargs):
            nonlocal calls
            if Path(path) == self.policy_path:
                calls += 1
                if calls == 2:
                    raise FileNotFoundError("replaced during open")
            return original(path, *args, **kwargs)

        with patch("universal_ir.receipts.os.open", side_effect=disappears):
            self.assertEqual(self.project_verify()["verification"], "verified_under_pinned_policy")
        self.assertGreater(calls, 2)

    def test_source_changes_between_inspections_reconcile_before_report(self):
        actual = inspect_knowledge
        calls = 0

        def changes(root, **kwargs):
            nonlocal calls
            view = actual(root, **kwargs)
            calls += 1
            if calls == 1:
                (self.root / "new.py").write_bytes(b"new input\n")
            return view

        with patch("universal_ir.receipts.inspect_knowledge", side_effect=changes):
            output = self.project_verify()
        self.assertGreater(calls, 2)
        self.assertEqual(output["observation"]["snapshot"], actual(self.root)["snapshot"])

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_host_input_junctions_rejected(self):
        folder = self.base / "host"
        folder.mkdir()
        actual = folder / "policy.json"
        actual.write_bytes(canonical(self.policy) + b"\n")
        link = self.base / "junction"
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(folder)], capture_output=True, check=True)
        self.policy_path = link / "policy.json"
        self.assert_error("invalid_host_input", self.project_verify)

    def test_cli_errors_have_no_success_output(self):
        self.receipt = self.rehash(dict(self.receipt, signature="00" * 64))
        self.save_inputs()
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(["verify-receipt", str(self.root), self.record["record_id"], "--receipt", str(self.proof_path),
                           "--policy", str(self.policy_path), "--policy-id", identity(self.policy)])
        self.assertEqual(status, 2)
        self.assertEqual(stdout.getvalue(), "")
        output = json.loads(stderr.getvalue())
        self.assertEqual(output["format"], FORMAT)
        self.assertEqual(output["error"]["code"], "invalid_receipt_signature")


if __name__ == "__main__":
    unittest.main()
