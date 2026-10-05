"""Host-configured WebAuthn assertion checks; no enrollment, UI, or acceptance."""

import base64
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from .inventory import ChangedDuringCapture, InventoryError, canonical, identity, parse_json
from .preparation import prepare_knowledge
from .receipts import _digest, _fail, _shape, _text


FORMAT = "uir.webauthn-review-verification.v1"
REQUEST = "uir.webauthn-review-request.v1"
DOMAIN = b"Universal IR WebAuthn review v1\x00"
MAX_ASSERTION_BYTES = 16 * 1024


def encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value, minimum, maximum, code):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value) or len(value) > (maximum * 4 + 2) // 3:
        _fail(code, "Expected bounded unpadded base64url bytes.")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except ValueError:
        _fail(code, "Invalid base64url encoding.")
    if not minimum <= len(decoded) <= maximum or encode(decoded) != value:
        _fail(code, "Noncanonical or unsupported byte encoding.")
    return decoded


def _backend():
    try:
        from fido2.cose import ES256
        from fido2.server import Fido2Server
        from fido2.webauthn import AttestedCredentialData, PublicKeyCredentialRpEntity, UserVerificationRequirement
        from cryptography.hazmat.primitives.asymmetric import ec
    except ImportError:
        _fail("webauthn_unavailable", "Install the optional hashed WebAuthn requirements in the host environment.")
    return ES256, Fido2Server, AttestedCredentialData, PublicKeyCredentialRpEntity, UserVerificationRequirement, ec


def _path(value):
    try:
        path = Path(os.path.abspath(value))
        str(path).encode("utf-8")
        if "\x00" in str(path):
            raise ValueError("NUL in host path")
        return path
    except (TypeError, ValueError, OSError):
        _fail("invalid_review_configuration", "Invalid host-selected path.")


def _origin(rp_id, origin):
    code = "invalid_review_configuration"
    if not isinstance(rp_id, str) or len(rp_id) > 253 or not all(
        re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in rp_id.split(".")
    ) or re.fullmatch(r"[0-9.]+", rp_id):
        _fail(code, "RP ID must be a lowercase DNS host name.")
    try:
        parts = urlsplit(origin)
        port = parts.port
        expected = parts.scheme + "://" + rp_id + (":" + str(port) if port is not None else "")
        if parts.hostname != rp_id or origin != expected or parts.scheme not in ("http", "https") or (parts.scheme == "http" and rp_id != "localhost"):
            raise ValueError("unsupported origin")
        if port == 0 or (parts.scheme, port) in (("https", 443), ("http", 80)):
            raise ValueError("noncanonical port")
    except (ValueError, TypeError, AttributeError):
        _fail(code, "Use an exact HTTPS origin, or HTTP localhost, with the same RP host and no path.")


