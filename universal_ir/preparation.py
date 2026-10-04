"""Read-only external knowledge candidate review; no authority or acceptance."""

from datetime import datetime, timezone
import os
from pathlib import Path

from .inventory import ChangedDuringCapture, IgnoreRules, InventoryError, _is_link, _read_file, capture, identity, parse_json
from .knowledge import DIGEST, MAX_RECORD_BYTES, _inspect_capture, _read_bytes, source_projection


FORMAT = "uir.knowledge-preparation.v1"


def _candidate_input(path, root):
    """Explicit external transport, never a source inclusion or a write target."""
    try:
        path = Path(os.path.abspath(path))
        str(path).encode("utf-8")
        if "\x00" in str(path):
            raise ValueError("NUL in candidate path")
        if any(_is_link(part) for part in (path, *path.parents)):
            raise InventoryError("invalid_candidate_input", "Candidate paths cannot cross a link or junction.")
        if path.resolve().is_relative_to(root) or not path.is_file():
            raise InventoryError("invalid_candidate_input", "Select an existing regular candidate file outside the project.")
        digest, size, token = _read_file(path)
        if size > MAX_RECORD_BYTES:
            raise InventoryError("invalid_candidate_input", "Candidate input is limited to 1 MiB.")
        data = _read_bytes(path.parent, {"path": path.name, "content_id": digest, "bytes": size})
        if _read_file(path) != (digest, size, token):
            raise ChangedDuringCapture()
        return data, digest, token
    except FileNotFoundError as error:
        raise ChangedDuringCapture() from error
    except OSError as error:
        raise InventoryError("unreadable_input", f"Cannot read selected candidate input: {error}") from error
    except (TypeError, ValueError) as error:
        raise InventoryError("invalid_candidate_input", "Candidate path must be representable as UTF-8.") from error


def prepare_knowledge(root, candidate_path, *, expected_snapshot=None):
    """Inspect an in-memory candidate overlay between matching source captures."""
    if expected_snapshot is not None and (not isinstance(expected_snapshot, str) or not DIGEST.fullmatch(expected_snapshot)):
        raise InventoryError("invalid_arguments", "Expected snapshot must be a lowercase SHA-256 identity.")
    try:
        str(root).encode("utf-8")
        if "\x00" in str(root):
            raise ValueError("NUL in project root")
        root = Path(root).resolve()
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise InventoryError("invalid_root", f"Cannot resolve selected project: {error}") from error
    if not root.is_dir():
        raise InventoryError("invalid_root", "Select an existing project directory.")
    started = datetime.now(timezone.utc).isoformat()
    rules = IgnoreRules(root)
    try:
        for _ in range(3):
            try:
                first = capture(root, rules)
                problem, candidate_input = None, None
                try:
                    candidate_input = _candidate_input(candidate_path, root)
                    data = candidate_input[0]
                    if b"\r" in data or not data.endswith(b"\n"):
                        raise InventoryError("invalid_knowledge", "Candidate JSON requires LF and a final newline.")
                    try:
                        record = parse_json(data)
                    except (ValueError, UnicodeError) as error:
                        raise InventoryError("invalid_knowledge", f"Invalid candidate JSON: {error}") from error
                    if not isinstance(record, dict):
                        raise InventoryError("invalid_knowledge", "Candidate must be a complete record object.")
                    project, records, heads, gaps = _inspect_capture(root, first, candidate=record)
                except InventoryError as error:
                    problem = error
                second = capture(root, rules)
                try:
                    final_input = _candidate_input(candidate_path, root)
                except InventoryError as error:
                    if candidate_input is not None or problem is None or error.code != problem.code:
                        continue
                    final_input = None
                if first != second or candidate_input != final_input:
                    continue
                if problem is not None:
                    raise problem
                snapshot = identity(second.manifest)
                if expected_snapshot is not None and snapshot != expected_snapshot:
                    raise InventoryError("stale_snapshot", "Current project differs from the expected review base.")
                key, body = record["record_id"], record["body"]
                included = records[key]["path"] is not None
                existing = set(records) if included else set(records) - {key}
                base_heads = sorted(item for item in existing if records[item]["body"]["id"] == body["id"]
                                    and not any(child in existing for child in records[item]["successors"]))
                projection = identity(source_projection(second.manifest, body["scope"]))
                inputs = {"format": "uir.knowledge-preparation-input.v1", "project_id": project,
                          "record_id": key, "snapshot": snapshot, "source_input_id": projection,
                          "included_heads": base_heads}
                return {"format": FORMAT, "status": "ok", "preparation_id": identity(inputs),
                        "project_id": project, "snapshot": snapshot, "preconditions": inputs,
                        "candidate": {"record": record, "already_included": included,
                                      "evaluation": records[key]},
                        "transition": {"meaning": "included_structural_history_only",
                                       "operation": "already_included" if included else "proposed_addition",
                                       "included_heads_before": base_heads, "included_heads_after": heads[body["id"]],
                                       "uncovered_heads": sorted(set(base_heads) - set(body["supersedes"])),
                                       "would_leave_competing_heads": len(heads[body["id"]]) > 1},
                        "coverage": {"complete": not gaps, "gaps": gaps, "semantics": "unknown"},
                        "authority": {"approval": "not_established", "acceptance": "not_established",
                                      "writes": False, "model_calls": 0},
                        "observation": {"root": str(root), "started_at": started,
                                        "verified_at": datetime.now(timezone.utc).isoformat(),
                                        "candidate_content_id": candidate_input[1], "atomic": False,
                                        "freshness": "matching_captures_and_candidate_reads"}}
            except ChangedDuringCapture:
                continue
        raise InventoryError("unstable_inputs", "Project or candidate changed repeatedly; retry when stable.")
    finally:
        rules.close()
