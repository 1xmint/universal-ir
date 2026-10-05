"""Read-only literal task retrieval with snapshot-bound source excerpts."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import stat
import unicodedata

from .inventory import (
    ChangedDuringCapture, IgnoreRules, InventoryError, _classification, _is_link, _token,
    capture, identity, relative_path, view,
)


FORMAT = "uir.context.v1"
RETRIEVER = "literal.v1"
MAX_FILE_BYTES = 256 * 1024
MAX_EXCERPT_BYTES = 2048


def _terms(query):
    if not isinstance(query, str) or not query.strip() or len(query) > 256:
        raise InventoryError("invalid_arguments", "Query must contain 1..256 characters and non-whitespace text.")
    try:
        query.encode("utf-8")
    except UnicodeError as error:
        raise InventoryError("invalid_arguments", "Query must be UTF-8 representable.") from error
    if any((ord(char) < 32 and char not in "\t\n\r") or ord(char) == 127 for char in query):
        raise InventoryError("invalid_arguments", "Query contains unsupported control characters.")
    terms = sorted(set(query.casefold().split()))
    if len(terms) > 16:
        raise InventoryError("invalid_arguments", "Use at most 16 distinct whitespace-separated terms.")
    return terms


def _read_text(root, entry):
    """Bound a source read and compare exact bytes and ordinary path observations."""
    path = root / entry["path"]

    def parents():
        current = root
        for part in Path(entry["path"]).parts[:-1]:
            current /= part
            if _is_link(current) or not current.is_dir():
                raise ChangedDuringCapture()

    try:
        parents()
        before = path.lstat()
        if _is_link(path) or not stat.S_ISREG(before.st_mode):
            raise ChangedDuringCapture()
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(path, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            if _token(opened) != _token(before):
                raise ChangedDuringCapture()
            data = stream.read(MAX_FILE_BYTES + 1)
            if _token(os.fstat(stream.fileno())) != _token(opened):
                raise ChangedDuringCapture()
        parents()
        if _is_link(path) or _token(path.lstat()) != _token(opened):
            raise ChangedDuringCapture()
        if len(data) != entry["bytes"] or "sha256:" + hashlib.sha256(data).hexdigest() != entry["content_id"]:
            raise ChangedDuringCapture()
        if b"\x00" in data:
            return None, "nul_bytes"
        try:
            return data.decode("utf-8"), None
        except UnicodeError:
            return None, "not_utf8"
    except FileNotFoundError as error:
        raise ChangedDuringCapture() from error
    except OSError as error:
        raise InventoryError("unreadable_input", f"Cannot read context source {entry['path']}: {error}") from error


def _prefix(text, budget):
    return text.encode("utf-8")[:budget].decode("utf-8", errors="ignore")


def _excerpt(text, matched_lines):
    if not text:
        return None
    # Lines use LF delimiters; CR in CRLF stays in the exact excerpt bytes.
    parts = text.split("\n")
    lines = [part + ("\n" if index < len(parts) - 1 else "") for index, part in enumerate(parts)]
    if lines[-1] == "":
        lines.pop()
    center = matched_lines[0] - 1 if matched_lines else 0
    start, end = max(0, center - 2), min(len(lines), center + 3)
    window = "".join(lines[start:end])
    excerpt = _prefix(window, MAX_EXCERPT_BYTES)
    start_byte = sum(len(line.encode("utf-8")) for line in lines[:start])
    return {"text": excerpt, "start_byte": start_byte,
            "end_byte": start_byte + len(excerpt.encode("utf-8")), "start_line": start + 1,
            "end_line": start + 1 + excerpt.count("\n") - int(excerpt.endswith("\n")),
            "window_end_byte": start_byte + len(window.encode("utf-8")),
            "truncated": excerpt != window}


def _search(root, captured, terms, selection):
    entries = captured.manifest["entries"]
    by_path = {entry["path"]: entry for entry in entries}
    if selection not in by_path or by_path[selection]["kind"] == "boundary":
        raise InventoryError("invalid_selection", "Select an included file or directory; boundaries cannot be searched.")
    files = [entry for entry in entries if entry["kind"] == "file" and
             (selection == "." or entry["path"] == selection or entry["path"].startswith(selection + "/"))]
    matches, gaps = [], []
    for entry in files:
        text, reason = (None, "file_too_large") if entry["bytes"] > MAX_FILE_BYTES else _read_text(root, entry)
        path_terms = [term for term in terms if term in entry["path"].casefold()]
        folded = None if text is None else text.casefold()
        content_terms = [term for term in terms if folded is not None and term in folded]
        if reason:
            gaps.append({"path": entry["path"], "reason": reason, "content_id": entry["content_id"]})
        if not path_terms and not content_terms:
            continue
        matched_lines = [] if text is None else [index + 1 for index, line in
                                               enumerate(part.casefold() for part in text.split("\n"))
                                               if any(term in line for term in terms)]
        matches.append({**_classification(entry), "match": {"origin": "literal_search", "path_terms": path_terms,
                         "content_terms": content_terms, "distinct_terms": len(set(path_terms + content_terms)),
                         "first_content_line": matched_lines[0] if matched_lines else None,
                         "matching_lines_total": len(matched_lines)},
                        "text_status": reason or "searched_utf8", "excerpt": None if text is None else _excerpt(text, matched_lines)})
    matches.sort(key=lambda item: (-item["match"]["distinct_terms"], item["path"]))
    return matches, gaps, len(files)


def task_context(root: Path, query, *, selection=".", limit=10, offset=0,
                 max_bytes=8192, expected_snapshot=None):
    """Retrieve literals between matching full captures; no semantics or source writes."""
    terms = _terms(query)
    relative_path(selection, root_allowed=True)
    if type(limit) is not int or not 1 <= limit <= 50 or type(offset) is not int or offset < 0 or \
            type(max_bytes) is not int or not 128 <= max_bytes <= 65536:
        raise InventoryError("invalid_arguments", "Use limit 1..50, nonnegative offset, and max-bytes 128..65536.")
    if expected_snapshot is not None and (not isinstance(expected_snapshot, str) or
            len(expected_snapshot) != 71 or not expected_snapshot.startswith("sha256:") or
            any(char not in "0123456789abcdef" for char in expected_snapshot[7:])):
        raise InventoryError("invalid_arguments", "Expected snapshot must be a lowercase SHA-256 identity.")
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
                search_error = None
                try:
                    matches, gaps, files_total = _search(root, first, terms, selection)
                except InventoryError as error:
                    search_error = error
                second = capture(root, rules)
                if first != second:
                    continue
                if search_error:
                    raise search_error
                break
            except ChangedDuringCapture:
                continue
        else:
            raise InventoryError("unstable_inputs", "Inputs changed during context retrieval; retry when stable.")
    finally:
        rules.close()
    snapshot = identity(second.manifest)
    if expected_snapshot is not None and snapshot != expected_snapshot:
        raise InventoryError("stale_snapshot", "Current inputs differ from the expected snapshot; request a fresh first page.")
    verified = datetime.now(timezone.utc).isoformat()
    result = {"format": FORMAT, "status": "ok", "snapshot": snapshot,
              "manifest": second.manifest, "observation": {"root": str(root), "started_at": started,
              "verified_at": verified, "freshness": "matching_captures_around_context_reads", "atomic": False}}
    structure = view(result, selection=selection, limit=20)
    shown = matches[offset:offset + limit]
    remaining = max_bytes
    for item in shown:
        item["evidence"] = {"snapshot": snapshot, "path": item["path"], "content_id": item["content_id"]}
        excerpt = item["excerpt"]
        if excerpt is not None:
            text = _prefix(excerpt["text"], remaining)
            if not text:
                item["excerpt"] = None
                item["text_status"] = "excerpt_budget_exhausted"
                continue
            used = len(text.encode("utf-8"))
            remaining -= used
            excerpt.update(text=text, end_byte=excerpt["start_byte"] + used,
                           end_line=excerpt["start_line"] + text.count("\n") - int(text.endswith("\n")),
                           truncated=excerpt["start_byte"] + used < excerpt["window_end_byte"])
    ancestors = set()
    for item in shown:
        current = item["path"]
        while current != ".":
            ancestors.add(current)
            current = current.rpartition("/")[0] or "."
    # All ancestor edges stay in the snapshot. Bound their transport separately.
    paths = sorted(ancestors)
    boundaries = [entry for entry in second.manifest["entries"] if entry["kind"] == "boundary"]
    edges = [{"kind": "contains", "from": path.rpartition("/")[0] or ".", "to": path,
              "origin": "inventory", "evidence": {"snapshot": snapshot, "path": path}} for path in paths[:200]]
    return {key: value for key, value in result.items() if key != "manifest"} | {
        "retriever": RETRIEVER, "unicode_version": unicodedata.unidata_version, "project": structure["project"],
        "selection": {"path": selection, "query": query, "terms": terms, "limit": limit,
                      "offset": offset, "order": "distinct_terms_descending_then_path"},
        "matches": {"total": len(matches), "omitted": len(matches) - len(shown), "entries": shown,
                    "next_offset": offset + len(shown) if offset + len(shown) < len(matches) else None},
        "excerpt_budget": {"max_bytes": max_bytes, "used_bytes": max_bytes - remaining,
                           "unit": "utf8_source_text_only", "per_file_max_bytes": MAX_EXCERPT_BYTES},
        "relationships": {"total": len(paths), "omitted": max(0, len(paths) - 200), "entries": edges},
        "outline": structure["outline"], "guidance": structure["guidance"],
        "document_links": structure["document_links"], "exclusions": structure["exclusions"],
        "boundaries": {"total": len(boundaries), "omitted": max(0, len(boundaries) - 20), "entries": boundaries[:20]},
        "coverage": {"semantics": "unknown", "change_impact": "not_established", "purpose": "not_inferred",
                     "model_calls": 0, "files_in_selection": files_total, "text_searched": files_total - len(gaps),
                     "file_bytes_limit": MAX_FILE_BYTES, "gap_counts": dict(sorted(Counter(item["reason"] for item in gaps).items())),
                     "gaps": {"total": len(gaps), "omitted": max(0, len(gaps) - 20), "entries": gaps[:20]},
                     "inventory": structure["coverage"], "source_text": "untrusted_project_data"},
    }
