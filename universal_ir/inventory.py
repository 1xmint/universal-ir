"""Deterministic local inventory, independent of the terminal adapter."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from tempfile import TemporaryDirectory, gettempdir


FORMAT = "uir.inventory.v1"
EXTRACTOR = "inventory.v1"
CONFIG_PATH = ".uir/config/project.json"
DEFAULT_CONFIG = {"version": 1, "project_id": None, "exclude": [], "documents": []}
LANGUAGES = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".rs": "Rust",
    ".go": "Go", ".java": "Java", ".c": "C", ".h": "C/C++",
    ".cpp": "C++", ".cs": "C#", ".rb": "Ruby", ".php": "PHP",
    ".swift": "Swift", ".kt": "Kotlin", ".sql": "SQL", ".sh": "Shell",
    ".md": "Markdown", ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML", ".html": "HTML", ".css": "CSS",
}
GUIDANCE_NAMES = {"readme.md", "agents.md", "contributing.md", "security.md"}


class InventoryError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ChangedDuringCapture(Exception):
    pass


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def identity(value) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"non-finite JSON value: {value}")


def parse_json(data: bytes):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=_reject_constant)
    except RecursionError as error:
        raise ValueError("JSON nesting exceeds the supported decoder depth") from error


def relative_path(value, *, root_allowed=False) -> str:
    if root_allowed and value == ".":
        return value
    if not isinstance(value, str) or not value or any(
        char in value for char in "\\:*?[]"
    ) or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise InventoryError("invalid_path", "Use a literal relative path with '/' separators.")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise InventoryError("invalid_path", "Absolute, empty, '.' and '..' path segments are unsupported.")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise InventoryError("unsupported_path", "Path names must be representable as UTF-8.") from error
    return value


def validate_config(value, *, default=False):
    if not isinstance(value, dict) or set(value) != set(DEFAULT_CONFIG):
        raise InventoryError("invalid_configuration", "Configuration needs exactly version, project_id, exclude, documents.")
    if type(value["version"]) is not int or value["version"] != 1:
        raise InventoryError("invalid_configuration", "Only configuration version 1 is supported.")
    project = value["project_id"]
    if not (default and project is None) and (
        not isinstance(project, str) or not project.strip()
    ):
        raise InventoryError("invalid_configuration", "project_id must be a nonempty string.")
    if isinstance(project, str):
        try:
            project.encode("utf-8")
        except UnicodeError as error:
            raise InventoryError("invalid_configuration", "project_id must be representable as UTF-8.") from error
    for field in ("exclude", "documents"):
        paths = value[field]
        if not isinstance(paths, list):
            raise InventoryError("invalid_configuration", f"{field} must be a list.")
        for path in paths:
            relative_path(path)
        if len(paths) != len(set(paths)):
            raise InventoryError("invalid_configuration", f"{field} cannot contain duplicate paths.")


def _token(info):
    # Windows path and handle APIs can report different ctime values; it is
    # historically creation time there, not the POSIX metadata-change clock.
    return (info.st_mode, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns if os.name != "nt" else None,
            info.st_dev, info.st_ino)


def _is_link(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def _read_file(path: Path):
    """Hash exact bytes and detect ordinary replacement/edit during reading."""
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or _is_link(path):
            raise ChangedDuringCapture()
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if _token(opened) != _token(before):
                raise ChangedDuringCapture()
            digest = hashlib.sha256()
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
            after = os.fstat(stream.fileno())
        if _token(before) != _token(after) or _token(path.lstat()) != _token(after):
            raise ChangedDuringCapture()
        return "sha256:" + digest.hexdigest(), after.st_size, _token(after)
    except FileNotFoundError as error:
        raise ChangedDuringCapture() from error
    except OSError as error:
        raise InventoryError("unreadable_input", f"Cannot read {path}: {error}") from error


class IgnoreRules:
    """Git's evaluator, isolated from user/project Git configuration."""

    def __init__(self, root: Path):
        self.root = root
        self.environment = {key: value for key, value in os.environ.items()
                            if not key.startswith("GIT_")}
        self.environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        if Path(gettempdir()).resolve().is_relative_to(root):
            raise InventoryError("invalid_root", "Select a project that does not contain the system temporary directory.")
        self.temporary = TemporaryDirectory(prefix="uir-ignore-")
        try:
            directory = Path(self.temporary.name)
            self._run(["init", "--quiet", "--template=", str(directory)])
            version = self._run(["--version"]).stdout.decode("utf-8").strip()
            match = re.search(r"\d+\.\d+\.\d+", version)
            if not match:
                raise InventoryError("ignore_failure", "Cannot identify Git ignore-engine version.")
            self.version = "git-" + match.group()
            self.arguments = ["--git-dir=" + str(directory / ".git"),
                              "--work-tree=" + str(root), "-c", "core.ignorecase=false",
                              "-c", "core.excludesFile=" + os.devnull]
        except Exception:
            self.temporary.cleanup()
            raise

    def _run(self, arguments, data=None, accepted=(0,)):
        try:
            result = subprocess.run(["git", *arguments], cwd=self.root,
                                    env=self.environment, input=data, capture_output=True,
                                    timeout=30)
        except FileNotFoundError as error:
            raise InventoryError("missing_git", "Install Git and make it available on PATH.") from error
        except (OSError, subprocess.TimeoutExpired) as error:
            raise InventoryError("ignore_failure", f"Git ignore evaluation failed: {error}") from error
        if result.returncode not in accepted:
            raise InventoryError("ignore_failure", "Git ignore evaluation failed: " +
                                 result.stderr.decode("utf-8", errors="replace").strip())
        return result

    def excluded(self, paths: list[str]) -> set[str]:
        if not paths:
            return set()
        data = ("\0".join(paths) + "\0").encode("utf-8")
        result = self._run([*self.arguments, "check-ignore", "--no-index", "-z", "--stdin"],
                           data, accepted=(0, 1))
        return {path.rstrip("/") for path in result.stdout.decode("utf-8").split("\0") if path}

    def close(self):
        self.temporary.cleanup()


