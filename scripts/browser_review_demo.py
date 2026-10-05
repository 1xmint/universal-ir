"""Ephemeral loopback development host, not an isolated approval authority."""

import argparse
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import secrets
import sys
from threading import Lock
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from universal_ir.inventory import InventoryError, canonical, parse_json
from universal_ir.preparation import prepare_knowledge
from universal_ir.receipts import _digest, _fail, _shape, _text
from universal_ir.webauthn_registration import WebAuthnRegistration
from universal_ir.webauthn_review import WebAuthnReview, _origin, _path


ASSETS = Path(__file__).resolve().parents[1] / "examples/browser-review"


class ReviewSession:
    def __init__(self, *, root, candidate_path, preparation_id, project_id, host_id, actor_id, event_id, origin, clock=None):
        _digest(preparation_id, "invalid_review_configuration")
        _origin("localhost", origin)
        for value in (project_id, host_id, actor_id, event_id):
            _text(value, "invalid_review_configuration")
        if clock is not None and not callable(clock):
            _fail("invalid_review_configuration", "Host clock must be callable.")
        self._settings = dict(root=_path(root), candidate_path=_path(candidate_path), preparation_id=preparation_id,
                              project_id=project_id, host_id=host_id, actor_id=actor_id, event_id=event_id,
                              rp_id="localhost", origin=origin, clock=clock)
        prepared = self._current()
        if prepared["candidate"]["record"]["body"]["origin"] != {
            "kind": "developer_statement", "host_id": host_id, "actor_id": actor_id, "event_id": event_id
        }:
            _fail("review_subject_mismatch", "Operator-selected actor/event differs from the candidate.")
        self.token = secrets.token_urlsafe(32)
        self._deadline = time.monotonic() + 600
        self._stage = "new"
        self._registration = self._review = self._credential = None
        self._lock = Lock()

    def _current(self):
        settings = self._settings
        prepared = prepare_knowledge(settings["root"], settings["candidate_path"])
        if prepared["project_id"] != settings["project_id"]:
            _fail("host_project_mismatch", "Project differs from operator configuration.")
        if prepared["preparation_id"] != settings["preparation_id"]:
            _fail("stale_preparation", "Review changed; restart against a newly selected preparation.")
        return prepared

    def dispatch(self, path, raw):
        with self._lock:
            if time.monotonic() >= self._deadline:
                _fail("session_expired", "Temporary session expired; restart the demo.")
            if self._stage in ("finished", "cancelled"):
                _fail("ceremony_finished", "Temporary ceremony is closed.")
            if path not in {"/session", "/register/options", "/register/complete", "/review/options", "/review/complete", "/cancel"}:
                _fail("unknown_operation", "Unknown operation.")
            if path not in {"/register/complete", "/review/complete"}:
                try:
                    _shape(parse_json(raw), "", "invalid_tool_request")
                except (ValueError, UnicodeError):
                    _fail("invalid_tool_request", "Operation requires an empty JSON object.")
            if path == "/cancel":
                self._stage = "cancelled"
                self._registration = self._review = self._credential = None
                return self._result({"status": "cancelled", "writes": False})
            prepared = self._current()
            if path == "/session":
                return self._result({"stage": self._stage, "review": prepared, "acceptance": "not_established"})
            settings = self._settings
            if path == "/register/options" and self._stage in ("new", "enrolling"):
                self._registration = WebAuthnRegistration(**{key: settings[key] for key in ("host_id", "actor_id", "rp_id", "origin", "clock")})
                self._stage = "enrolling"
                return self._result(self._registration.options())
            if path == "/register/complete" and self._stage == "enrolling":
                result = self._registration.complete(raw)
                self._current()
                self._credential = deepcopy(result["credential"])
                self._stage = "enrolled"
                return self._result({"status": "registered_for_demo", "actor_authentication": "not_established", "persistence": "none"})
            if path == "/review/options" and self._stage in ("enrolled", "reviewing"):
                self._review = WebAuthnReview(**settings, credential=self._credential)
                self._stage = "reviewing"
                return self._result(self._review.options())
            if path == "/review/complete" and self._stage == "reviewing":
                result = self._review.verify(raw)
                self._stage = "finished"
                self._registration = self._review = self._credential = None
                return self._result(result)
            _fail("invalid_ceremony_stage", "Operation is not available in the current stage.")

    def _result(self, result):
        if time.monotonic() >= self._deadline:
            _fail("session_expired", "Temporary session expired during the operation.")
        return result


