"""Reproducible local inventory cost baseline; no model or source writes."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from tempfile import TemporaryDirectory, gettempdir
from time import perf_counter_ns, process_time_ns

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from universal_ir.cache import cache_snapshot
from universal_ir.inventory import EXTRACTOR, FORMAT, InventoryError, identity, inventory, view


REPORT_FORMAT = "uir.inventory-cost.v1"


def tool_sources() -> dict:
    tool = Path(__file__).resolve().parents[1]
    files = [*sorted((tool / "universal_ir").glob("*.py")), Path(__file__).resolve()]
    return {path.relative_to(tool).as_posix(): "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files}


def sample(root: Path, cache_dir: Path | None = None) -> dict:
    start, cpu = perf_counter_ns(), process_time_ns()
    timings = {}
    try:
        phase = perf_counter_ns()
        result = inventory(root)
        timings["inventory_with_freshness_ns"] = perf_counter_ns() - phase
        valid = identity(result["manifest"]) == result["snapshot"]
        phase = perf_counter_ns()
        if cache_dir is not None:
            result = cache_snapshot(result, cache_dir)
        timings["cache_total_ns"] = perf_counter_ns() - phase if cache_dir is not None else 0
        phase = perf_counter_ns()
        output = view(result)
        timings["view_ns"] = perf_counter_ns() - phase
        phase = perf_counter_ns()
        encoded = (json.dumps(output, ensure_ascii=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
        timings["json_encoding_ns"] = perf_counter_ns() - phase
        files = [entry for entry in result["manifest"]["entries"] if entry["kind"] == "file"]
        artifact = result.get("cache", {}).get("artifact")
        stored = Path(artifact).stat().st_size if artifact and Path(artifact).is_file() else 0
        return {"status": "ok", "snapshot": result["snapshot"], "manifest_identity_valid": valid,
                "ignore_engine": result["manifest"]["ignore_engine"],
                "included_files": len(files), "included_file_bytes": sum(entry["bytes"] for entry in files),
                "context_json_bytes": len(encoded), "cache": result.get("cache"),
                "artifact_bytes": stored, "timings": timings,
                "worker_wall_ns": perf_counter_ns() - start,
                "worker_cpu_ns_excluding_git": process_time_ns() - cpu}
    except (InventoryError, OSError) as error:
        return {"status": "error", "error": {"code": getattr(error, "code", "measurement_io_failure"),
                "message": str(error)}, "timings": timings,
                "worker_wall_ns": perf_counter_ns() - start,
                "worker_cpu_ns_excluding_git": process_time_ns() - cpu}


def fixture(root: Path):
    root.mkdir()
    (root / "README.md").write_bytes(b"# Synthetic inventory fixture\n")
    (root / "AGENTS.md").write_bytes(b"# Fixture guidance\n")
    (root / ".gitignore").write_bytes(b"vendor/\n")
    for number in range(100):
        directory = root / f"part-{number // 10:02d}"
        directory.mkdir(exist_ok=True)
        suffix = ("py", "ts", "rs", "sql")[number % 4]
        (directory / f"item-{number:03d}.{suffix}").write_bytes(
            (f"opaque fixture input {number:03d}\n" * 32).encode("utf-8"))
    (root / "vendor").mkdir()
    (root / "vendor/ignored.bin").write_bytes(b"excluded" * 1024)


def invoke(root: Path, cache_dir: Path | None) -> dict:
    arguments = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", "--root", str(root)]
    if cache_dir is not None:
        arguments.extend(["--cache-dir", str(cache_dir)])
    start = perf_counter_ns()
    try:
        completed = subprocess.run(arguments, capture_output=True, timeout=120)
        if completed.returncode or completed.stderr:
            return {"status": "error", "error": {"code": "worker_failed",
                    "message": completed.stderr.decode("utf-8", errors="replace"),
                    "exit": completed.returncode}, "process_wall_ns": perf_counter_ns() - start}
        result = json.loads(completed.stdout)
        result["process_wall_ns"] = perf_counter_ns() - start
        return result
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        return {"status": "error", "error": {"code": "worker_failed", "message": str(error)},
                "process_wall_ns": perf_counter_ns() - start}


def comparison(samples: list[dict]) -> str:
    if any(item["status"] != "ok" or not item["manifest_identity_valid"] for item in samples):
        return "failed_sample"
    if len({item["snapshot"] for item in samples}) != 1:
        return "not_comparable_inputs_changed"
    cold, warm = samples[1]["cache"], samples[2]["cache"]
    if cold.get("lookup") != "miss" or cold.get("publication") != "stored" or \
            warm.get("lookup") != "hit" or warm.get("publication") != "reused":
        return "cache_expectation_failed"
    return "matching_inventory_identities_and_expected_cache_states"


def measure(root: Path | None, repetitions: int) -> dict:
    if not 1 <= repetitions <= 20:
        raise ValueError("repetitions must be 1..20")
    if root is not None:
        root = root.resolve()
        if not root.is_dir() or Path(gettempdir()).resolve().is_relative_to(root):
            raise ValueError("Select an existing project that does not contain the system temporary directory.")
    sources = tool_sources()
    trials = []
    with TemporaryDirectory(prefix="uir-cost-") as temporary:
        scratch = Path(temporary)
        if root is None:
            root = scratch / "fixture"
            fixture(root)
            corpus = "synthetic_100_opaque_mixed_extension_files_plus_guidance_and_ignore"
        else:
            corpus = "user_selected_project"
        for number in range(repetitions):
            cache_dir = scratch / f"cache-{number}"
            samples = [invoke(root, None), invoke(root, cache_dir), invoke(root, cache_dir)]
            for mode, result in zip(("uncached", "cold_cache", "warm_cache"), samples):
                result["mode"] = mode
            trials.append({"trial": number + 1, "comparison": comparison(samples), "samples": samples})
        for trial in trials:
            for result in trial["samples"]:
                cache = result.get("cache")
                if cache and "artifact" in cache:
                    cache["artifact"] = "<temporary workspace>/" + Path(cache["artifact"]).relative_to(scratch).as_posix()
        summary = {}
        for mode in ("uncached", "cold_cache", "warm_cache"):
            values = [sample["process_wall_ns"] for trial in trials for sample in trial["samples"]
                      if sample["mode"] == mode and sample["status"] == "ok"]
            summary[mode] = {"successful_samples": len(values), "median_process_wall_ns":
                             statistics.median(values) if values else None}
    return {"format": REPORT_FORMAT, "recorded_at": datetime.now(timezone.utc).isoformat(),
            "tool_source_id": identity(sources), "tool_source_files": sources,
            "tool_source_unchanged": sources == tool_sources(),
            "inventory_format": FORMAT, "extractor": EXTRACTOR,
            "python": platform.python_version(), "platform": platform.platform(), "corpus": corpus,
            "repetitions": repetitions, "order": ["uncached", "cold_cache", "warm_cache"],
            "model_calls": 0, "network_transfer_bytes": 0,
            "unmeasured": ["git_child_cpu", "peak_memory", "separate_extraction_and_verification",
                           "separate_cache_read_validation_and_write", "model_tokens", "agent_task_success",
                           "repair_attempts", "review_effort"],
            "cold_meaning": "empty_tool_cache_not_cold_os_filesystem_cache",
            "summary": summary, "trials": trials}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="Optional project; default is a fixed synthetic fixture")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--cache-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.worker:
            if args.root is None:
                raise ValueError("worker requires root")
            result = sample(args.root, args.cache_dir)
        else:
            if args.cache_dir is not None:
                raise ValueError("cache-dir is an internal worker option")
            result = measure(args.root, args.repetitions)
        print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
        if args.worker:
            return 0
        return 0 if result["tool_source_unchanged"] and all(trial["comparison"] == "matching_inventory_identities_and_expected_cache_states"
                        for trial in result["trials"]) else 1
    except (ValueError, OSError) as error:
        print(json.dumps({"format": REPORT_FORMAT, "status": "error", "message": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
