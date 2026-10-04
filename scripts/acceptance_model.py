"""Abstract acceptance protocol model. NOT a writer or authentication boundary.

Tokens and Conditions are supplied by tests, not verified project inputs.
Publication/restart assume ideal atomicity and durability, not real filesystems.
No production operation may use this model as authorization or accepted intent.
"""

from dataclasses import asdict, dataclass
import hashlib
import json


class ModelError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _token(value):
    if not isinstance(value, str) or not value.strip():
        raise ModelError("invalid_model_input")
    try:
        value.encode("utf-8")
    except UnicodeError as error:
        raise ModelError("invalid_model_input") from error


def _tokens(values):
    if not isinstance(values, tuple):
        raise ModelError("invalid_model_input")
    for value in values:
        _token(value)
    if tuple(sorted(set(values))) != values:
        raise ModelError("invalid_model_input")


@dataclass(frozen=True)
class Record:
    logical_id: str
    record_id: str
    supersedes: tuple[str, ...] = ()
    state: str = "active"

    def __post_init__(self):
        _token(self.logical_id)
        _token(self.record_id)
        _tokens(self.supersedes)
        if self.state not in ("active", "withdrawn") or self.record_id in self.supersedes:
            raise ModelError("invalid_model_input")


@dataclass(frozen=True)
class Operation:
    project_id: str
    record: Record
    preparation_id: str
    source_id: str
    expected_heads: tuple[str, ...]
    receipt_id: str
    host_id: str
    event_id: str
    action: str = "approved"

    def __post_init__(self):
        for field in (self.project_id, self.preparation_id, self.source_id, self.receipt_id, self.host_id, self.event_id):
            _token(field)
        _tokens(self.expected_heads)
        if not isinstance(self.record, Record) or self.action != "approved":
            raise ModelError("invalid_model_input")

    @property
    def operation_id(self):
        data = {"format": "uir.acceptance-model-operation.v1", **asdict(self)}
        return "sha256:" + hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True,
                                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()

    @property
    def event_key(self):
        return self.project_id, self.host_id, self.event_id

    @property
    def receipt_subject(self):
        return self.project_id, self.record.record_id, self.preparation_id, self.host_id, self.event_id, self.action


@dataclass(frozen=True)
class Conditions:
    """Test oracles. Real authentication/freshness/policy are NOT implemented."""
    authenticated_event: bool = False
    receipt_valid: bool = False
    policy_current: bool = False
    review_current: bool = False
    evidence_ready: bool = False
    coverage_complete: bool = False

    def __post_init__(self):
        if any(type(value) is not bool for value in asdict(self).values()):
            raise ModelError("invalid_model_input")


