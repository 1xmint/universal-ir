"""Narrow host-configured verification tool; no signer, user auth, or writer."""

from datetime import datetime, timezone
import os
from pathlib import Path

from .inventory import InventoryError, parse_json
from .knowledge import DIGEST
from .receipts import verify_project_receipt
from .prepared_receipts import verify_candidate_receipt


FORMAT = "uir.harness-verification.v1"
MAX_REQUEST_BYTES = 1024


def tool_definition():
    """Return a fresh provider-neutral tool description for a trusted host."""
    return {"name": "uir_verify_receipt",
            "description": "Verify a registered receipt under the host's fixed project and trust policy. "
                           "Does not approve, accept, or write knowledge.",
            "input_schema": {"type": "object", "additionalProperties": False,
                             "required": ["record_id", "receipt_id"], "properties": {
                                 name: {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                                        "minLength": 71, "maxLength": 71}
                                 for name in ("record_id", "receipt_id")}}}


def prepared_tool_definition():
    return {"name": "uir_verify_preparation",
            "description": "Verify a host-registered external candidate and its exact reviewed context. "
                           "Does not authenticate a human event, accept, or write knowledge.",
            "input_schema": {"type": "object", "additionalProperties": False, "required": ["preparation_id"],
                             "properties": {"preparation_id": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                                                               "minLength": 71, "maxLength": 71}}}}


def _request(arguments, fields):
    if not isinstance(arguments, bytes) or len(arguments) > MAX_REQUEST_BYTES:
        raise InventoryError("invalid_tool_request", "Request must be at most 1024 UTF-8 JSON bytes.")
    try:
        request = parse_json(arguments)
    except (ValueError, UnicodeError) as error:
        raise InventoryError("invalid_tool_request", "Request is not strict UTF-8 JSON.") from error
    if not isinstance(request, dict) or set(request) != set(fields):
        raise InventoryError("invalid_tool_request", "Request fields do not match the registered operation.")
    for value in request.values():
        _digest(value, "invalid_tool_request")
    return request


def _failure(error):
    return {"format": FORMAT, "status": "error", "error": {
        "code": error.code, "message": "Verification failed; the host can inspect the inputs and retry."}}


def _digest(value, code):
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise InventoryError(code, "Expected a lowercase SHA-256 identity.")


def _path(value):
    try:
        path = Path(os.path.abspath(value))
        str(path).encode("utf-8")
        if "\x00" in str(path):
            raise ValueError("NUL in host path")
        return path
    except (TypeError, ValueError, OSError) as error:
        raise InventoryError("invalid_host_configuration", "Invalid host-selected path.") from error


class HarnessVerifier:
    """Host-only construction; expose handle(), not this object's configuration.

    Python object privacy is not isolation. The host must restrict model tools
    and protect this process/configuration from arbitrary model code or shells.
    """

    def __init__(self, *, root, project_id, policy_path, policy_id, receipt_paths, clock=None):
        if not isinstance(project_id, str) or not project_id.strip():
            raise InventoryError("invalid_host_configuration", "A fixed project identity is required.")
        try:
            project_id.encode("utf-8")
        except UnicodeError as error:
            raise InventoryError("invalid_host_configuration", "Invalid project identity encoding.") from error
        _digest(policy_id, "invalid_host_configuration")
        if not isinstance(receipt_paths, dict) or (clock is not None and not callable(clock)):
            raise InventoryError("invalid_host_configuration", "Host receipt registry and clock are invalid.")
        paths = {}
        for receipt_id, path in receipt_paths.items():
            _digest(receipt_id, "invalid_host_configuration")
            paths[receipt_id] = _path(path)
        self._root, self._policy_path = _path(root), _path(policy_path)
        self._project_id, self._policy_id = project_id, policy_id
        self._receipt_paths = paths
        self._clock = clock if clock is not None else lambda: datetime.now(timezone.utc)

    def handle(self, arguments):
        """Consume raw UTF-8 JSON arguments; return an automation result, no writes."""
        try:
            request = _request(arguments, ("record_id", "receipt_id"))
            path = self._receipt_paths.get(request["receipt_id"])
            if path is None:
                raise InventoryError("unknown_receipt", "Receipt is not registered by this host.")

            result = verify_project_receipt(
                self._root, request["record_id"], path, self._policy_path, self._policy_id,
                expected_project_id=self._project_id, clock=self._trusted_time,
            )
            if result["receipt_id"] != request["receipt_id"]:
                raise InventoryError("receipt_lookup_mismatch", "Registered input does not match requested receipt.")
            return {"format": FORMAT, "status": "ok", "result": result}
        except InventoryError as error:
            # Do not forward host paths or arbitrary decoder/OS details to a model.
            return _failure(error)

    def _trusted_time(self):
        try:
            return self._clock()
        except Exception as error:
            raise InventoryError("host_clock_unavailable", "Host clock failed.") from error


class PreparedReceiptVerifier(HarnessVerifier):
    """Host owns the complete review registry; models select a preparation ID."""

    def __init__(self, *, root, project_id, policy_path, policy_id, reviews, clock=None):
        super().__init__(root=root, project_id=project_id, policy_path=policy_path, policy_id=policy_id,
                         receipt_paths={}, clock=clock)
        if not isinstance(reviews, dict):
            raise InventoryError("invalid_host_configuration", "Host review registry must be a dictionary.")
        self._reviews = {}
        for preparation_id, review in reviews.items():
            _digest(preparation_id, "invalid_host_configuration")
            if not isinstance(review, dict) or set(review) != {"record_id", "candidate_path", "receipt_id", "receipt_path"}:
                raise InventoryError("invalid_host_configuration", "Review entry has unsupported fields.")
            for name in ("record_id", "receipt_id"):
                _digest(review[name], "invalid_host_configuration")
            self._reviews[preparation_id] = {"record_id": review["record_id"], "receipt_id": review["receipt_id"],
                                             "candidate_path": _path(review["candidate_path"]),
                                             "receipt_path": _path(review["receipt_path"])}

    def handle(self, arguments):
        try:
            request = _request(arguments, ("preparation_id",))
            review = self._reviews.get(request["preparation_id"])
            if review is None:
                raise InventoryError("unknown_preparation", "Review is not registered by this host.")
            result = verify_candidate_receipt(
                self._root, review["candidate_path"], review["receipt_path"], self._policy_path, self._policy_id,
                request["preparation_id"], expected_project_id=self._project_id, clock=self._trusted_time)
            if result["record_id"] != review["record_id"] or result["receipt_id"] != review["receipt_id"]:
                raise InventoryError("receipt_lookup_mismatch", "Review lookup does not match verified candidate/receipt identities.")
            return {"format": FORMAT, "status": "ok", "result": result}
        except InventoryError as error:
            return _failure(error)