@dataclass
class Capture:
    manifest: dict
    tokens: dict


def capture(root: Path, rules: IgnoreRules) -> Capture:
    controls, tokens, entries, omissions = {}, {}, [], []
    config_file = root / CONFIG_PATH
    for part in (root / ".uir", root / ".uir/config", config_file):
        if _is_link(part):
            raise InventoryError("invalid_configuration", "Configuration path cannot cross a link or junction.")
        if os.path.lexists(part) and part != config_file and not part.is_dir():
            raise InventoryError("invalid_configuration", "Configuration parents must be directories.")
    if config_file.exists():
        if not config_file.is_file():
            raise InventoryError("invalid_configuration", "Configuration must be a regular JSON file.")
        digest, _, token = _read_file(config_file)
        try:
            config = parse_json(config_file.read_bytes())
        except FileNotFoundError as error:
            raise ChangedDuringCapture() from error
        except OSError as error:
            raise InventoryError("unreadable_input", f"Cannot read configuration: {error}") from error
        except (ValueError, UnicodeError) as error:
            raise InventoryError("invalid_configuration", f"Invalid configuration JSON: {error}") from error
        if _read_file(config_file)[0] != digest:
            raise ChangedDuringCapture()
        validate_config(config)
        controls[CONFIG_PATH] = digest
        tokens[CONFIG_PATH] = token
    else:
        config = dict(DEFAULT_CONFIG)

    def walk(directory: Path, name: str):
        try:
            directory_info = directory.lstat()
            children = sorted(directory.iterdir(), key=lambda path: path.name)
            tokens[name] = _token(directory_info)
            entries.append({"path": name, "kind": "directory", "parent":
                            None if name == "." else str(PurePosixPath(name).parent)})
            ignore_file = directory / ".gitignore"
            if not _is_link(ignore_file) and ignore_file.is_file():
                digest, _, token = _read_file(ignore_file)
                ignore_name = ignore_file.relative_to(root).as_posix()
                controls[ignore_name], tokens[ignore_name] = digest, token
            candidates = []
            for child in children:
                child_name = child.relative_to(root).as_posix()
                try:
                    relative_path(child_name)
                except InventoryError as error:
                    raise InventoryError("unsupported_path", f"Unsupported portable path {child_name!r}: {error}") from error
                if child.name == ".git" or child_name == ".uir/cache":
                    omissions.append({"path": child_name, "reason": "internal"})
                elif any(child_name == path or child_name.startswith(path + "/")
                         for path in config["exclude"]):
                    omissions.append({"path": child_name, "reason": "configuration"})
                else:
                    candidates.append(child)
            ignored = rules.excluded([path.relative_to(root).as_posix() +
                                      ("/" if not _is_link(path) and path.is_dir() else "")
                                      for path in candidates])
            for child in candidates:
                child_name = child.relative_to(root).as_posix()
                if child_name in ignored:
                    omissions.append({"path": child_name, "reason": "gitignore"})
                    continue
                info = child.lstat()
                parent = name
                if _is_link(child):
                    entries.append({"path": child_name, "kind": "boundary", "parent": parent,
                                    "reason": "link", "target": os.readlink(child)})
                    tokens[child_name] = _token(info)
                elif stat.S_ISDIR(info.st_mode):
                    if os.path.lexists(child / ".git"):
                        entries.append({"path": child_name, "kind": "boundary", "parent": parent,
                                        "reason": "nested_repository"})
                        tokens[child_name] = _token(info)
                    else:
                        walk(child, child_name)
                elif stat.S_ISREG(info.st_mode):
                    digest, size, token = _read_file(child)
                    entries.append({"path": child_name, "kind": "file", "parent": parent,
                                    "content_id": digest, "bytes": size})
                    tokens[child_name] = token
                else:
                    entries.append({"path": child_name, "kind": "boundary", "parent": parent,
                                    "reason": "special_file"})
                    tokens[child_name] = _token(info)
            if _token(directory.lstat()) != tokens[name]:
                raise ChangedDuringCapture()
        except FileNotFoundError as error:
            raise ChangedDuringCapture() from error
        except OSError as error:
            raise InventoryError("unreadable_input", f"Cannot inventory {directory}: {error}") from error

    walk(root, ".")
    manifest = {"format": FORMAT, "extractor": EXTRACTOR, "ignore_engine": rules.version,
                "configuration": config, "controls": controls,
                "entries": sorted(entries, key=lambda entry: entry["path"]),
                "omissions": sorted(omissions, key=lambda entry: entry["path"])}
    return Capture(manifest, tokens)