class Protocol:
    """Single serialized abstract world; dictionaries simulate durable artifacts."""

    def __init__(self, project_id="sample", source_id="source-1"):
        _token(project_id)
        _token(source_id)
        self.project_id, self.source_id = project_id, source_id
        self.records, self.receipts, self.markers = {}, {}, {}
        self.active = None  # Ideal checkout lock owner; not an OS lock.

    def resolve(self):
        """All-or-error: never drop a broken committed marker to restore old heads."""
        accepted, events = {}, {}
        for key, operation in sorted(self.markers.items()):
            if not isinstance(operation, Operation) or key != operation.operation_id or operation.project_id != self.project_id:
                raise ModelError("invalid_marker")
            record = operation.record
            if not set(operation.expected_heads) <= set(record.supersedes) or (record.state == "withdrawn" and not operation.expected_heads):
                raise ModelError("invalid_transition")
            if self.records.get(record.record_id) != record or self.receipts.get(operation.receipt_id) != operation.receipt_subject:
                raise ModelError("incomplete_commit")
            if operation.event_key in events and events[operation.event_key] != key:
                raise ModelError("event_conflict")
            events[operation.event_key] = key
            if record.record_id in accepted:
                raise ModelError("duplicate_record")
            accepted[record.record_id] = record
        # Imported branches may share a base. Check accepted ancestry, not order.
        remaining, visited = set(accepted), set()
        while remaining:
            ready = set()
            for key in remaining:
                record = accepted[key]
                for predecessor in record.supersedes:
                    if predecessor not in accepted or accepted[predecessor].logical_id != record.logical_id:
                        raise ModelError("invalid_transition")
                if set(record.supersedes) <= visited:
                    ready.add(key)
            if not ready:
                raise ModelError("invalid_transition")
            remaining -= ready
            visited |= ready
        superseded = {key for record in accepted.values() for key in record.supersedes}
        heads = {}
        for key, record in sorted(accepted.items()):
            if key not in superseded:
                heads.setdefault(record.logical_id, []).append(key)
        return {"heads": heads, "events": events, "accepted": accepted}

    def _check(self, operation, conditions):
        if operation.project_id != self.project_id:
            raise ModelError("project_mismatch")
        resolved = self.resolve()
        if operation.operation_id in self.markers:
            return "already_committed"  # Historical acknowledgement, not fresh approval.
        if operation.event_key in resolved["events"]:
            raise ModelError("event_conflict")
        for field, code in (("authenticated_event", "attribution_required"), ("receipt_valid", "receipt_invalid"),
                            ("policy_current", "policy_not_current"), ("review_current", "stale_preparation"),
                            ("evidence_ready", "unresolved_evidence"), ("coverage_complete", "incomplete_coverage")):
            if not getattr(conditions, field):
                raise ModelError(code)
        if operation.source_id != self.source_id:
            raise ModelError("stale_source")
        heads = tuple(resolved["heads"].get(operation.record.logical_id, []))
        if operation.expected_heads != heads:
            raise ModelError("stale_heads")
        record = operation.record
        if record.record_id in resolved["accepted"]:
            raise ModelError("duplicate_record")
        if not set(heads) <= set(record.supersedes) or (record.state == "withdrawn" and not heads):
            raise ModelError("invalid_transition")
        for predecessor in record.supersedes:
            if predecessor not in resolved["accepted"] or resolved["accepted"][predecessor].logical_id != record.logical_id:
                raise ModelError("invalid_transition")
        return "ready"

    def start(self, operation, conditions=Conditions()):
        if not isinstance(operation, Operation) or not isinstance(conditions, Conditions):
            raise ModelError("invalid_model_input")
        if self.active is not None:
            raise ModelError("busy")
        status = self._check(operation, conditions)
        if status == "ready":
            self.active = operation
        return status

    def stage(self, kind):
        if self.active is None:
            raise ModelError("no_active_operation")
        operation = self.active
        if kind == "record":
            target, key, value = self.records, operation.record.record_id, operation.record
        elif kind == "receipt":
            target, key, value = self.receipts, operation.receipt_id, operation.receipt_subject
        else:
            raise ModelError("invalid_model_input")
        if key in target and target[key] != value:
            raise ModelError("artifact_conflict")
        target[key] = value  # Staged artifacts are inert until marker publication.

    def publish(self, conditions=Conditions()):
        if self.active is None:
            raise ModelError("no_active_operation")
        if not isinstance(conditions, Conditions):
            raise ModelError("invalid_model_input")
        operation = self.active
        self._check(operation, conditions)  # Reconcile again at the abstract commit point.
        if self.records.get(operation.record.record_id) != operation.record or self.receipts.get(operation.receipt_id) != operation.receipt_subject:
            raise ModelError("incomplete_staging")
        self.markers[operation.operation_id] = operation  # Assumed atomic + durable.
        self.active = None
        return "committed"

    def restart(self):
        result = Protocol(self.project_id, self.source_id)
        result.records, result.receipts, result.markers = self.records.copy(), self.receipts.copy(), self.markers.copy()
        return result  # Simulates crash release; proves nothing about OS recovery.

    def abort(self):
        self.active = None  # Staged artifacts remain inert; no event was consumed.

    def merge(self, other):
        """Union committed histories without a timestamp winner; validate on resolve."""
        if not isinstance(other, Protocol) or self.project_id != other.project_id:
            raise ModelError("project_mismatch")
        result = self.restart()
        for name in ("records", "receipts", "markers"):
            target = getattr(result, name)
            for key, value in getattr(other, name).items():
                if key in target and target[key] != value:
                    raise ModelError("artifact_conflict")
                target[key] = value
        return result


def demonstration():
    ready = Conditions(True, True, True, True, True, True)
    initial = Operation("sample", Record("retention", "r1"), "review-1", "source-1", (), "proof-1", "host", "event-1")
    world = Protocol()
    world.start(initial, ready)
    world.stage("record")
    before_marker = world.restart()
    before_marker.start(initial, ready)
    before_marker.stage("record")
    before_marker.stage("receipt")
    before_marker.publish(ready)
    after_marker = before_marker.restart()
    after_marker.source_id = "source-2"
    return {"format": "uir.acceptance-model-demo.v1", "status": "ok", "kind": "abstract_protocol_model",
            "before_marker_heads": world.resolve()["heads"], "after_marker_heads": after_marker.resolve()["heads"],
            "retry_after_source_change": after_marker.start(initial), "markers": len(after_marker.markers),
            "authority": {"human_authentication": "assumed_not_demonstrated", "filesystem_atomicity": "assumed_not_demonstrated",
                          "durability": "assumed_not_demonstrated", "project_writes": False, "model_calls": 0}}


if __name__ == "__main__":
    print(json.dumps(demonstration(), ensure_ascii=True, indent=2, allow_nan=False))
