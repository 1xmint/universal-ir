"""Temporary registration checks; account mapping and isolation belong to a host."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import os
import struct
from threading import Lock

from .inventory import InventoryError, canonical, identity, parse_json
from .receipts import _fail, _shape, _text
from .webauthn_review import _backend, _decode, _origin, encode


DOMAIN = b"Universal IR WebAuthn registration v1\x00"


class WebAuthnRegistration:
    def __init__(self, *, host_id, actor_id, rp_id, origin, clock=None):
        for value in (host_id, actor_id):
            _text(value, "invalid_review_configuration")
        _origin(rp_id, origin)
        if clock is not None and not callable(clock):
            _fail("invalid_review_configuration", "Host clock must be callable.")
        _backend()
        from fido2.server import Fido2Server
        from fido2.webauthn import PublicKeyCredentialRpEntity, PublicKeyCredentialUserEntity, PublicKeyCredentialParameters
        self._clock = clock if clock is not None else lambda: datetime.now(timezone.utc)
        self._issued = self._now()
        self._expires = self._issued + timedelta(minutes=2)
        self._handle = os.urandom(32)
        self._request = {"format": "uir.webauthn-registration-request.v1", "host_id": host_id, "actor_id": actor_id,
                         "rp_id": rp_id, "origin": origin, "user_handle": encode(self._handle),
                         "issued_at": self._issued.isoformat(), "expires_at": self._expires.isoformat(), "nonce": encode(os.urandom(32))}
        challenge = hashlib.sha256(DOMAIN + canonical(self._request)).digest()
        self._origin = origin
        self._server = Fido2Server(PublicKeyCredentialRpEntity(id=rp_id, name="Universal IR review demo"),
                                  attestation="none", verify_origin=lambda actual: actual == origin)
        self._server.allowed_algorithms = [PublicKeyCredentialParameters(type="public-key", alg=-7)]
        options, self._state = self._server.register_begin(PublicKeyCredentialUserEntity(
            id=self._handle, name=actor_id, display_name=actor_id), user_verification="required", challenge=challenge)
        self._options = dict(options)
        self._options["publicKey"]["timeout"] = 120000
        self._challenge = encode(challenge)
        self._used = False
        self._lock = Lock()

    def _now(self):
        try:
            value = self._clock()
        except Exception:
            _fail("host_clock_unavailable", "Host clock is unavailable.")
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
            _fail("invalid_verification_time", "Host time must be aware UTC.")
        return value

    def _live(self):
        if self._used:
            _fail("registration_used", "This temporary registration has already completed.")
        if not self._issued <= self._now() < self._expires:
            _fail("review_expired", "Registration expired or host time precedes issuance.")

    def options(self):
        with self._lock:
            self._live()
            return {"request_id": identity(self._request), "request": deepcopy(self._request), "options": deepcopy(self._options)}

    def complete(self, raw):
        with self._lock:
            self._live()
            code = "invalid_webauthn_registration"
            try:
                if not isinstance(raw, bytes) or not 0 < len(raw) <= 16 * 1024:
                    raise ValueError("bounded bytes required")
                response = parse_json(raw)
                if not isinstance(response, dict) or not {"id", "rawId", "type", "response"} <= set(response) or set(response) - {
                    "id", "rawId", "type", "response", "authenticatorAttachment", "clientExtensionResults"
                }:
                    raise ValueError("unsupported response fields")
                credential_id = _decode(response["rawId"], 1, 1023, code)
                if response["id"] != response["rawId"] or response["type"] != "public-key" or response.get("clientExtensionResults", {}) != {}:
                    raise ValueError("unsupported identity or extensions")
                if response.get("authenticatorAttachment") not in (None, "platform", "cross-platform"):
                    raise ValueError("unsupported attachment")
                _shape(response["response"], "clientDataJSON attestationObject", code)
                client = parse_json(_decode(response["response"]["clientDataJSON"], 1, 4096, code))
                if not isinstance(client, dict) or not {"type", "challenge", "origin"} <= set(client) or set(client) - {"type", "challenge", "origin", "crossOrigin"}:
                    raise ValueError("unsupported client data")
                if client["type"] != "webauthn.create" or client["challenge"] != self._challenge or client["origin"] != self._origin or client.get("crossOrigin", False) is not False:
                    raise ValueError("client context mismatch")
                from fido2 import cbor
                from fido2.webauthn import AuthenticatorData
                from cryptography.hazmat.primitives.asymmetric import ec
                attestation = cbor.decode(_decode(response["response"]["attestationObject"], 1, 8192, code))
                _shape(attestation, "fmt authData attStmt", code)
                if attestation["fmt"] != "none" or attestation["attStmt"] != {} or not isinstance(attestation["authData"], bytes):
                    raise ValueError("only none attestation supported")
                auth = AuthenticatorData(attestation["authData"])
                if auth.flags & ~0x5d or not auth.is_attested() or (auth.is_backed_up() and not auth.is_backup_eligible()):
                    raise ValueError("unsupported flags")
                registered = auth.credential_data
                key = registered.public_key
                if registered.credential_id != credential_id or set(key) != {1, 3, -1, -2, -3} or any(type(key[k]) is not int for k in (1, 3, -1)) or (key[1], key[3], key[-1]) != (2, -7, 1):
                    raise ValueError("credential or algorithm mismatch")
                if any(not isinstance(key[k], bytes) or len(key[k]) != 32 for k in (-2, -3)):
                    raise ValueError("invalid coordinates")
                ec.EllipticCurvePublicNumbers(int.from_bytes(key[-2], "big"), int.from_bytes(key[-3], "big"), ec.SECP256R1()).public_key()
                self._server.register_complete(self._state, response)
                self._live()
                credential = {"id": encode(credential_id), "public_key_x": encode(key[-2]), "public_key_y": encode(key[-3]),
                              "user_handle": encode(self._handle), "sign_count": auth.counter}
                self._used = True
                return {"format": "uir.webauthn-registration.v1", "status": "ok", "request_id": identity(self._request),
                        "credential": credential, "actor_authentication": "not_established", "device_attestation": "not_requested",
                        "persistence": "none"}
            except (ValueError, KeyError, TypeError, AttributeError, AssertionError, struct.error, RecursionError) as error:
                raise InventoryError(code, "Malformed, unsupported, or context-mismatched registration.") from error
