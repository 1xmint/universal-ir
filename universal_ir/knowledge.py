"""Read-only inspection of immutable project knowledge; no approval verifier."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path, PurePosixPath
import re

from .inventory import (
    ChangedDuringCapture, IgnoreRules, InventoryError, _is_link, _read_file,
    _token, capture, identity, parse_json, relative_path,
)


FORMAT = "uir.knowledge-view.v1"
RECORD_FORMAT = "uir.knowledge.v1"
STORE = ".uir/knowledge/records"
MAX_RECORD_BYTES = 1024 * 1024
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
LOGICAL_ID = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")


def _invalid(message):
    raise InventoryError("invalid_knowledge", message)


def _shape(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields.split()):
        _invalid("Knowledge object has missing or unsupported fields.")


def _text(value):
    if not isinstance(value, str) or not value.strip():
        _invalid("Knowledge strings must be nonempty UTF-8.")
    try:
        value.encode("utf-8")
    except UnicodeError:
        _invalid("Knowledge strings must be representable as UTF-8.")


def _digest(value):
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        _invalid("Knowledge digests require sha256 and 64 lowercase hexadecimal digits.")


def _paths(value):
    if not isinstance(value, list) or not value:
        _invalid("Knowledge scope must be a nonempty path list.")
    for path in value:
        relative_path(path, root_allowed=True)
    if len(set(value)) != len(value):
        _invalid("Knowledge scope paths must be unique.")


def _within(path, scope):
    return any(part == "." or path == part or path.startswith(part + "/") for part in scope)


def source_projection(manifest, scope):
    """Scoped evidence identity, excluding knowledge entries without losing controls."""
    _paths(scope)
    result = {"format": "uir.knowledge-input.v1", "scope": scope}
    for field in ("extractor", "ignore_engine", "configuration", "controls"):
        result[field] = manifest[field]
    for field in ("entries", "omissions"):
        result[field] = [item for item in manifest[field] if _within(item["path"], scope)
                         and item["path"] != ".uir" and not item["path"].startswith(".uir/")]
    return result


def validate_record(record, project_id, path):
    """Validate bytes' meaning and identity; never establish developer approval."""
    try:
        _shape(record, "format project_id record_id body")
        if record["format"] != RECORD_FORMAT or record["project_id"] != project_id:
            _invalid("Knowledge format or project identity does not match.")
        _digest(record["record_id"])
        body = record["body"]
        _shape(body, "id category text scope origin input_id evidence supersedes state")
        if not isinstance(body["id"], str) or not LOGICAL_ID.fullmatch(body["id"]):
            _invalid("Invalid logical knowledge identity.")
        if body["category"] not in ("purpose", "requirement", "decision", "summary"):
            _invalid("Unknown knowledge category.")
        _text(body["text"])
        _paths(body["scope"])
        if body["state"] not in ("active", "withdrawn"):
            _invalid("Unknown knowledge state.")
        predecessors = body["supersedes"]
        if not isinstance(predecessors, list):
            _invalid("Supersedes must be a list of record identities.")
        for predecessor in predecessors:
            _digest(predecessor)
        if len(set(predecessors)) != len(predecessors):
            _invalid("Supersession references must be unique.")
        if body["state"] == "withdrawn" and not predecessors:
            _invalid("Withdrawal needs a predecessor.")
        origin = body["origin"]
        if not isinstance(origin, dict):
            _invalid("Origin must be a supported object.")
        kind = origin.get("kind")
        if kind == "ai_interpretation":
            _shape(origin, "kind host_id method assumptions")
            _text(origin["host_id"])
            _text(origin["method"])
            if not isinstance(origin["assumptions"], list):
                _invalid("Assumptions must be strings.")
            for assumption in origin["assumptions"]:
                if not isinstance(assumption, str):
                    _invalid("Assumptions must be strings.")
                assumption.encode("utf-8")
            _digest(body["input_id"])
        elif kind == "developer_statement":
            _shape(origin, "kind host_id event_id actor_id")
            for field in ("host_id", "event_id", "actor_id"):
                _text(origin[field])
        elif kind == "document_declaration":
            _shape(origin, "kind")
        else:
            _invalid("Unknown knowledge origin.")
        if kind != "ai_interpretation" and body["input_id"] is not None:
            _invalid("Declarations must not claim a source projection identity.")
        evidence = body["evidence"]
        if not isinstance(evidence, list) or (not evidence and kind != "developer_statement"):
            _invalid("This origin needs an evidence list with references.")
        for reference in evidence:
            if not isinstance(reference, dict):
                _invalid("Evidence must use supported reference objects.")
            reference_kind = reference.get("kind")
            if reference_kind == "record":
                _shape(reference, "kind record_id")
                _digest(reference["record_id"])
                continue
            if reference_kind == "file":
                _shape(reference, "kind path content_id")
            elif reference_kind == "document":
                _shape(reference, "kind path content_id start_byte end_byte quote")
                start, end = reference["start_byte"], reference["end_byte"]
                if type(start) is not int or type(end) is not int or not 0 <= start < end:
                    _invalid("Document byte offsets must be ordered nonnegative integers.")
                _text(reference["quote"])
                if end - start != len(reference["quote"].encode("utf-8")):
                    _invalid("Document offsets and quoted UTF-8 byte length disagree.")
            else:
                _invalid("Unknown evidence reference kind.")
            relative_path(reference["path"])
            if _within(reference["path"], [".uir/knowledge"]):
                _invalid("Knowledge dependencies must use record references.")
            _digest(reference["content_id"])
        if kind == "document_declaration" and not any(
            ref["kind"] == "document" and ref["quote"] == body["text"] for ref in evidence
        ):
            _invalid("Document declarations need exact quoted wording.")
        unsigned = {key: record[key] for key in ("format", "project_id", "body")}
        if identity(unsigned) != record["record_id"]:
            _invalid("Knowledge record identity does not match its contents.")
        expected = f"{STORE}/{body['id']}/{record['record_id'][7:]}.json"
        if path != expected:
            _invalid("Knowledge record path does not match logical and content identities.")
    except (UnicodeError, TypeError, ValueError, InventoryError) as error:
        if isinstance(error, InventoryError) and error.code == "invalid_knowledge":
            raise
        _invalid(f"Invalid knowledge record: {error}")
    return record