class WebAuthnReview:
    """Internal host component. Construction is trusted; assertions are not.

    Configuration/enrollment and the review display must be protected by the host.
    Python object privacy provides no isolation from an unrestricted agent shell.
    """

    def __init__(self, *, root, candidate_path, preparation_id, project_id, host_id, actor_id,
                 event_id, rp_id, origin, credential, clock=None):
        code = "invalid_review_configuration"
        _digest(preparation_id, code)
        for value in (project_id, host_id, actor_id, event_id):
            _text(value, code)
        _origin(rp_id, origin)
        _shape(credential, "id public_key_x public_key_y user_handle sign_count", code)
        credential_id = _decode(credential["id"], 1, 1023, code)
        x = _decode(credential["public_key_x"], 32, 32, code)
        y = _decode(credential["public_key_y"], 32, 32, code)
        _decode(credential["user_handle"], 1, 64, code)
        count = credential["sign_count"]
        if type(count) is not int or not 0 <= count <= 0xffffffff:
            _fail(code, "Credential counter must be an unsigned 32-bit integer.")
        if clock is not None and not callable(clock):
            _fail(code, "Host clock must be callable.")
        ES256, Server, Registered, RP, UV, ec = _backend()
        try:
            public = ec.EllipticCurvePublicNumbers(int.from_bytes(x, "big"), int.from_bytes(y, "big"), ec.SECP256R1()).public_key()
        except ValueError:
            _fail(code, "Credential public key is not a P-256 curve point.")
        self._credential = deepcopy(credential)
        self._registered = Registered.create(b"\x00" * 16, credential_id, ES256.from_cryptography_key(public))
        self._server = Server(RP(id=rp_id, name="Universal IR review"), verify_origin=lambda actual: actual == origin)
        self._clock = clock if clock is not None else (lambda: datetime.now(timezone.utc))
        self._root, self._candidate = _path(root), _path(candidate_path)
        self._project, self._preparation = project_id, preparation_id
        self._origin = origin
        prepared = self._current()
        subject = prepared["candidate"]["record"]
        expected_origin = {"kind": "developer_statement", "host_id": host_id, "actor_id": actor_id, "event_id": event_id}
        if subject["body"]["origin"] != expected_origin:
            _fail("review_subject_mismatch", "Candidate origin differs from the host-selected developer event.")
        issued = self._now()
        self._expires = issued + timedelta(minutes=2)
        self._request = {"format": REQUEST, "project_id": project_id, "preparation_id": preparation_id,
                         "record_id": subject["record_id"], "host_id": host_id, "actor_id": actor_id,
                         "event_id": event_id, "action": "approved", "configuration_id": identity({
                             "rp_id": rp_id, "origin": origin, "credential": self._credential}),
                         "issued_at": issued.isoformat(), "expires_at": self._expires.isoformat(),
                         "nonce": encode(os.urandom(32))}
        self._issued = issued
        self._challenge = hashlib.sha256(DOMAIN + canonical(self._request)).digest()
        options, self._state = self._server.authenticate_begin([self._registered], user_verification=UV.REQUIRED, challenge=self._challenge)
        self._options = dict(options)
        # Timeout is a browser hint; the trusted clock enforces the actual interval.
        self._options["publicKey"]["timeout"] = 120000

    def _now(self):
        try:
            value = self._clock()
        except Exception:
            _fail("host_clock_unavailable", "Host clock is unavailable.")
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
            _fail("invalid_verification_time", "Host time must be aware UTC.")
        return value

    def _live(self):
        now = self._now()
        if not self._issued <= now < self._expires:
            _fail("review_expired", "Review is expired or host time precedes issuance.")
        return now

    def _current(self):
        prepared = prepare_knowledge(self._root, self._candidate)
        if prepared["project_id"] != self._project:
            _fail("host_project_mismatch", "Project differs from the host-selected project.")
        if prepared["preparation_id"] != self._preparation:
            _fail("stale_preparation", "Candidate or current review context differs from the host-selected preparation.")
        return prepared

    def options(self):
        """Browser transport uses base64url strings; the host must show the review."""
        self._live()
        prepared = self._current()
        self._live()
        return {"request_id": identity(self._request), "request": deepcopy(self._request),
                "review": prepared, "options": deepcopy(self._options)}

    def verify(self, assertion):
        """Read-only assertion verification, with current-source checks on both sides."""
        self._live()
        response, auth_data = self._response(assertion)
        for _ in range(3):
            try:
                before = self._current()
                try:
                    self._server.authenticate_complete(self._state, [self._registered], response)
                except (ValueError, KeyError, TypeError):
                    _fail("invalid_webauthn_assertion", "Assertion fails the fixed host credential, RP, origin, challenge, or signature checks.")
                counter = int.from_bytes(auth_data[33:37], "big")
                previous = self._credential["sign_count"]
                if (counter or previous) and counter <= previous:
                    _fail("credential_counter_conflict", "Counter did not advance; host investigation is required.")
                after = self._current()
                if before["observation"]["candidate_content_id"] != after["observation"]["candidate_content_id"]:
                    continue
                now = self._live()
                return {"format": FORMAT, "status": "ok", "verification": "verified_under_host_configured_credential",
                        "request_id": identity(self._request), "request": deepcopy(self._request),
                        "assertion_id": "sha256:" + hashlib.sha256(assertion).hexdigest(),
                        "preparation": after, "verified_at": now.isoformat(),
                        "authenticator": {"user_presence": True, "user_verification": True,
                                          "sign_count": counter, "previous_sign_count": previous,
                                          "backup_eligible": bool(auth_data[32] & 8), "backed_up": bool(auth_data[32] & 16)},
                        "authority": {"human_event_authentication": "not_established", "enrollment": "host_responsibility",
                                      "review_display": "not_verified", "acceptance": "not_established",
                                      "replay": "not_checked", "writes": False},
                        "observation": {"atomic": False, "freshness": "matching_preparations"}}
            except ChangedDuringCapture:
                continue
        _fail("unstable_inputs", "Project or candidate changed repeatedly; retry when stable.")

    def _response(self, assertion):
        code = "invalid_webauthn_assertion"
        if not isinstance(assertion, bytes) or not 0 < len(assertion) <= MAX_ASSERTION_BYTES:
            _fail(code, "Assertion must be bounded UTF-8 JSON bytes.")
        try:
            response = parse_json(assertion)
            if not isinstance(response, dict) or not {"id", "rawId", "type", "response"} <= set(response) or set(response) - {
                "id", "rawId", "type", "response", "clientExtensionResults", "authenticatorAttachment"
            }:
                raise ValueError("unsupported response fields")
            if response["type"] != "public-key" or response["id"] != response["rawId"] or response["rawId"] != self._credential["id"]:
                raise ValueError("credential mismatch")
            if response.get("clientExtensionResults", {}) != {} or response.get("authenticatorAttachment") not in (None, "platform", "cross-platform"):
                raise ValueError("unsupported extensions or attachment")
            data = response["response"]
            _shape(data, "clientDataJSON authenticatorData signature userHandle", code)
            client_bytes = _decode(data["clientDataJSON"], 1, 4096, code)
            client = parse_json(client_bytes)
            if not isinstance(client, dict) or not {"type", "challenge", "origin"} <= set(client) or set(client) - {"type", "challenge", "origin", "crossOrigin"}:
                raise ValueError("unsupported client data")
            if client.get("crossOrigin", False) is not False or client["type"] != "webauthn.get" or client["origin"] != self._origin:
                raise ValueError("unsupported client origin or operation")
            if _decode(client["challenge"], 32, 32, code) != self._challenge:
                raise ValueError("challenge mismatch")
            auth = _decode(data["authenticatorData"], 37, 37, code)
            if auth[32] & ~0x1d or (auth[32] & 16 and not auth[32] & 8):
                raise ValueError("unsupported flags or backup state")
            _decode(data["signature"], 8, 80, code)
            if data["userHandle"] is not None and _decode(data["userHandle"], 1, 64, code) != _decode(self._credential["user_handle"], 1, 64, code):
                raise ValueError("user handle mismatch")
            return response, auth
        except (ValueError, KeyError, TypeError, UnicodeError) as error:
            raise InventoryError(code, "Malformed or unsupported WebAuthn assertion.") from error
