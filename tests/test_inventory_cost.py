"""Measurement validity and failure reporting, not performance thresholds."""

import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import statistics
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/measure_inventory.py"
SPEC = importlib.util.spec_from_file_location("measure_inventory", SCRIPT)
cost = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cost)


class CostTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix="uir-cost-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir()
        (self.root / "main.py").write_bytes(b"pass\n")
        self.store = self.root.parent / "cache"

    def test_measurement_reports_actual_states_sizes_and_preserves_project(self):
        samples = [cost.sample(self.root), cost.sample(self.root, self.store), cost.sample(self.root, self.store)]
        self.assertEqual(cost.comparison(samples), "matching_inventory_identities_and_expected_cache_states")
        self.assertEqual(samples[0]["included_files"], 1)
        self.assertEqual(samples[0]["included_file_bytes"], 5)
        self.assertEqual(samples[0]["artifact_bytes"], 0)
        self.assertGreater(samples[1]["artifact_bytes"], 0)
        self.assertGreater(samples[0]["context_json_bytes"], 0)
        self.assertTrue(all(item["timings"]["inventory_with_freshness_ns"] > 0 for item in samples))
        self.assertEqual((self.root / "main.py").read_bytes(), b"pass\n")
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_failed_capture_is_retained_in_measurement(self):
        with patch.object(cost, "inventory", side_effect=cost.InventoryError("unstable_inputs", "changed")):
            result = cost.sample(self.root, self.store)
        self.assertEqual(result["error"]["code"], "unstable_inputs")
        self.assertFalse(self.store.exists())
        self.assertEqual(cost.comparison([result]), "failed_sample")

    def test_changed_inputs_and_failed_storage_are_not_called_comparable(self):
        samples = [cost.sample(self.root), cost.sample(self.root, self.store), cost.sample(self.root, self.store)]
        changed = copy.deepcopy(samples)
        changed[2]["snapshot"] = "different"
        self.assertEqual(cost.comparison(changed), "not_comparable_inputs_changed")
        samples[1]["cache"]["publication"] = "unavailable"
        self.assertEqual(cost.comparison(samples), "cache_expectation_failed")

    def test_worker_crash_and_timeout_are_reported(self):
        failed = subprocess.CompletedProcess([], 7, b"", b"failed")
        with patch.object(cost.subprocess, "run", return_value=failed):
            self.assertEqual(cost.invoke(self.root, None)["error"]["exit"], 7)
        with patch.object(cost.subprocess, "run", side_effect=subprocess.TimeoutExpired("worker", 120)):
            self.assertEqual(cost.invoke(self.root, None)["status"], "error")

    def test_fixture_process_runs_have_matching_identities(self):
        report = cost.measure(None, 1)
        self.assertEqual(report["format"], "uir.inventory-cost.v1")
        self.assertEqual(report["model_calls"], 0)
        self.assertEqual(report["trials"][0]["comparison"], "matching_inventory_identities_and_expected_cache_states")
        self.assertEqual(report["trials"][0]["samples"][0]["included_files"], 103)
        self.assertIn("separate_extraction_and_verification", report["unmeasured"])
        self.assertEqual(report["summary"]["warm_cache"]["successful_samples"], 1)

    def test_invalid_scope_and_trial_count_do_not_run_workers(self):
        with patch.object(cost, "invoke") as invoke:
            for root, count in ((self.root, 0), (self.root, 21), (self.root / "missing", 1)):
                with self.assertRaises(ValueError):
                    cost.measure(root, count)
        invoke.assert_not_called()

    def test_changed_tool_sources_are_reported_without_discarding_attempts(self):
        valid = {"status": "ok", "manifest_identity_valid": True, "snapshot": "same",
                 "cache": {"lookup": "miss", "publication": "stored"}, "process_wall_ns": 1}
        warm = copy.deepcopy(valid)
        warm["cache"] = {"lookup": "hit", "publication": "reused"}
        with patch.object(cost, "tool_sources", side_effect=[{"old": "digest"}, {"new": "digest"}]), \
                patch.object(cost, "invoke", side_effect=[valid, copy.deepcopy(valid), warm]):
            report = cost.measure(None, 1)
        self.assertFalse(report["tool_source_unchanged"])
        self.assertEqual(len(report["trials"][0]["samples"]), 3)

    def test_temporary_path_alias_is_normalized_before_artifact_redaction(self):
        base = self.root.parent
        (base / "alias-parent").mkdir()
        (base / "scratch").mkdir()
        alias = base / "alias-parent" / ".." / "scratch"

        @contextmanager
        def temporary_alias(**kwargs):
            yield str(alias)

        with patch.object(cost, "TemporaryDirectory", temporary_alias):
            report = cost.measure(None, 1)
        self.assertEqual(report["trials"][0]["comparison"], "matching_inventory_identities_and_expected_cache_states")
        artifact = report["trials"][0]["samples"][2]["cache"]["artifact"]
        self.assertTrue(artifact.startswith("<temporary workspace>/cache-0/"))

    def test_recorded_baseline_retains_valid_identities_and_reproducible_summary(self):
        path = SCRIPT.parent.parent / "benchmarks/results/local-inventory-windows.json"
        report = json.loads(path.read_bytes())
        self.assertEqual(report["tool_source_id"], cost.identity(report["tool_source_files"]))
        self.assertTrue(report["tool_source_unchanged"])
        self.assertEqual(len(report["trials"]), report["repetitions"])
        for trial in report["trials"]:
            self.assertEqual(cost.comparison(trial["samples"]), trial["comparison"])
            self.assertEqual(trial["comparison"], "matching_inventory_identities_and_expected_cache_states")
        for mode, summary in report["summary"].items():
            values = [item["process_wall_ns"] for trial in report["trials"] for item in trial["samples"]
                      if item["mode"] == mode and item["status"] == "ok"]
            self.assertEqual(summary["successful_samples"], len(values))
            self.assertEqual(summary["median_process_wall_ns"], statistics.median(values))


if __name__ == "__main__":
    unittest.main()
