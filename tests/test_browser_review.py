"""Software-credential registration and real loopback transport checks."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from fido2 import cbor
from fido2.cose import ES256
from fido2.webauthn import AttestedCredentialData, AuthenticatorData

from scripts.browser_review_demo import ReviewSession, handler
from universal_ir.inventory import InventoryError, canonical, identity, parse_json
from universal_ir.preparation import prepare_knowledge
from universal_ir.webauthn_registration import WebAuthnRegistration
from universal_ir.webauthn_review import encode


class BrowserReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="uir-browser-test-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "project"
        config = self.root / ".uir/config"
        config.mkdir(parents=True)
        (config / "project.json").write_bytes(canonical({"version": 1, "project_id": "sample", "exclude": [], "documents": []}) + b"\n")
        self.source = self.root / "README.md"
        self.source.write_bytes(b"# Project\nKeep tenants apart.\n")
        unsigned = {"format": "uir.knowledge.v1", "project_id": "sample", "body": {
            "id": "isolation", "category": "requirement", "text": "Keep tenants apart. <script>untrusted()</script>", "scope": ["."],
            "origin": {"kind": "developer_statement", "host_id": "test-host", "actor_id": "test-alice", "event_id": "test-event"},
            "input_id": None, "evidence": [], "supersedes": [], "state": "active"}}
        self.record = dict(unsigned, record_id=identity(unsigned))
        self.candidate = self.base / "candidate.json"
        self.candidate.write_bytes(canonical(self.record) + b"\n")
        self.prepared = prepare_knowledge(self.root, self.candidate)
        self.now = datetime.now(timezone.utc)
        self.origin = "http://localhost:8765"
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = b"fictional-test-credential"

    def registration(self):
        return WebAuthnRegistration(host_id="test-host", actor_id="test-alice", rp_id="localhost", origin=self.origin, clock=lambda: self.now)

    def registration_response(self, options, *, flags=69, rp_id="localhost", client_updates=None, attestation_updates=None, key_updates=None):
        client = dict(type="webauthn.create", challenge=options["options"]["publicKey"]["challenge"], origin=self.origin, crossOrigin=False)
        client.update(client_updates or {})
        public_key = ES256.from_cryptography_key(self.key.public_key())
        public_key.update(key_updates or {})
        registered = AttestedCredentialData.create(b"\x00" * 16, self.credential_id, public_key)
        auth = hashlib.sha256(rp_id.encode()).digest() + bytes([flags]) + b"\x00" * 4 + registered
        attestation = dict(fmt="none", attStmt={}, authData=bytes(auth))
        attestation.update(attestation_updates or {})
        return canonical({"id": encode(self.credential_id), "rawId": encode(self.credential_id), "type": "public-key", "response": {
            "clientDataJSON": encode(canonical(client)), "attestationObject": encode(cbor.encode(attestation))}})

    def assertion(self, options):
        client = canonical(dict(type="webauthn.get", challenge=options["options"]["publicKey"]["challenge"], origin=self.origin, crossOrigin=False))
        auth = hashlib.sha256(b"localhost").digest() + bytes([5]) + (1).to_bytes(4, "big")
        signature = self.key.sign(auth + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
        return canonical({"id": encode(self.credential_id), "rawId": encode(self.credential_id), "type": "public-key", "response": {
            "clientDataJSON": encode(client), "authenticatorData": encode(auth), "signature": encode(signature), "userHandle": None}})

    def error(self, code, call):
        with self.assertRaises(InventoryError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def session(self, **updates):
        settings = dict(root=self.root, candidate_path=self.candidate, preparation_id=self.prepared["preparation_id"], project_id="sample",
                        host_id="test-host", actor_id="test-alice", event_id="test-event", origin=self.origin, clock=lambda: self.now)
        settings.update(updates)
        return ReviewSession(**settings)

    def server(self):
        server = HTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
        self.origin = "http://localhost:" + str(server.server_port)
        session = self.session()
        server.RequestHandlerClass = handler(session, self.origin)
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        thread.start()
        def stop():
            server.shutdown()
            server.server_close()
            thread.join(2)
        self.addCleanup(stop)
        def request(path, body=b"{}", *, method="POST", updates=None):
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            headers = {"Host": self.origin.removeprefix("http://"), "Origin": self.origin, "Authorization": "Bearer " + session.token, "Content-Type": "application/json"}
            headers.update(updates or {})
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            result = (response.status, dict(response.getheaders()), response.read())
            connection.close()
            return result
        return session, request

    def test_registration_context_and_one_time_completion(self):
        registration = self.registration()
        options = registration.options()
        self.assertEqual(options["options"]["publicKey"]["pubKeyCredParams"], [{"type": "public-key", "alg": -7}])
        self.assertEqual(options["options"]["publicKey"]["attestation"], "none")
        raw = self.registration_response(options)
        result = registration.complete(raw)
        self.assertEqual(result["credential"]["id"], encode(self.credential_id))
        self.assertEqual(result["actor_authentication"], "not_established")
        self.assertEqual(result["device_attestation"], "not_requested")
        self.error("registration_used", lambda: registration.complete(raw))
        self.error("registration_used", registration.options)

    def test_registration_rejects_context_flags_and_attestation_substitution(self):
        registration = self.registration()
        options = registration.options()
        changes = ({"rp_id": "evil.test"}, {"flags": 65}, {"flags": 68}, {"flags": 69 | 2}, {"flags": 69 | 16},
                   {"client_updates": {"challenge": encode(b"x" * 32)}}, {"client_updates": {"origin": "https://evil.test"}},
                   {"client_updates": {"crossOrigin": True}}, {"client_updates": {"topOrigin": "https://evil.test"}},
                   {"attestation_updates": {"fmt": "packed"}}, {"attestation_updates": {"attStmt": {"alg": -7}}},
                   {"attestation_updates": {"authData": b"\x00" * 37}})
        for change in changes:
            with self.subTest(change=change):
                self.error("invalid_webauthn_registration", lambda: registration.complete(self.registration_response(options, **change)))
        self.assertEqual(registration.complete(self.registration_response(options))["status"], "ok")

    def test_registration_rejects_malformed_identity_json_and_bytes(self):
        registration = self.registration()
        raw = self.registration_response(registration.options())
        obj = parse_json(raw)
        for value in (b"\xff", b"[]", raw[:-1] + b',"type":"public-key"}', b"x" * 16385, "{}"):
            self.error("invalid_webauthn_registration", lambda: registration.complete(value))
        for fields in ({"id": encode(b"other")}, {"id": encode(b"other"), "rawId": encode(b"other")}, {"actor_id": "mallory"}, {"clientExtensionResults": {"credProps": {}}}):
            value = dict(obj, **fields)
            self.error("invalid_webauthn_registration", lambda: registration.complete(canonical(value)))
        for value in ("a", "===", encode(b"\x00" * 80)):
            bad = deepcopy(obj)
            bad["response"]["attestationObject"] = value
            self.error("invalid_webauthn_registration", lambda: registration.complete(canonical(bad)))

    def test_registration_nonce_expiry_and_option_copies(self):
        first, second = self.registration(), self.registration()
        original = first.options()
        self.assertNotEqual(original["request_id"], second.options()["request_id"])
        self.error("invalid_webauthn_registration", lambda: second.complete(self.registration_response(original)))
        modified = first.options()
        modified["options"]["publicKey"]["challenge"] = "changed"
        self.assertEqual(first.options(), original)
        raw = self.registration_response(original)
        self.now += timedelta(seconds=120)
        self.error("review_expired", lambda: first.complete(raw))

    def test_registration_completion_is_serialized(self):
        registration = self.registration()
        raw = self.registration_response(registration.options())
        def attempt():
            try:
                return registration.complete(raw)["status"]
            except InventoryError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(lambda _: attempt(), range(2))), ["ok", "registration_used"])

    def test_registration_rejects_other_algorithms_invalid_points_and_key_fields(self):
        registration = self.registration()
        options = registration.options()
        for update in ({3: -8}, {-1: 2}, {7: b"unsupported"}, {-2: b"\x00" * 32, -3: b"\x00" * 32}, {-2: b"short"}):
            self.error("invalid_webauthn_registration", lambda: registration.complete(self.registration_response(options, key_updates=update)))

    def test_registration_expiry_after_library_validation_does_not_complete(self):
        registration = self.registration()
        raw = self.registration_response(registration.options())
        complete = registration._server.register_complete
        def expire(*args):
            result = complete(*args)
            self.now += timedelta(seconds=120)
            return result
        with patch.object(registration._server, "register_complete", side_effect=expire):
            self.error("review_expired", lambda: registration.complete(raw))

    def test_http_registration_review_verification_preserves_files_and_closes(self):
        session, request = self.server()
        before = {p.relative_to(self.base): p.read_bytes() for p in self.base.rglob("*") if p.is_file()}
        status, headers, raw = request("/session")
        self.assertEqual(status, 200)
        self.assertEqual(parse_json(raw)["review"]["candidate"]["record"], self.record)
        options = parse_json(request("/register/options")[2])
        self.assertEqual(request("/register/complete", self.registration_response(options))[0], 200)
        review = parse_json(request("/review/options")[2])
        proof = self.assertion(review)
        status, _, raw = request("/review/complete", proof)
        result = parse_json(raw)
        self.assertEqual(status, 200)
        self.assertEqual(result["preparation"]["preparation_id"], self.prepared["preparation_id"])
        self.assertEqual(result["authority"]["human_event_authentication"], "not_established")
        self.assertFalse(result["authority"]["writes"])
        self.assertEqual(parse_json(request("/review/complete", proof)[2])["error"]["code"], "ceremony_finished")
        self.assertEqual(before, {p.relative_to(self.base): p.read_bytes() for p in self.base.rglob("*") if p.is_file()})

    def test_http_origin_host_token_content_type_and_size_rejection(self):
        _, request = self.server()
        for updates in ({"Host": "evil.test"}, {"Origin": "http://localhost:9999"}, {"Authorization": "Bearer bad"}):
            self.assertEqual(request("/session", updates=updates)[0], 403)
        for updates in ({"Content-Type": "text/plain"}, {"Content-Length": "0"}, {"Content-Length": "9" * 5000}, {"Transfer-Encoding": "chunked"}):
            self.assertEqual(request("/session", body=b"", updates=updates)[0], 400)
        self.assertEqual(request("/session", body=b"", updates={"Content-Length": "16385"})[0], 400)
        self.assertEqual(request("/session", canonical({"root": "another"}))[0], 409)
        self.assertEqual(request("/unknown")[0], 409)

    def test_public_assets_have_browser_boundaries_and_no_project_data(self):
        _, request = self.server()
        for path in ("/", "/review.js", "/style.css"):
            status, headers, raw = request(path, method="GET")
            self.assertEqual(status, 200)
            self.assertEqual(headers["Cache-Control"], "no-store")
            self.assertEqual(headers["X-Frame-Options"], "DENY")
            self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
            self.assertNotIn(self.record["body"]["text"].encode(), raw)
            self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(request("/../LICENSE", method="GET")[0], 404)
        self.assertEqual(request("/", method="GET", updates={"Host": "127.0.0.1"})[0], 403)

    def test_cancel_stage_and_session_expiry(self):
        session = self.session()
        self.error("invalid_ceremony_stage", lambda: session.dispatch("/review/options", b"{}"))
        self.assertEqual(session.dispatch("/cancel", b"{}")["status"], "cancelled")
        self.error("ceremony_finished", lambda: session.dispatch("/session", b"{}"))
        session = self.session()
        with patch("scripts.browser_review_demo.time.monotonic", return_value=session._deadline):
            self.error("session_expired", lambda: session.dispatch("/session", b"{}"))

    def test_stale_source_and_operator_substitution_rejected(self):
        self.error("review_subject_mismatch", lambda: self.session(actor_id="mallory"))
        session = self.session()
        session.dispatch("/register/options", b"{}")
        self.source.write_bytes(b"changed manually\n")
        self.error("stale_preparation", lambda: session.dispatch("/session", b"{}"))
        self.error("stale_preparation", lambda: session.dispatch("/register/options", b"{}"))
        self.assertEqual(session.dispatch("/cancel", b"{}")["status"], "cancelled")

    def test_session_expiry_during_read_does_not_return_a_review(self):
        session = self.session()
        with patch("scripts.browser_review_demo.time.monotonic", side_effect=[session._deadline - 1, session._deadline]):
            self.error("session_expired", lambda: session.dispatch("/session", b"{}"))

    def test_duplicate_http_authority_headers_and_unsupported_methods(self):
        session, request = self.server()
        port = int(self.origin.rsplit(":", 1)[1])
        for name in ("Host", "Origin", "Authorization", "Content-Length"):
            connection = HTTPConnection("127.0.0.1", port, timeout=5)
            connection.putrequest("POST", "/session", skip_host=True)
            headers = {"Host": self.origin.removeprefix("http://"), "Origin": self.origin, "Authorization": "Bearer " + session.token,
                       "Content-Type": "application/json", "Content-Length": "2"}
            for key, value in headers.items():
                connection.putheader(key, value)
                if key == name:
                    connection.putheader(key, value)
            connection.endheaders()
            response = connection.getresponse()
            self.assertIn(response.status, (400, 403))
            response.read()
            connection.close()
        status, headers, raw = request("/session", method="OPTIONS")
        self.assertEqual(status, 501)
        self.assertEqual(headers["Cache-Control"], "no-store")


if __name__ == "__main__":
    unittest.main()