def handler(session, origin):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def setup(self):
            super().setup()
            self.connection.settimeout(3)

        def log_message(self, *args):
            pass  # Do not log the session capability, proposal, credential, or assertion.

        def send_error(self, status, message=None, explain=None):
            self._error(status, "unsupported_http_request")

        def _headers(self, status, content_type, data):
            self.send_response(status)
            for name, value in {
                "Content-Type": content_type, "Content-Length": str(len(data)), "Cache-Control": "no-store",
                "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
                "X-Frame-Options": "DENY", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
                "Permissions-Policy": "publickey-credentials-create=(self), publickey-credentials-get=(self)",
            }.items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(data)

        def _error(self, status, code):
            self._headers(status, "application/json", canonical({"status": "error", "error": {"code": code}}))

        def _host(self):
            return self.client_address[0] == "127.0.0.1" and self.headers.get_all("Host") == [origin.removeprefix("http://")]

        def do_GET(self):
            if not self._host():
                return self._error(403, "invalid_browser_origin")
            assets = {"/": ("index.html", "text/html; charset=utf-8"), "/review.js": ("review.js", "text/javascript; charset=utf-8"),
                      "/style.css": ("style.css", "text/css; charset=utf-8")}
            if self.path not in assets:
                return self._error(404, "unknown_operation")
            name, content_type = assets[self.path]
            self._headers(200, content_type, (ASSETS / name).read_bytes())

        def do_POST(self):
            if not self._host() or self.headers.get_all("Origin") != [origin]:
                return self._error(403, "invalid_browser_origin")
            authorization = self.headers.get_all("Authorization")
            if authorization is None or len(authorization) != 1 or not secrets.compare_digest(authorization[0].encode(), ("Bearer " + session.token).encode()):
                return self._error(403, "invalid_session_capability")
            lengths = self.headers.get_all("Content-Length")
            if self.headers.get("Transfer-Encoding") is not None or lengths is None or len(lengths) != 1 or not 1 <= len(lengths[0]) <= 5 or not lengths[0].isascii() or not lengths[0].isdigit() or not 0 < int(lengths[0]) <= 16 * 1024:
                return self._error(400, "invalid_request_size")
            if self.headers.get_all("Content-Type") != ["application/json"]:
                return self._error(400, "invalid_content_type")
            self.connection.settimeout(3)
            try:
                raw = self.rfile.read(int(lengths[0]))
                if len(raw) != int(lengths[0]):
                    return self._error(400, "invalid_request_size")
                result = session.dispatch(self.path, raw)
            except InventoryError as error:
                return self._error(409, error.code)
            except (TimeoutError, OSError):
                return self._error(400, "incomplete_request")
            self._headers(200, "application/json", canonical(result))
    return Handler


def serve(arguments=None):
    parser = argparse.ArgumentParser(description="Temporary browser ceremony demo; no isolated authority or knowledge writes.")
    for name in ("root", "candidate-path", "preparation-id", "project-id", "host-id", "actor-id", "event-id"):
        parser.add_argument("--" + name, required=True)
    args = vars(parser.parse_args(arguments))
    server = HTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    try:
        origin = "http://localhost:" + str(server.server_port)
        session = ReviewSession(**args, origin=origin)
        server.RequestHandlerClass = handler(session, origin)
        print("Development demo only. Keep the capability URL private; unrestricted local agents can defeat this boundary.", flush=True)
        print(origin + "/#" + session.token, flush=True)
        print("Expires in ten minutes. Ctrl+C stops the server. Nothing is accepted or written.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
