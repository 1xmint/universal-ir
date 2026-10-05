"""Real signatures from a software test credential; no real user ceremony."""

import builtins
from contextlib import chdir
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from universal_ir.inventory import ChangedDuringCapture, InventoryError, canonical, identity, parse_json
from universal_ir.knowledge import inspect_knowledge
from universal_ir.preparation import prepare_knowledge
from universal_ir.webauthn_review import DOMAIN, FORMAT, MAX_ASSERTION_BYTES, WebAuthnReview, encode


class WebAuthnReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="uir-webauthn-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.write(".uir/config/project.json", canonical({"version": 1, "project_id": "sample", "exclude": [], "documents": []}) + b"\n")
        self.write("README.md", "# Sample\nKeep tenants apart.\n")
        self.now = datetime.now(timezone.utc)
        self.body = {"id": "isolation", "category": "requirement", "text": "Keep tenants apart.", "scope": ["."],
                     "origin": {"kind": "developer_statement", "host_id": "test-host", "actor_id": "test-alice", "event_id": "test-event"},
                     "input_id": None, "evidence": [], "supersedes": [], "state": "active"}
        self.candidate = self.base / "candidate.json"
        self.update_record()
        self.key = ec.generate_private_key(ec.SECP256R1())
        numbers = self.key.public_key().public_numbers()
        self.credential = {"id": encode(b"fictional-test-credential"), "public_key_x": encode(numbers.x.to_bytes(32, "big")),
                           "public_key_y": encode(numbers.y.to_bytes(32, "big")), "user_handle": encode(b"fictional-alice"), "sign_count": 0}
        self.host = self.make_host()

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode() if isinstance(value, str) else value)
        return path

    def update_record(self):
        unsigned = {"format": "uir.knowledge.v1", "project_id": "sample", "body": self.body}
        self.record = dict(unsigned, record_id=identity(unsigned))
        self.candidate.write_bytes(canonical(self.record) + b"\n")
        self.prepared = prepare_knowledge(self.root, self.candidate)

    def make_host(self, **updates):
        parameters = dict(root=self.root, candidate_path=self.candidate, preparation_id=self.prepared["preparation_id"],
                          project_id="sample", host_id="test-host", actor_id="test-alice", event_id="test-event",
                          rp_id="localhost", origin="http://localhost:8765", credential=self.credential, clock=lambda: self.now)
        parameters.update(updates)
        return WebAuthnReview(**parameters)

    def assertion(self, *, host=None, key=None, client_updates=None, client_bytes=None, flags=5, counter=0,
                  rp_id="localhost", user_handle="default", response_updates=None):
        options = (host or self.host).options()["options"]["publicKey"]
        client = dict(type="webauthn.get", challenge=options["challenge"], origin="http://localhost:8765", crossOrigin=False)
        client.update(client_updates or {})
        raw = client_bytes if client_bytes is not None else canonical(client)
        auth = hashlib.sha256(rp_id.encode()).digest() + bytes([flags]) + counter.to_bytes(4, "big")
        signature = (key or self.key).sign(auth + hashlib.sha256(raw).digest(), ec.ECDSA(hashes.SHA256()))
        response = {"id": self.credential["id"], "rawId": self.credential["id"], "type": "public-key",
                    "response": {"clientDataJSON": encode(raw), "authenticatorData": encode(auth), "signature": encode(signature),
                                 "userHandle": self.credential["user_handle"] if user_handle == "default" else user_handle},
                    "clientExtensionResults": {}}
        response.update(response_updates or {})
        return canonical(response)

    def error(self, code, call):
        with self.assertRaises(InventoryError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def test_exact_signed_assertion_and_options_preserve_all_files(self):
        before = {p.relative_to(self.base): p.read_bytes() for p in self.base.rglob("*") if p.is_file()}
        options = self.host.options()
        self.assertEqual(options["review"]["candidate"]["record"], self.record)
        self.assertEqual(options["options"]["publicKey"]["userVerification"], "required")
        self.assertEqual(options["options"]["publicKey"]["allowCredentials"], [{"type": "public-key", "id": self.credential["id"]}])
        result = self.host.verify(self.assertion())
        self.assertEqual(result["format"], FORMAT)
        self.assertEqual(result["request_id"], options["request_id"])
        self.assertEqual(result["request"]["preparation_id"], self.prepared["preparation_id"])
        self.assertEqual(result["verification"], "verified_under_host_configured_credential")
        self.assertTrue(result["authenticator"]["user_verification"])
        self.assertEqual(result["authority"]["human_event_authentication"], "not_established")
        self.assertEqual(result["authority"]["replay"], "not_checked")
        self.assertFalse(result["authority"]["writes"])
        self.assertEqual(inspect_knowledge(self.root)["records"]["total"], 0)
        self.assertEqual(before, {p.relative_to(self.base): p.read_bytes() for p in self.base.rglob("*") if p.is_file()})

    def test_wrong_signing_key_and_tampered_signature(self):
        self.error("invalid_webauthn_assertion", lambda: self.host.verify(self.assertion(key=ec.generate_private_key(ec.SECP256R1()))))
        response = parse_json(self.assertion())
        response["response"]["signature"] = encode(b"\x00" * 70)
        self.error("invalid_webauthn_assertion", lambda: self.host.verify(canonical(response)))

    def test_wrong_rp_origin_challenge_and_operation(self):
        for options in ({"rp_id": "evil.test"}, {"client_updates": {"origin": "http://localhost:9999"}},
                        {"client_updates": {"challenge": encode(b"x" * 32)}}, {"client_updates": {"type": "webauthn.create"}}):
            with self.subTest(options=options):
                self.error("invalid_webauthn_assertion", lambda: self.host.verify(self.assertion(**options)))

    def test_presence_and_verification_must_be_signed(self):
        for flags in (0, 1, 4):
            with self.subTest(flags=flags):
                self.error("invalid_webauthn_assertion", lambda: self.host.verify(self.assertion(flags=flags)))
        response = parse_json(self.assertion(flags=1))
        auth = hashlib.sha256(b"localhost").digest() + bytes([5]) + b"\x00" * 4
        response["response"]["authenticatorData"] = encode(auth)
        self.error("invalid_webauthn_assertion", lambda: self.host.verify(canonical(response)))

    def test_cross_origin_top_origin_extensions_and_extra_fields_rejected(self):
        for changes in ({"crossOrigin": True}, {"crossOrigin": 0}, {"topOrigin": "https://evil.test"}, {"tokenBinding": {}}):
            self.error("invalid_webauthn_assertion", lambda: self.host.verify(self.assertion(client_updates=changes)))
        for changes in ({"clientExtensionResults": {"appid": True}}, {"actor_id": "test-alice"},
                        {"authenticatorAttachment": "invented"}, {"type": "other"}):
            self.error("invalid_webauthn_assertion", lambda: self.host.verify(self.assertion(response_updates=changes)))

    def test_credential_and_user_handle_must_match_host_selection(self):
        for changes in ({"id": encode(b"different")}, {"rawId": encode(b"different")},
                        {"id": encode(b"different"), "rawId": encode(b"different")}):
            self.error("invalid_webauthn_assertion", lambda: self.host.verify(self.assertion(response_updates=changes)))
        self.error("invalid_webauthn_assertion", lambda: self.host.verify(self.assertion(user_handle=encode(b"mallory"))))
        self.assertEqual(self.host.verify(self.assertion(user_handle=None))["status"], "ok")

    def test_new_review_nonce_and_configuration_cannot_reuse_assertion(self):
        proof = self.assertion()
        other = self.make_host()
        self.assertNotEqual(self.host.options()["request_id"], other.options()["request_id"])
        self.error("invalid_webauthn_assertion", lambda: other.verify(proof))

    def test_challenge_binds_request_and_configuration_even_with_identical_nonce(self):
        with patch("universal_ir.webauthn_review.os.urandom", return_value=b"n" * 32):
            first = self.make_host()
            second = self.make_host(credential=dict(self.credential, sign_count=1))
        one, two = first.options(), second.options()
        self.assertEqual(one["request"]["nonce"], two["request"]["nonce"])
        self.assertNotEqual(one["request"]["configuration_id"], two["request"]["configuration_id"])
        self.assertNotEqual(one["options"]["publicKey"]["challenge"], two["options"]["publicKey"]["challenge"])
        self.assertEqual(one["options"]["publicKey"]["challenge"], encode(hashlib.sha256(DOMAIN + canonical(one["request"])).digest()))
        self.assertEqual(one["request_id"], identity(one["request"]))
        self.error("invalid_webauthn_assertion", lambda: second.verify(self.assertion(host=first, counter=2)))

    def test_relative_host_paths_stay_fixed_after_working_directory_change(self):
        with chdir(self.base):
            host = self.make_host(root="project", candidate_path="candidate.json")
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        with chdir(elsewhere):
            self.assertEqual(host.verify(self.assertion(host=host))["status"], "ok")

    def test_invalid_paths_and_falsey_callable_clock(self):
        for changes in ({"root": "bad\x00path"}, {"candidate_path": []}, {"candidate_path": "bad\ud800path"}):
            self.error("invalid_review_configuration", lambda: self.make_host(**changes))
        now = self.now
        class Clock:
            def __bool__(self):
                return False
            def __call__(self):
                return now
        host = self.make_host(clock=Clock())
        self.assertEqual(host.options()["request"]["issued_at"], now.isoformat())

    def test_options_and_constructor_dictionary_cannot_mutate_authority(self):
        proof = self.assertion()
        options = self.host.options()
        options["options"]["publicKey"]["challenge"] = encode(b"x" * 32)
        options["request"]["actor_id"] = "mallory"
        options["review"]["candidate"]["record"]["body"]["text"] = "Changed"
        self.credential["user_handle"] = encode(b"mallory")
        self.assertEqual(self.host.verify(proof)["request"]["actor_id"], "test-alice")
        self.assertEqual(self.host.options()["review"]["candidate"]["record"], self.record)

    def test_counter_conflict_and_zero_counter_support_do_not_consume_event(self):
        proof = self.assertion()
        self.host.verify(proof)
        self.assertEqual(self.host.verify(proof)["authority"]["replay"], "not_checked")
        host = self.make_host(credential=dict(self.credential, sign_count=7))
        for count in (0, 6, 7):
            self.error("credential_counter_conflict", lambda: host.verify(self.assertion(host=host, counter=count)))
        result = host.verify(self.assertion(host=host, counter=8))
        self.assertEqual(result["authenticator"]["sign_count"], 8)
        self.assertEqual(result["authenticator"]["previous_sign_count"], 7)
        self.assertEqual(self.credential["sign_count"], 0)

    def test_backup_flags_and_unsupported_authenticator_data(self):
        for flags in (5 | 16, 5 | 2, 5 | 32, 5 | 64, 5 | 128):
            self.error("invalid_webauthn_assertion", lambda: self.host.verify(self.assertion(flags=flags)))
        result = self.host.verify(self.assertion(flags=5 | 8 | 16))
        self.assertTrue(result["authenticator"]["backup_eligible"])
        self.assertTrue(result["authenticator"]["backed_up"])
        response = parse_json(self.assertion())
        response["response"]["authenticatorData"] += "AAAA"
        self.error("invalid_webauthn_assertion", lambda: self.host.verify(canonical(response)))

    def test_strict_json_duplicate_keys_byte_limits_and_base64(self):
        for raw in (b"{}", b"[]", b"null", b"\xff", b'{"x":NaN}', b"x" * (MAX_ASSERTION_BYTES + 1), "{}"):
            self.error("invalid_webauthn_assertion", lambda: self.host.verify(raw))
        response = self.assertion()
        duplicate = response[:-1] + b',"type":"public-key"}'
        self.error("invalid_webauthn_assertion", lambda: self.host.verify(duplicate))
        client = canonical({"type": "webauthn.get", "challenge": self.host.options()["options"]["publicKey"]["challenge"], "origin": "http://localhost:8765"})
        duplicate = client[:-1] + b',"type":"webauthn.get"}'
        self.error("invalid_webauthn_assertion", lambda: self.host.verify(self.assertion(client_bytes=duplicate)))
        for field in ("clientDataJSON", "authenticatorData", "signature", "userHandle"):
            for value in ("=", "a", "AB", "abcd=", 4, "x" * 12000):
                obj = parse_json(response)
                obj["response"][field] = value
                self.error("invalid_webauthn_assertion", lambda: self.host.verify(canonical(obj)))

    def test_host_configuration_rejects_substitutions_and_malformed_keys(self):
        for changes in ({"preparation_id": "invalid"}, {"event_id": ""}, {"clock": 3}, {"rp_id": "evil.test"},
                        {"origin": "http://localhost:8765/path"}, {"origin": "http://user@localhost:8765"},
                        {"origin": "http://localhost:080"}, {"origin": "http://localhost:80"},
                        {"origin": "http://localhost:0"}, {"rp_id": "127.0.0.1", "origin": "http://127.0.0.1"},
                        {"rp_id": "Localhost"}, {"origin": "https://localhost:443"},
                        {"credential": dict(self.credential, sign_count=True)}, {"credential": dict(self.credential, sign_count=-1)},
                        {"credential": dict(self.credential, public_key_x=encode(b"\x00" * 32), public_key_y=encode(b"\x00" * 32))}):
            with self.subTest(changes=changes):
                self.error("invalid_review_configuration", lambda: self.make_host(**changes))
        for changes in ({"actor_id": "mallory"}, {"event_id": "other"}, {"host_id": "other"}):
            self.error("review_subject_mismatch", lambda: self.make_host(**changes))
        self.error("host_project_mismatch", lambda: self.make_host(project_id="other"))
        self.error("stale_preparation", lambda: self.make_host(preparation_id="sha256:" + "0" * 64))

    def test_https_origin_and_missing_cross_origin_field_supported(self):
        host = self.make_host(rp_id="review.example.test", origin="https://review.example.test")
        proof = self.assertion(host=host, rp_id="review.example.test", client_updates={"origin": "https://review.example.test"})
        self.assertEqual(host.verify(proof)["status"], "ok")
        client = {"type": "webauthn.get", "challenge": self.host.options()["options"]["publicKey"]["challenge"], "origin": "http://localhost:8765"}
        self.assertEqual(self.host.verify(self.assertion(client_bytes=canonical(client)))["status"], "ok")

    def test_expiry_rollback_unavailable_and_invalid_clock(self):
        proof = self.assertion()
        original = self.now
        for delta in (-1, 120, 121):
            self.now = original + timedelta(seconds=delta)
            self.error("review_expired", lambda: self.host.verify(proof))
            self.error("review_expired", self.host.options)
        self.now = original + timedelta(seconds=119)
        self.assertEqual(self.host.verify(proof)["status"], "ok")
        self.error("invalid_verification_time", lambda: self.make_host(clock=lambda: datetime.now()))
        def failing():
            raise RuntimeError("private clock detail")
        self.error("host_clock_unavailable", lambda: self.make_host(clock=failing))

    def test_expiry_during_verification_is_rejected(self):
        proof = self.assertion()
        complete = self.host._server.authenticate_complete
        def advance(*args):
            result = complete(*args)
            self.now += timedelta(seconds=120)
            return result
        with patch.object(self.host._server, "authenticate_complete", side_effect=advance):
            self.error("review_expired", lambda: self.host.verify(proof))

    def test_source_and_candidate_changes_invalidate_review(self):
        proof = self.assertion()
        self.write("new.py", "manual edit\n")
        self.error("stale_preparation", lambda: self.host.verify(proof))
        self.error("stale_preparation", self.host.options)
        (self.root / "new.py").unlink()
        self.body["text"] = "Different requirement."
        self.update_record()
        self.error("stale_preparation", lambda: self.host.verify(proof))

    def test_change_during_signature_verification_and_unstable_reads(self):
        proof = self.assertion()
        complete = self.host._server.authenticate_complete
        def mutate(*args):
            result = complete(*args)
            self.write("README.md", "manual edit\n")
            return result
        with patch.object(self.host._server, "authenticate_complete", side_effect=mutate):
            self.error("stale_preparation", lambda: self.host.verify(proof))
        self.write("README.md", "# Sample\nKeep tenants apart.\n")
        with patch("universal_ir.webauthn_review.prepare_knowledge", side_effect=ChangedDuringCapture):
            self.error("unstable_inputs", lambda: self.host.verify(proof))

    def test_candidate_transport_race_is_not_hidden_by_same_identity(self):
        proof = self.assertion()
        current = self.host._current
        def alternate():
            result = current()
            result["observation"]["candidate_content_id"] = str(alternate.calls % 2)
            alternate.calls += 1
            return result
        alternate.calls = 0
        with patch.object(self.host, "_current", side_effect=alternate):
            self.error("unstable_inputs", lambda: self.host.verify(proof))

    def test_dependency_import_is_lazy_and_missing_backend_is_explicit(self):
        original = builtins.__import__
        def without_optional(name, *args, **kwargs):
            if name.startswith("fido2"):
                raise ImportError("not installed")
            return original(name, *args, **kwargs)
        with patch("builtins.__import__", side_effect=without_optional):
            self.error("webauthn_unavailable", self.make_host)
        result = subprocess.run([sys.executable, "-S", "-c", "import universal_ir.webauthn_review; import universal_ir.__main__"],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_real_demonstration_script_reports_its_boundaries(self):
        process = subprocess.run([sys.executable, "-B", "scripts/demo_webauthn_review.py"],
                                 cwd=Path(__file__).resolve().parents[1], capture_output=True, check=True)
        result = parse_json(process.stdout)
        self.assertEqual(result["source_change_rejected"], "stale_preparation")
        self.assertTrue(result["verification_preserved_files"])
        self.assertFalse(result["real_user_demonstrated"])
        self.assertFalse(result["enrollment_demonstrated"])
        self.assertFalse(result["browser_ceremony_demonstrated"])
        self.assertEqual(result["model_calls"], 0)


if __name__ == "__main__":
    unittest.main()