def inventory(root: Path) -> dict:
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
                first, second = capture(root, rules), capture(root, rules)
                if first == second:
                    return {"format": FORMAT, "status": "ok", "snapshot": identity(second.manifest),
                            "manifest": second.manifest, "observation": {
                                "root": str(root), "started_at": started,
                                "verified_at": datetime.now(timezone.utc).isoformat(),
                                "freshness": "verified_consecutive_captures",
                                "atomic": False}}
            except ChangedDuringCapture:
                continue
        raise InventoryError("unstable_inputs", "Inputs changed during capture; retry when stable or use a frozen tree.")
    finally:
        rules.close()


def _classification(entry):
    if entry["kind"] != "file":
        return entry
    path = PurePosixPath(entry["path"])
    role = "guidance" if path.name.lower() in GUIDANCE_NAMES else "unknown"
    return {**entry, "classification": {"origin": "hypothesis",
            "method": "filename_and_extension", "language": LANGUAGES.get(path.suffix.lower(), "unknown"),
            "role": role}}


def view(result: dict, *, selection=".", offset=0, limit=20, full=False) -> dict:
    relative_path(selection, root_allowed=True)
    if not 1 <= limit <= 200 or offset < 0:
        raise InventoryError("invalid_arguments", "limit must be 1..200 and offset must be nonnegative.")
    manifest = result["manifest"]
    all_entries = manifest["entries"]
    by_path = {entry["path"]: entry for entry in all_entries}
    if selection not in by_path or by_path[selection]["kind"] == "boundary":
        raise InventoryError("invalid_selection", "Select an included file or directory; boundaries cannot be expanded.")
    chosen = [entry for entry in all_entries if full or selection == "." or
              entry["path"] == selection or entry["path"].startswith(selection + "/")]
    shown = chosen if full else chosen[offset:offset + limit]
    edges = [{"kind": "contains", "from": entry["parent"], "to": entry["path"],
              "origin": "inventory", "evidence": {"snapshot": result["snapshot"],
              "path": entry["path"]}} for entry in shown if entry["parent"] is not None]
    documents = [{"kind": "document_link", "from": CONFIG_PATH, "to": path,
                  "origin": "configuration", "status": "resolved" if
                  path in by_path and by_path[path]["kind"] == "file" else "unresolved",
                  "evidence": {"snapshot": result["snapshot"], "path": CONFIG_PATH,
                               "content_id": manifest["controls"].get(CONFIG_PATH)}}
                 for path in manifest["configuration"]["documents"]]
    for link in documents:
        if link["status"] == "unresolved":
            target = link["to"]
            if target in by_path:
                link["reason"] = by_path[target]["kind"]
            elif any(target == item["path"] or target.startswith(item["path"] + "/")
                     for item in manifest["omissions"]):
                link["reason"] = "excluded"
            elif any(entry["kind"] == "boundary" and target.startswith(entry["path"] + "/")
                     for entry in all_entries):
                link["reason"] = "boundary"
            else:
                link["reason"] = "absent"
    outline = [{"path": entry["path"], "kind": entry["kind"]} for entry in all_entries
               if entry["parent"] == ("." if full else selection)]
    guidance = [{"path": entry["path"], "content_id": entry["content_id"],
                 "snapshot": result["snapshot"], "origin": "filename_hypothesis"}
                for entry in all_entries if entry["kind"] == "file" and
                PurePosixPath(entry["path"]).name.lower() in GUIDANCE_NAMES]
    omitted = len(chosen) - len(shown)
    output = {key: value for key, value in result.items() if key != "manifest" or full}
    output.update(coverage={"semantics": "unknown", "purpose": "not_inferred",
                           "ignore_scope": "root_and_nested_gitignore_plus_configuration",
                           "private_and_global_git_excludes": "not_applied",
                           "counts": dict(Counter(entry["kind"] for entry in all_entries)),
                           "language_hypotheses": dict(sorted(Counter(
                               LANGUAGES.get(PurePosixPath(entry["path"]).suffix.lower(), "unknown")
                               for entry in all_entries if entry["kind"] == "file").items())),
                           "omitted_paths": len(manifest["omissions"]),
                           "model_calls": 0},
                  project={"id": manifest["configuration"]["project_id"],
                           "configuration": CONFIG_PATH if CONFIG_PATH in manifest["controls"] else None},
                  outline={"total": len(outline), "omitted": 0 if full else max(0, len(outline) - limit),
                           "entries": outline if full else outline[:limit]},
                  view={"selection": "." if full else selection, "offset": 0 if full else offset,
                        "total": len(chosen), "omitted": omitted,
                        "next_offset": offset + len(shown) if not full and offset + len(shown) < len(chosen) else None,
                        "entries": [_classification(entry) for entry in shown], "relationships": edges},
                  guidance={"total": len(guidance), "omitted": 0 if full else max(0, len(guidance) - limit),
                            "entries": guidance if full else guidance[:limit]},
                  document_links={"total": len(documents), "omitted": 0 if full else max(0, len(documents) - limit),
                                  "entries": documents if full else documents[:limit]},
                  exclusions={"total": len(manifest["omissions"]),
                              "omitted": 0 if full else max(0, len(manifest["omissions"]) - limit), "entries":
                              manifest["omissions"] if full else manifest["omissions"][:limit]})
    return output


