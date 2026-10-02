"""Optional local snapshot storage; fresh inventory remains authoritative."""

import os
from pathlib import Path
import stat
from tempfile import mkstemp
from time import sleep

from .inventory import canonical, identity, parse_json


CACHE_FORMAT = "uir.local-cache.v1"
NAMESPACE = "uir-inventory-cache-v1"


class CacheUnavailable(Exception):
    pass


def _check_directories(path: Path):
    """Reject existing links/junctions and non-directory path components."""
    for part in reversed((path, *path.parents)):
        if part.is_symlink() or part.is_junction():
            raise CacheUnavailable(f"Cache directories cannot cross a link or junction: {part}")
        if os.path.lexists(part) and not part.is_dir():
            raise CacheUnavailable(f"Cache parent must be a directory: {part}")


def _check_artifact(path: Path):
    if path.is_symlink() or path.is_junction():
        raise CacheUnavailable(f"Cache artifact cannot be a link or junction: {path}")
    if os.path.lexists(path) and not stat.S_ISREG(path.lstat().st_mode):
        raise CacheUnavailable(f"Cache artifact must be a regular file: {path}")


def _location(directory: Path, root: Path) -> Path:
    # Check the lexical path before resolving it, so resolution cannot hide links.
    base = Path(os.path.abspath(directory))
    _check_directories(base)
    base = base.resolve()
    namespace = base / NAMESPACE
    if base.is_relative_to(root) or root.is_relative_to(namespace):
        raise CacheUnavailable("Select a cache directory outside the inventoried project; it cannot contain the project in its cache namespace.")
    _check_directories(namespace)
    return namespace


def _lookup(path: Path, expected: dict, encoded: bytes):
    _check_directories(path.parent)
    _check_artifact(path)
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) |
                             getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        return "miss", None
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise CacheUnavailable("Cache artifact is not a regular file.")
        # Bound untrusted cache input by the freshly established manifest size.
        bound = len(encoded) * 2 + 4096
        data = stream.read(bound + 1)
    if len(data) > bound:
        return "corrupt", None
    try:
        candidate = parse_json(data)
        if not isinstance(candidate, dict) or not isinstance(candidate.get("format"), str):
            return "corrupt", None
        if candidate["format"] != CACHE_FORMAT:
            return "incompatible", None
        if set(candidate) != {"format", "snapshot", "manifest"}:
            return "corrupt", None
        if candidate["snapshot"] != expected["snapshot"] or identity(candidate["manifest"]) != expected["snapshot"]:
            return "corrupt", None
        # A self-consistent digest is insufficient: compare against local facts.
        if canonical(candidate) != canonical(expected):
            return "corrupt", None
        return "hit", candidate["manifest"]
    except (ValueError, UnicodeError, TypeError):
        return "corrupt", None


def _matches_existing(path: Path, encoded: bytes) -> bool:
    _check_artifact(path)
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) |
                             getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        return False
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise CacheUnavailable("Cache artifact is not a regular file.")
        return stream.read(len(encoded) + 1) == encoded


def _publish(path: Path, encoded: bytes):
    """Publish a whole artifact; interrupted temporary files are never read."""
    _check_directories(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    _check_directories(path.parent)
    temporary = None
    try:
        descriptor, name = mkstemp(prefix=".pending-", suffix=".tmp", dir=path.parent)
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        _check_directories(path.parent)
        for attempt in range(4):
            try:
                # Another identical writer may have finished since lookup.
                # Leave accepted bytes in place rather than replace readers' file.
                if _matches_existing(path, encoded):
                    return
                os.replace(temporary, path)
                return
            except PermissionError as error:
                # Windows can briefly deny replacement while a reader is open.
                # Persistent permission failures still become cache diagnostics.
                if getattr(error, "winerror", None) not in {5, 32, 33} or attempt == 3:
                    raise
                sleep(0.05)
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                # A leftover private temporary file is not an accepted snapshot.
                pass


def cache_snapshot(result: dict, directory: Path) -> dict:
    """Persist/reuse only an already successful fresh local inventory result.

    Internal core adapter, not a public SDK or snapshot-import interface. Cache
    failures annotate the fresh result; they never authorize stale fallback.
    """
    expected = {"format": CACHE_FORMAT, "snapshot": result["snapshot"],
                "manifest": result["manifest"]}
    encoded = canonical(expected) + b"\n"
    report = {"format": CACHE_FORMAT, "lookup": "unavailable",
              "publication": "not_attempted", "verification": "full_local_capture"}
    output = {**result, "cache": report}
    phase = "prepare"
    try:
        directory = _location(directory, Path(result["observation"]["root"]))
        artifact = directory / (result["snapshot"].removeprefix("sha256:") + ".json")
        report["artifact"] = str(artifact)
        phase = "lookup"
        state, manifest = _lookup(artifact, expected, encoded)
        report["lookup"] = state
        if state == "hit":
            output["manifest"] = manifest
            report["publication"] = "reused"
        else:
            phase = "publication"
            _publish(artifact, encoded)
            report["publication"] = "stored"
    except (OSError, RuntimeError, ValueError, CacheUnavailable) as error:
        if phase == "publication":
            report["publication"] = "unavailable"
        report["diagnostic"] = {"code": "cache_unavailable", "phase": phase,
                                "message": str(error)}
    return output