def _read_bytes(root, entry, *, window=None):
    """Read only inventoried files, checking parent boundaries and opened identity."""
    path = root / entry["path"]

    def parents():
        current = root
        for part in PurePosixPath(entry["path"]).parts[:-1]:
            current /= part
            if _is_link(current) or not current.is_dir():
                raise ChangedDuringCapture()

    try:
        parents()
        digest, size, token = _read_file(path)
        if digest != entry["content_id"] or size != entry["bytes"]:
            raise ChangedDuringCapture()
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            if _token(os.fstat(stream.fileno())) != token:
                raise ChangedDuringCapture()
            if window is None:
                data = stream.read(MAX_RECORD_BYTES + 1)
                if len(data) > MAX_RECORD_BYTES:
                    _invalid("Knowledge records are limited to 1 MiB each in this prototype.")
            else:
                start, end = window
                stream.seek(start)
                data = stream.read(end - start)
            if _token(os.fstat(stream.fileno())) != token:
                raise ChangedDuringCapture()
        parents()
        if _is_link(path) or _token(path.lstat()) != token:
            raise ChangedDuringCapture()
        if window is None and "sha256:" + hashlib.sha256(data).hexdigest() != digest:
            raise ChangedDuringCapture()
        return data
    except FileNotFoundError as error:
        raise ChangedDuringCapture() from error
    except OSError as error:
        raise InventoryError("unreadable_input", f"Cannot read knowledge evidence {entry['path']}: {error}") from error


def _history(records):
    dependencies, children = {}, {key: [] for key in records}
    for key, record in records.items():
        body = record["body"]
        dependencies[key] = body["supersedes"] + [ref["record_id"] for ref in body["evidence"]
                                                   if ref["kind"] == "record"]
        for predecessor in body["supersedes"]:
            if predecessor in records:
                if records[predecessor]["body"]["id"] != body["id"]:
                    _invalid("Supersession crosses logical identities.")
                children[predecessor].append(key)
    # Iterative traversal keeps long valid histories independent of Python recursion limits.
    order, colors = [], {}
    for key in records:
        if colors.get(key) == 2:
            continue
        stack = [(key, False)]
        while stack:
            current, leaving = stack.pop()
            if leaving:
                colors[current] = 2
                order.append(current)
                continue
            if colors.get(current) == 1:
                _invalid("Knowledge dependencies contain a cycle.")
            if colors.get(current) == 2:
                continue
            colors[current] = 1
            stack.append((current, True))
            stack.extend((dep, False) for dep in reversed(dependencies[current]) if dep in records)
    groups = {}
    for key, record in records.items():
        groups.setdefault(record["body"]["id"], []).append(key)
    heads = {name: sorted(key for key in keys if not children[key]) for name, keys in groups.items()}
    return order, children, heads


