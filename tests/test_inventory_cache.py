"""Local cache correctness, recovery, and preservation checks."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
import copy
import errno
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from universal_ir.__main__ import main
from universal_ir.cache import CACHE_FORMAT, NAMESPACE, _publish, cache_snapshot
from universal_ir.inventory import InventoryError, canonical, identity, inventory


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix="uir-cache-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.source = self.root / "main.py"
        self.source.write_bytes(b"print(1)\n")
        self.store = self.base / "cache"

    def run_cache(self, root=None):
        return cache_snapshot(inventory(root or self.root), self.store)

    def cli(self, *extra):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(["inventory", str(self.root), *extra])
        return status, stdout.getvalue(), stderr.getvalue()

    def test_cold_warm_and_disabled_preserve_source_and_identity(self):
        before = inventory(self.root)
        cold = self.run_cache()
        artifact = Path(cold["cache"]["artifact"])
        stored = artifact.read_bytes()
        stamp = artifact.stat().st_mtime_ns
        warm = self.run_cache()
        self.assertEqual(cold["cache"]["lookup"], "miss")
        self.assertEqual(cold["cache"]["publication"], "stored")
        self.assertEqual(warm["cache"]["lookup"], "hit")
        self.assertEqual(warm["cache"]["publication"], "reused")
        self.assertEqual(before["snapshot"], warm["snapshot"])
        self.assertNotEqual(cold["observation"]["verified_at"], warm["observation"]["verified_at"])
        self.assertEqual(stored, artifact.read_bytes())
        self.assertEqual(stamp, artifact.stat().st_mtime_ns)
        self.assertEqual(list(self.root.iterdir()), [self.source])
        self.assertEqual(self.source.read_bytes(), b"print(1)\n")
        envelope = json.loads(stored)
        self.assertEqual(set(envelope), {"format", "snapshot", "manifest"})
        status, output, errors = self.cli("--full")
        self.assertEqual((status, errors), (0, ""))
        self.assertNotIn("cache", json.loads(output))

    def test_restart_reads_bytes_even_with_restored_size_and_mtime(self):
        first = self.run_cache()
        info = self.source.stat()
        self.source.write_bytes(b"print(2)\n")
        os.utime(self.source, ns=(info.st_atime_ns, info.st_mtime_ns))
        second = self.run_cache()
        self.assertNotEqual(first["snapshot"], second["snapshot"])
        self.assertEqual(second["cache"]["lookup"], "miss")
        self.assertEqual(second["cache"]["verification"], "full_local_capture")

    def test_restart_detects_additions_deletions_configuration_and_ignore_changes(self):
        results = [self.run_cache()]
        added = self.root / "new.ts"
        added.write_bytes(b"export {}\n")
        results.append(self.run_cache())
        self.source.unlink()
        results.append(self.run_cache())
        config = self.root / ".uir/config/project.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({"version": 1, "project_id": "demo", "exclude": [], "documents": []}), encoding="utf-8")
        results.append(self.run_cache())
        (self.root / ".gitignore").write_bytes(b"new.ts\n")
        results.append(self.run_cache())
        self.assertEqual(len({item["snapshot"] for item in results}), 5)
        self.assertTrue(all(item["cache"]["lookup"] == "miss" for item in results))
        self.assertNotIn("new.ts", [item["path"] for item in results[-1]["manifest"]["entries"]])

    def test_deleted_artifact_reconstructs_and_old_snapshots_remain_available(self):
        first = self.run_cache()
        old = Path(first["cache"]["artifact"])
        self.source.write_bytes(b"print(2)\n")
        second = self.run_cache()
        self.assertTrue(old.is_file())
        Path(second["cache"]["artifact"]).unlink()
        rebuilt = self.run_cache()
        self.assertEqual(rebuilt["snapshot"], second["snapshot"])
        self.assertEqual(rebuilt["cache"]["lookup"], "miss")
        self.source.write_bytes(b"print(1)\n")
        self.assertEqual(self.run_cache()["cache"]["lookup"], "hit")

    def test_identical_checkouts_can_reuse_facts_without_observation_attribution(self):
        first = self.run_cache()
        other = self.base / "other"
        other.mkdir()
        (other / "main.py").write_bytes(self.source.read_bytes())
        second = self.run_cache(other)
        self.assertEqual(second["cache"]["lookup"], "hit")
        self.assertEqual(first["snapshot"], second["snapshot"])
        self.assertEqual(second["observation"]["root"], str(other.resolve()))

    def test_corrupt_or_incompatible_regular_artifacts_rebuild(self):
        first = self.run_cache()
        artifact = Path(first["cache"]["artifact"])
        valid = artifact.read_bytes()
        cases = [(b"{partial", "corrupt"), (b"\xff", "corrupt"),
                 (b'{"format":"uir.local-cache.v9"}', "incompatible"),
                 (b'{"format":"uir.local-cache.v1","format":"duplicate"}', "corrupt"),
                 (b" " * (len(valid) * 2 + 4097), "corrupt")]
        for data, expected in cases:
            with self.subTest(expected=expected, prefix=data[:30]):
                artifact.write_bytes(data)
                result = self.run_cache()
                self.assertEqual(result["cache"]["lookup"], expected)
                self.assertEqual(result["cache"]["publication"], "stored")
                self.assertEqual(artifact.read_bytes(), valid)

    def test_self_consistent_but_false_cached_facts_are_not_trusted(self):
        first = self.run_cache()
        artifact = Path(first["cache"]["artifact"])
        fabricated = json.loads(artifact.read_bytes())
        file_entry = next(item for item in fabricated["manifest"]["entries"] if item["kind"] == "file")
        file_entry["content_id"] = "sha256:" + "0" * 64
        fabricated["snapshot"] = identity(fabricated["manifest"])
        artifact.write_bytes(canonical(fabricated))
        result = self.run_cache()
        self.assertEqual(result["cache"]["lookup"], "corrupt")
        self.assertEqual(result["manifest"], first["manifest"])

    def test_current_extractor_and_scope_determine_lookup_identity(self):
        first = self.run_cache()
        with patch("universal_ir.inventory.EXTRACTOR", "inventory.future-test"):
            future = self.run_cache()
        self.assertEqual(future["cache"]["lookup"], "miss")
        self.assertNotEqual(future["snapshot"], first["snapshot"])
        self.assertTrue(Path(first["cache"]["artifact"]).is_file())

    def test_cache_inside_project_is_unavailable_without_creating_paths(self):
        before = inventory(self.root)
        for directory in (self.root, self.root / ".uir/cache", self.root / "new/cache"):
            result = cache_snapshot(before, directory)
            self.assertEqual(result["cache"]["lookup"], "unavailable")
            self.assertEqual(result["cache"]["diagnostic"]["phase"], "prepare")
        self.assertEqual(list(self.root.iterdir()), [self.source])

    def test_cache_namespace_containing_project_is_rejected(self):
        root = self.store / NAMESPACE / "project"
        root.mkdir(parents=True)
        result = cache_snapshot(inventory(root), self.store)
        self.assertEqual(result["cache"]["lookup"], "unavailable")
        self.assertEqual(list((self.store / NAMESPACE).iterdir()), [root])

    def test_non_directory_parent_and_special_artifact_are_not_overwritten(self):
        self.store.write_bytes(b"user-owned")
        result = self.run_cache()
        self.assertEqual(result["cache"]["diagnostic"]["phase"], "prepare")
        self.assertEqual(self.store.read_bytes(), b"user-owned")
        self.store.unlink()
        result = self.run_cache()
        artifact = Path(result["cache"]["artifact"])
        artifact.unlink()
        artifact.mkdir()
        result = self.run_cache()
        self.assertEqual(result["cache"]["lookup"], "unavailable")
        self.assertTrue(artifact.is_dir())

    def test_unreadable_cache_falls_back_to_fresh_result_without_publication(self):
        first = self.run_cache()
        with patch("universal_ir.cache._lookup", side_effect=PermissionError("denied")), \
                patch("universal_ir.cache._publish") as publish:
            result = self.run_cache()
        publish.assert_not_called()
        self.assertEqual(result["manifest"], first["manifest"])
        self.assertEqual(result["cache"]["diagnostic"]["phase"], "lookup")

    def test_interrupted_publication_preserves_existing_artifacts_and_cleans_own_temporary(self):
        first = self.run_cache()
        artifact = Path(first["cache"]["artifact"])
        previous = artifact.read_bytes()
        with patch("universal_ir.cache.os.replace", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                _publish(artifact, b"replacement\n")
        self.assertEqual(artifact.read_bytes(), previous)
        self.assertEqual(list(artifact.parent.glob(".pending-*.tmp")), [])
        self.source.write_bytes(b"print(2)\n")
        with patch("universal_ir.cache.os.replace", side_effect=OSError("interrupted")):
            result = self.run_cache()
        self.assertEqual(result["cache"]["publication"], "unavailable")
        self.assertEqual(result["cache"]["diagnostic"]["phase"], "publication")
        self.assertFalse(Path(result["cache"]["artifact"]).exists())
        self.assertEqual(artifact.read_bytes(), previous)
        self.assertEqual(self.run_cache()["cache"]["publication"], "stored")

    def test_failed_flush_does_not_publish_partial_file(self):
        with patch("universal_ir.cache.os.fsync", side_effect=OSError("disk failure")):
            result = self.run_cache()
        self.assertEqual(result["cache"]["publication"], "unavailable")
        self.assertFalse(Path(result["cache"]["artifact"]).exists())
        self.assertEqual(list((self.store / NAMESPACE).glob(".pending-*.tmp")), [])

    def test_abandoned_temporary_files_are_not_loaded_or_deleted(self):
        namespace = self.store / NAMESPACE
        namespace.mkdir(parents=True)
        abandoned = namespace / ".pending-crashed.tmp"
        abandoned.write_bytes(b"partial")
        result = self.run_cache()
        self.assertEqual(result["cache"]["lookup"], "miss")
        self.assertEqual(abandoned.read_bytes(), b"partial")

    def test_concurrent_identical_publication_is_idempotent(self):
        fresh = inventory(self.root)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: cache_snapshot(copy.deepcopy(fresh), self.store), range(8)))
        self.assertTrue(all(item["snapshot"] == fresh["snapshot"] for item in results))
        self.assertTrue(all("diagnostic" not in item["cache"] for item in results), results)
        self.assertEqual(self.run_cache()["cache"]["lookup"], "hit")
        self.assertEqual(len(list((self.store / NAMESPACE).glob("*.json"))), 1)

    def test_identical_completed_publication_is_not_replaced_again(self):
        first = self.run_cache()
        artifact = Path(first["cache"]["artifact"])
        with patch("universal_ir.cache.os.replace") as replace:
            _publish(artifact, artifact.read_bytes())
        replace.assert_not_called()
        self.assertEqual(list(artifact.parent.glob(".pending-*.tmp")), [])

    def test_windows_sharing_errors_retry_boundedly_and_persistent_failure_is_visible(self):
        sharing = PermissionError("reader still open")
        sharing.winerror = 32
        real_replace = os.replace
        calls = []

        def blocked_once(source, destination):
            calls.append(destination)
            if len(calls) == 1:
                raise sharing
            real_replace(source, destination)

        with patch("universal_ir.cache.os.replace", side_effect=blocked_once), \
                patch("universal_ir.cache.sleep") as sleep:
            result = self.run_cache()
        self.assertEqual(result["cache"]["publication"], "stored")
        self.assertEqual(len(calls), 2)
        sleep.assert_called_once_with(0.05)
        self.source.write_bytes(b"print(2)\n")
        with patch("universal_ir.cache.os.replace", side_effect=sharing) as replace, \
                patch("universal_ir.cache.sleep") as sleep:
            result = self.run_cache()
        self.assertEqual(result["cache"]["publication"], "unavailable")
        self.assertEqual(replace.call_count, 4)
        self.assertEqual(sleep.call_count, 3)
        self.assertEqual(result["status"], "ok")

    def test_late_old_publication_cannot_replace_newer_snapshot(self):
        old = inventory(self.root)
        self.source.write_bytes(b"print(2)\n")
        new = self.run_cache()
        cache_snapshot(old, self.store)
        current = self.run_cache()
        self.assertEqual(current["snapshot"], new["snapshot"])
        self.assertEqual(current["cache"]["lookup"], "hit")
        self.assertEqual(len(list((self.store / NAMESPACE).glob("*.json"))), 2)

    def test_windows_crt_probe_denial_without_native_code_retries_boundedly(self):
        from universal_ir.cache import _matches_existing
        denial = PermissionError(errno.EACCES, "Concurrent publication probe denied")
        calls = []

        def blocked_once(path, encoded):
            calls.append(path)
            if len(calls) == 1:
                raise denial
            return _matches_existing(path, encoded)

        with patch("universal_ir.cache._WINDOWS", True), \
                patch("universal_ir.cache._matches_existing", side_effect=blocked_once), \
                patch("universal_ir.cache.sleep") as sleep:
            result = self.run_cache()
        self.assertEqual(result["cache"]["publication"], "stored")
        self.assertEqual(len(calls), 2)
        sleep.assert_called_once_with(0.05)
        accepted = Path(result["cache"]["artifact"])
        contents = accepted.read_bytes()
        self.source.write_bytes(b"print(2)\n")
        with patch("universal_ir.cache._WINDOWS", True), \
                patch("universal_ir.cache._matches_existing", side_effect=denial) as probe, \
                patch("universal_ir.cache.sleep") as sleep:
            failure = self.run_cache()
        self.assertEqual(probe.call_count, 4)
        self.assertEqual(sleep.call_count, 3)
        self.assertEqual(failure["cache"]["publication"], "unavailable")
        self.assertEqual(failure["status"], "ok")
        self.assertEqual(accepted.read_bytes(), contents)
        self.assertEqual(list(accepted.parent.glob(".pending-*.tmp")), [])

    def test_posix_access_denial_and_other_windows_errors_are_not_retried(self):
        for windows, error in ((False, PermissionError(errno.EACCES, "denied")),
                               (True, PermissionError(errno.EPERM, "denied"))):
            with self.subTest(windows=windows, errno=error.errno), \
                    patch("universal_ir.cache._WINDOWS", windows), \
                    patch("universal_ir.cache._matches_existing", side_effect=error) as probe, \
                    patch("universal_ir.cache.sleep") as sleep:
                result = self.run_cache()
            self.assertEqual(probe.call_count, 1)
            sleep.assert_not_called()
            self.assertEqual(result["cache"]["publication"], "unavailable")

    def test_cache_never_serves_when_local_capture_fails(self):
        self.run_cache()
        for code in ("unstable_inputs", "unreadable_input", "invalid_configuration"):
            with self.subTest(code=code), \
                    patch("universal_ir.__main__.inventory", side_effect=InventoryError(code, "blocked")), \
                    patch("universal_ir.__main__.cache_snapshot") as cache:
                status, output, errors = self.cli("--cache-dir", str(self.store))
            self.assertEqual(status, 3 if code == "unstable_inputs" else 2)
            self.assertEqual(output, "")
            self.assertEqual(json.loads(errors)["error"]["code"], code)
            cache.assert_not_called()

    def test_invalid_selection_or_baseline_does_not_write_cache(self):
        for args in (("--path", "absent"), ("--baseline", str(self.base / "absent.json"))):
            status, output, errors = self.cli("--cache-dir", str(self.store), *args)
            self.assertEqual(status, 2)
            self.assertEqual(output, "")
            self.assertTrue(errors)
            self.assertFalse(self.store.exists())

    def test_cli_cache_failure_is_a_successful_fresh_view_with_diagnostic(self):
        status, output, errors = self.cli("--cache-dir", str(self.root / "cache"))
        self.assertEqual((status, errors), (0, ""))
        result = json.loads(output)
        self.assertEqual(result["cache"]["lookup"], "unavailable")
        self.assertEqual(result["observation"]["freshness"], "verified_consecutive_captures")
        self.assertFalse((self.root / "cache").exists())

    def test_process_restart_reuses_persisted_snapshot(self):
        command = [sys.executable, "-B", "-m", "universal_ir", "inventory", str(self.root),
                   "--cache-dir", str(self.store), "--full"]
        first = subprocess.run(command, capture_output=True, check=True)
        second = subprocess.run(command, capture_output=True, check=True)
        self.assertEqual(first.stderr + second.stderr, b"")
        cold, warm = json.loads(first.stdout), json.loads(second.stdout)
        self.assertEqual(cold["cache"]["lookup"], "miss")
        self.assertEqual(warm["cache"]["lookup"], "hit")
        self.assertEqual(cold["snapshot"], warm["snapshot"])

    def test_linked_cache_directory_and_artifact_do_not_modify_target(self):
        target = self.base / "target"
        target.mkdir()
        link = self.base / "link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink creation is unavailable in this environment")
        self.store = link / "cache"
        result = self.run_cache()
        self.assertEqual(result["cache"]["lookup"], "unavailable")
        self.assertEqual(list(target.iterdir()), [])
        self.store = self.base / "cache"
        first = self.run_cache()
        artifact = Path(first["cache"]["artifact"])
        artifact.unlink()
        outside = target / "owned.json"
        outside.write_bytes(b"user-owned")
        artifact.symlink_to(outside)
        result = self.run_cache()
        self.assertEqual(result["cache"]["lookup"], "unavailable")
        self.assertEqual(outside.read_bytes(), b"user-owned")

    @unittest.skipUnless(os.name == "nt", "Windows junction boundary")
    def test_windows_junction_cache_directory_is_rejected(self):
        target = self.base / "target"
        target.mkdir()
        junction = self.base / "junction"
        subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(target)],
                       capture_output=True, check=True)
        self.store = junction / "cache"
        result = self.run_cache()
        self.assertEqual(result["cache"]["lookup"], "unavailable")
        self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