def load_baseline(path: Path) -> dict:
    try:
        result = parse_json(path.read_bytes())
        manifest = result["manifest"]
        if result["format"] != FORMAT or result["status"] != "ok" or manifest["format"] != FORMAT:
            raise ValueError("unsupported result format")
        if set(manifest) != {"format", "extractor", "ignore_engine", "configuration", "controls", "entries", "omissions"}:
            raise ValueError("unexpected manifest fields")
        if manifest["extractor"] != EXTRACTOR or not isinstance(manifest["ignore_engine"], str):
            raise ValueError("unsupported extractor")
        validate_config(manifest["configuration"], default=True)
        if not isinstance(manifest["controls"], dict) or not isinstance(manifest["omissions"], list):
            raise ValueError("invalid control inputs or omissions")
        for control, digest in manifest["controls"].items():
            relative_path(control)
            if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                raise ValueError("invalid control digest")
        entries = manifest["entries"]
        if not isinstance(entries, list) or not entries:
            raise ValueError("missing entries")
        names = []
        for entry in entries:
            relative_path(entry["path"], root_allowed=True)
            names.append(entry["path"])
            kind = entry["kind"]
            required = {"path", "kind", "parent"}
            if kind == "file":
                required |= {"content_id", "bytes"}
                if not re.fullmatch(r"sha256:[0-9a-f]{64}", entry["content_id"]) or type(entry["bytes"]) is not int or entry["bytes"] < 0:
                    raise ValueError("invalid file identity")
            elif kind == "boundary":
                required |= {"reason"}
                if entry["reason"] == "link":
                    required |= {"target"}
                    if not isinstance(entry["target"], str):
                        raise ValueError("invalid link target")
                elif entry["reason"] not in {"special_file", "nested_repository"}:
                    raise ValueError("invalid boundary")
            elif kind != "directory":
                raise ValueError("invalid entry kind")
            if set(entry) != required:
                raise ValueError("invalid entry fields")
            expected_parent = None if entry["path"] == "." else str(PurePosixPath(entry["path"]).parent)
            if entry["parent"] != expected_parent:
                raise ValueError("invalid containment")
        root_entries = [entry for entry in entries if entry["path"] == "."]
        if names != sorted(set(names)) or len(root_entries) != 1 or root_entries[0]["kind"] != "directory":
            raise ValueError("entries must be unique, sorted and rooted")
        directories = {entry["path"] for entry in entries if entry["kind"] == "directory"}
        if any(entry["parent"] is not None and entry["parent"] not in directories for entry in entries):
            raise ValueError("unresolved containment")
        omitted_names = []
        for omission in manifest["omissions"]:
            relative_path(omission["path"])
            if set(omission) != {"path", "reason"} or omission["reason"] not in {"internal", "configuration", "gitignore"}:
                raise ValueError("invalid omission")
            omitted_names.append(omission["path"])
        if omitted_names != sorted(set(omitted_names)):
            raise ValueError("omissions must be unique and sorted")
        if identity(manifest) != result["snapshot"]:
            raise ValueError("snapshot identity does not match manifest")
        return result
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, InventoryError) as error:
        raise InventoryError("invalid_baseline", f"Cannot use baseline: {error}") from error


def compare(previous: dict, current: dict, *, limit=20, full=False) -> dict:
    old, new = previous["manifest"], current["manifest"]
    if old["extractor"] != new["extractor"] or old["ignore_engine"] != new["ignore_engine"]:
        raise InventoryError("incompatible_baseline", "Baseline extractor and Git ignore versions must match.")
    before = {entry["path"]: entry for entry in old["entries"]}
    after = {entry["path"]: entry for entry in new["entries"]}
    changes = [{"path": path, "change": "added" if path not in before else
                "removed" if path not in after else "changed"}
               for path in sorted(before.keys() | after.keys()) if before.get(path) != after.get(path)]
    return {"previous_snapshot": previous["snapshot"], "current_snapshot": current["snapshot"],
            "configuration_changed": old["configuration"] != new["configuration"],
            "control_inputs_changed": old["controls"] != new["controls"],
            "meaning": "inventory_inputs_only_not_semantic_impact_or_physical_deletion",
            "total": len(changes), "omitted": 0 if full else max(0, len(changes) - limit),
            "changes": changes if full else changes[:limit]}