def _inspect_capture(root, captured):
    manifest = captured.manifest
    project = manifest["configuration"]["project_id"]
    if project is None:
        raise InventoryError("knowledge_unavailable", "Knowledge inspection needs configured project_id.")
    entries = {item["path"]: item for item in manifest["entries"]}
    for parent in (".uir/knowledge", STORE):
        if parent in entries and entries[parent]["kind"] == "file":
            _invalid("Knowledge store parents must be directories.")
    gaps = [item for item in manifest["omissions"] if _within(item["path"], [STORE])
            or _within(STORE, [item["path"]])]
    gaps += [item for item in entries.values() if item["kind"] == "boundary" and
             (_within(item["path"], [STORE]) or _within(STORE, [item["path"]]))]
    records, locations = {}, {}
    for path, entry in entries.items():
        if not _within(path, [STORE]):
            continue
        if entry["kind"] == "boundary":
            continue
        parts = path[len(STORE):].strip("/").split("/") if path != STORE else []
        if entry["kind"] == "directory":
            if len(parts) > 1 or (parts and not LOGICAL_ID.fullmatch(parts[0])):
                _invalid("Unexpected directory within the immutable record store.")
            continue
        if len(parts) != 2 or not parts[1].endswith(".json"):
            _invalid("Unexpected file within the immutable record store.")
        data = _read_bytes(root, entry)
        if b"\r" in data or not data.endswith(b"\n"):
            _invalid("Durable knowledge JSON requires LF and a final newline.")
        try:
            record = validate_record(parse_json(data), project, path)
        except (ValueError, UnicodeError) as error:
            _invalid(f"Invalid knowledge JSON at {path}: {error}")
        key = record["record_id"]
        records[key], locations[key] = record, path
    order, children, heads = _history(records)
    computed = {}
    for key in order:
        record, references = records[key], []
        issues = []
        body = record["body"]
        for ref in body["evidence"]:
            reference = dict(ref)
            if ref["kind"] == "record":
                target = computed.get(ref["record_id"])
                if target is None:
                    status, reason = "unresolved", "missing_revision"
                elif target["evidence_status"] == "unresolved":
                    status, reason = "unresolved", "referenced_evidence_unresolved"
                elif children[ref["record_id"]] or len(heads[target["body"]["id"]]) > 1:
                    status, reason = "changed", "superseded_or_competing_revision"
                else:
                    status, reason = target["evidence_status"], "referenced_revision"
                reference.update(status=status, reason=reason)
                if target:
                    reference["attribution"] = target["attribution"]
            else:
                target = entries.get(ref["path"])
                if target is None or target["kind"] != "file":
                    status, reason = "unresolved", "file_not_included"
                elif target["content_id"] != ref["content_id"]:
                    status, reason = "changed", "file_contents_changed"
                else:
                    status, reason = "matches", "file_contents_match"
                    if ref["kind"] == "document":
                        if ref["end_byte"] > target["bytes"]:
                            _invalid("Document offsets exceed the identified file's byte length.")
                        quoted = _read_bytes(root, target, window=(ref["start_byte"], ref["end_byte"]))
                        if quoted != ref["quote"].encode("utf-8"):
                            _invalid("Quoted document bytes do not match identified contents.")
                reference.update(status=status, reason=reason)
            references.append(reference)
        missing = [item for item in body["supersedes"] if item not in records]
        statuses = [ref["status"] for ref in references]
        if missing:
            statuses.append("unresolved")
            issues.append({"reason": "missing_predecessors", "record_ids": missing})
        projection = None
        if body["origin"]["kind"] == "ai_interpretation":
            projection = identity(source_projection(manifest, body["scope"]))
            if projection != body["input_id"]:
                statuses.append("changed")
                issues.append({"reason": "source_projection_changed"})
        if body["origin"]["kind"] == "document_declaration" and not any(
            ref["kind"] == "document" and ref["quote"] == body["text"] and
            ref["path"] in manifest["configuration"]["documents"] for ref in body["evidence"]
        ):
            statuses.append("unresolved")
            issues.append({"reason": "declaration_document_not_configured"})
        evidence_status = "unresolved" if "unresolved" in statuses else "changed" if "changed" in statuses else "matches"
        developer = body["origin"]["kind"] == "developer_statement"
        computed[key] = {
            "record_id": key, "path": locations[key], "body": body,
            "attribution": "unverified_attribution" if developer else "not_applicable",
            "evidence_status": evidence_status,
            "history": "superseded" if children[key] else "forked" if len(heads[body["id"]]) > 1 else "head",
            "disposition": "pending_acceptance" if developer or body["supersedes"] or body["state"] == "withdrawn" else body["state"],
            "source_projection": projection, "references": references,
            "issues": issues,
            "missing_predecessors": missing, "successors": sorted(children[key]),
            "unresolved_scope": [path for path in body["scope"] if path not in entries or entries[path]["kind"] == "boundary"],
        }
    return project, computed, heads, gaps


def inspect_knowledge(root: Path, *, selected_id=None, offset=0, limit=20, full=False):
    """Publish a bounded view only after matching captures around knowledge reads."""
    if not 1 <= limit <= 200 or offset < 0 or (selected_id is not None and not LOGICAL_ID.fullmatch(selected_id)):
        raise InventoryError("invalid_arguments", "Use a logical --id, limit 1..200, and nonnegative offset.")
    try:
        root = root.resolve()
    except (OSError, RuntimeError) as error:
        raise InventoryError("invalid_root", f"Cannot resolve selected project: {error}") from error
    if not root.is_dir():
        raise InventoryError("invalid_root", "Select an existing project directory.")
    started = datetime.now(timezone.utc).isoformat()
    rules = IgnoreRules(root)
    try:
        for _ in range(3):
            try:
                first = capture(root, rules)
                inspection_error = None
                try:
                    project, records, heads, gaps = _inspect_capture(root, first)
                except InventoryError as error:
                    inspection_error = error
                second = capture(root, rules)
                if first != second:
                    continue
                if inspection_error:
                    raise inspection_error
                verified = datetime.now(timezone.utc).isoformat()
                break
            except ChangedDuringCapture:
                continue
        else:
            raise InventoryError("unstable_inputs", "Knowledge inputs changed during inspection; retry when stable.")
    finally:
        rules.close()
    if selected_id is not None and selected_id not in heads:
        raise InventoryError("unknown_knowledge", "Selected logical identity has no included revisions.")
    ordered = sorted(records.values(), key=lambda item: (item["body"]["id"], item["record_id"]))
    selected = [item for item in ordered if selected_id is None or item["body"]["id"] == selected_id]
    shown = selected if full else selected[offset:offset + limit]
    group_ids = sorted(name for name in heads if selected_id is None or name == selected_id)
    group_shown = group_ids if full else group_ids[:limit]
    groups = [{"id": name, "competing_heads": len(heads[name]) > 1,
               "heads_total": len(heads[name]), "heads": heads[name] if full else heads[name][:limit],
               "heads_omitted": 0 if full else max(0, len(heads[name]) - limit)} for name in group_shown]
    return {
        "format": FORMAT, "status": "ok", "project_id": project, "snapshot": identity(second.manifest),
        "observation": {"root": str(root), "started_at": started,
                        "verified_at": verified,
                        "freshness": "matching_captures_around_knowledge_reads", "atomic": False},
        "coverage": {"complete": not gaps, "gaps_total": len(gaps),
                     "gaps": gaps if full else gaps[:limit], "gaps_omitted": 0 if full else max(0, len(gaps) - limit),
                     "attribution_verifier": "unavailable", "acceptance": "not_established",
                     "history": "included_revisions_only", "semantics": "unknown", "model_calls": 0,
                     "record_bytes_limit": MAX_RECORD_BYTES},
        "summary": {"revisions": len(records), "logical_ids": len(heads),
                    "competing_groups": sum(len(items) > 1 for items in heads.values()),
                    "evidence_status": dict(Counter(item["evidence_status"] for item in ordered)),
                    "unverified_developer_statements": sum(item["attribution"] == "unverified_attribution" for item in ordered)},
        "selection": {"id": selected_id, "offset": offset, "limit": limit, "full": full},
        "records": {"total": len(selected), "omitted": len(selected) - len(shown), "entries": shown},
        "groups": {"total": len(group_ids), "omitted": len(group_ids) - len(groups), "entries": groups},
    }
