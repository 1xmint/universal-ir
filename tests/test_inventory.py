"""Behavior and failure checks for the read-only local inventory proof."""

from contextlib import redirect_stderr, redirect_stdout
import copy
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
from universal_ir.inventory import (
    Capture, ChangedDuringCapture, InventoryError, compare, identity, inventory,
    load_baseline, view,
)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix="uir-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()

    def write(self, name, content=b"", root=None):
        path = (root or self.root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
        return path

    def configure(self, **updates):
        config = {"version": 1, "project_id": "sample", "exclude": [], "documents": []}
        config.update(updates)
        return self.write(".uir/config/project.json", json.dumps(config))

    def entries(self, result):
        return {entry["path"]: entry for entry in result["manifest"]["entries"]}

    def baseline(self, result):
        path = self.base / "before.json"
        path.write_text(json.dumps(view(result, full=True)), encoding="utf-8")
        return path

    def assert_error(self, code, call):
        with self.assertRaises(InventoryError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def cli(self, arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(arguments)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_non_git_mixed_language_opaque_bytes_and_preservation(self):
        files = {"README.md": b"# Purpose\r\n", "src/pay.py": b"pass\n",
                 "client.ts": b"export {}\n", "photo.bin": b"\x00\xff\xfe"}
        for name, content in files.items():
            self.write(name, content)
        before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        result = inventory(self.root)
        output = view(result, full=True)
        entries = {entry["path"]: entry for entry in output["view"]["entries"]}
        self.assertEqual(entries["src/pay.py"]["classification"]["language"], "Python")
        self.assertEqual(entries["client.ts"]["classification"]["origin"], "hypothesis")
        self.assertEqual(entries["photo.bin"]["classification"]["language"], "unknown")
        self.assertEqual(output["coverage"]["semantics"], "unknown")
        self.assertEqual(output["coverage"]["model_calls"], 0)
        self.assertFalse(result["observation"]["atomic"])
        self.assertEqual(output["guidance"]["entries"][0]["path"], "README.md")
        self.assertEqual(before, sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*")))
        for name, content in files.items():
            self.assertEqual((self.root / name).read_bytes(), content)
        self.assertFalse((self.root / ".git").exists())
        self.assertFalse((self.root / ".uir").exists())

    def test_equivalent_inputs_in_separate_checkouts(self):
        other = self.base / "elsewhere"
        other.mkdir()
        for root in (self.root, other):
            self.write("!first.txt", "same", root)
            self.write("space café/data.py", "print(1)", root)
        first, second = inventory(self.root), inventory(other)
        self.assertEqual(first["snapshot"], second["snapshot"])
        self.assertEqual(first["manifest"], second["manifest"])
        self.assertNotEqual(first["observation"]["root"], second["observation"]["root"])
        self.assertEqual(load_baseline(self.baseline(first))["snapshot"], first["snapshot"])

    def test_nested_gitignore_negation_and_excluded_parent(self):
        self.write(".gitignore", "*.log\n!keep.log\nbuild/\n.gitignore\n")
        self.write("skip.log", "excluded")
        self.write("keep.log", "included")
        self.write("build/.gitignore", "!visible.py\n")
        self.write("build/visible.py", "excluded parent")
        self.write("sub/.gitignore", "secret.py\n")
        self.write("sub/secret.py", "excluded")
        self.write("sub/visible.py", "included")
        result = inventory(self.root)
        names = self.entries(result)
        self.assertIn("keep.log", names)
        self.assertIn("sub/visible.py", names)
        self.assertNotIn("skip.log", names)
        self.assertNotIn("build/visible.py", names)
        self.assertNotIn("sub/secret.py", names)
        self.assertNotIn(".gitignore", names)
        self.assertIn(".gitignore", result["manifest"]["controls"])
        self.assertIn("sub/.gitignore", result["manifest"]["controls"])

    def test_private_global_and_injected_git_configuration_are_not_applied(self):
        subprocess.run(["git", "init", "--quiet", "--template=", str(self.root)], check=True)
        self.write(".git/info/exclude", "private.txt\n")
        self.write("private.txt", "included")
        self.write("global.txt", "included")
        self.write("core.txt", "included")
        global_ignore = self.base / "global.ignore"
        global_ignore.write_text("global.txt\ncore.txt\n", encoding="utf-8")
        with patch.dict(os.environ, {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.excludesFile",
                                     "GIT_CONFIG_VALUE_0": str(global_ignore)}):
            result = inventory(self.root)
        self.assertTrue({"private.txt", "global.txt", "core.txt"} <= self.entries(result).keys())
        self.assertNotIn(".git", self.entries(result))

    def test_gitignore_rules_apply_to_tracked_files_too(self):
        subprocess.run(["git", "init", "--quiet", "--template=", str(self.root)], check=True)
        self.write("tracked.log", "tracked")
        subprocess.run(["git", "-C", str(self.root), "add", "tracked.log"], check=True)
        self.write(".gitignore", "*.log\n")
        self.assertNotIn("tracked.log", self.entries(inventory(self.root)))

    def test_config_links_exclusions_and_cache_boundary(self):
        self.configure(exclude=["vendor"], documents=["README.md", "missing.md", "vendor/a.py"])
        self.write("README.md", "# Declared purpose\n")
        self.write("vendor/a.py", "excluded")
        self.write(".uir/cache/export.json", "excluded")
        self.write(".uir/knowledge/intent.md", "# Declared intent\n")
        result = inventory(self.root)
        output = view(result, full=True)
        links = {link["to"]: link for link in output["document_links"]["entries"]}
        self.assertEqual(links["README.md"]["status"], "resolved")
        self.assertEqual(links["missing.md"]["status"], "unresolved")
        self.assertEqual(links["missing.md"]["reason"], "absent")
        self.assertEqual(links["vendor/a.py"]["status"], "unresolved")
        self.assertEqual(links["vendor/a.py"]["reason"], "excluded")
        self.assertEqual(output["project"]["id"], "sample")
        self.assertNotIn(".uir/cache/export.json", self.entries(result))
        self.assertIn(".uir/knowledge/intent.md", self.entries(result))
        self.assertEqual(links["README.md"]["evidence"]["snapshot"], result["snapshot"])

    def test_config_is_control_input_even_when_hidden(self):
        self.configure(exclude=[".uir"])
        first = inventory(self.root)
        self.assertIn(".uir/config/project.json", first["manifest"]["controls"])
        self.assertNotIn(".uir/config/project.json", self.entries(first))
        self.configure(exclude=[".uir"], project_id="changed")
        self.assertNotEqual(first["snapshot"], inventory(self.root)["snapshot"])

    def test_ignored_content_changes_do_not_change_identity(self):
        self.write(".gitignore", "build/\n")
        self.write("build/ignored.txt", "old")
        first = inventory(self.root)
        self.write("build/ignored.txt", "new")
        self.assertEqual(first["snapshot"], inventory(self.root)["snapshot"])
        self.write(".gitignore", "build/\n# scope control change\n")
        self.assertNotEqual(first["snapshot"], inventory(self.root)["snapshot"])

    def test_restart_reconciles_added_removed_changed_and_scope(self):
        self.configure()
        self.write("remove.py", "old")
        self.write("change.py", "old")
        self.write("vendor/a.txt", "still exists")
        first = inventory(self.root)
        baseline = load_baseline(self.baseline(first))
        (self.root / "remove.py").unlink()
        self.write("change.py", "new")
        self.write("added.rs", "new")
        self.configure(exclude=["vendor"])
        second = inventory(self.root)
        changes = compare(baseline, second, full=True)
        actual = {change["path"]: change["change"] for change in changes["changes"]}
        self.assertEqual(actual["remove.py"], "removed")
        self.assertEqual(actual["added.rs"], "added")
        self.assertEqual(actual["change.py"], "changed")
        self.assertEqual(actual["vendor/a.txt"], "removed")
        self.assertTrue((self.root / "vendor/a.txt").is_file())
        self.assertTrue(changes["configuration_changed"])
        self.assertTrue(changes["control_inputs_changed"])
        self.assertNotEqual(first["snapshot"], second["snapshot"])

    def test_empty_directory_membership_is_an_input(self):
        first = inventory(self.root)
        (self.root / "empty").mkdir()
        self.assertNotEqual(first["snapshot"], inventory(self.root)["snapshot"])

    def test_bounded_views_expand_with_snapshot_evidence(self):
        for number in range(7):
            self.write(f"src/{number}.py", "pass\n")
        result = inventory(self.root)
        first = view(result, selection="src", limit=3)
        next_view = view(result, selection="src", limit=3, offset=first["view"]["next_offset"])
        self.assertEqual(first["view"]["total"], 8)
        self.assertEqual(first["view"]["omitted"], 5)
        self.assertEqual(first["outline"]["total"], 7)
        self.assertEqual(first["outline"]["omitted"], 4)
        self.assertEqual(len(first["view"]["entries"]), 3)
        self.assertEqual(first["snapshot"], next_view["snapshot"])
        self.assertTrue(all(edge["evidence"]["snapshot"] == result["snapshot"]
                            for edge in next_view["view"]["relationships"]))
        self.assertEqual(view(result, offset=999)["view"]["entries"], [])
        self.assert_error("invalid_selection", lambda: view(result, selection="missing"))
        self.assert_error("invalid_arguments", lambda: view(result, limit=0))

    def test_comparison_lists_are_bounded(self):
        first = inventory(self.root)
        for number in range(5):
            self.write(f"{number}.py", "new")
        changes = compare(first, inventory(self.root), limit=2)
        self.assertEqual(changes["total"], 5)
        self.assertEqual(changes["omitted"], 3)

    def test_nested_repositories_are_boundaries(self):
        self.write("nested/.git", "gitdir: irrelevant\n")
        self.write("nested/secret.py", "not inspected")
        result = inventory(self.root)
        self.assertEqual(self.entries(result)["nested"]["reason"], "nested_repository")
        self.assertNotIn("nested/secret.py", self.entries(result))
        self.assert_error("invalid_selection", lambda: view(result, selection="nested"))

    def test_symlinks_do_not_expand_or_load_configuration(self):
        target = self.base / "outside"
        target.mkdir()
        (target / "private.txt").write_text("outside", encoding="utf-8")
        try:
            (self.root / "linked").symlink_to(target, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Symlink creation unavailable: {error}")
        result = inventory(self.root)
        self.assertEqual(self.entries(result)["linked"]["reason"], "link")
        self.assertNotIn("linked/private.txt", self.entries(result))
        (self.root / ".uir").symlink_to(target, target_is_directory=True)
        self.assert_error("invalid_configuration", lambda: inventory(self.root))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX special file")
    def test_special_files_are_boundaries_without_reading(self):
        os.mkfifo(self.root / "pipe")
        self.assertEqual(self.entries(inventory(self.root))["pipe"]["reason"], "special_file")

    def test_invalid_configurations_fail_without_replacement(self):
        samples = ['{"version": 1, "version": 1}', '{broken',
                   json.dumps({"version": True, "project_id": "x", "exclude": [], "documents": []}),
                   json.dumps({"version": 1, "project_id": "x", "exclude": ["../escape"], "documents": []}),
                   json.dumps({"version": 1, "project_id": "x", "exclude": [], "documents": [], "extra": 1}),
                   json.dumps({"version": 1, "project_id": "x", "exclude": ["a", "a"], "documents": []})]
        for content in samples:
            with self.subTest(content=content):
                path = self.write(".uir/config/project.json", content)
                with self.assertRaises(InventoryError):
                    inventory(self.root)
                self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_invalid_baselines_do_not_replace_current_extraction(self):
        self.write("app.py", "pass")
        first = inventory(self.root)
        path = self.baseline(first)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["manifest"]["entries"][-1]["content_id"] = "sha256:" + "0" * 64
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assert_error("invalid_baseline", lambda: load_baseline(path))
        data["snapshot"] = identity(data["manifest"])
        data["manifest"]["entries"].append(data["manifest"]["entries"][-1])
        data["snapshot"] = identity(data["manifest"])
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assert_error("invalid_baseline", lambda: load_baseline(path))
        previous = copy.deepcopy(first)
        previous["manifest"]["ignore_engine"] = "git-0.0.0"
        self.assert_error("incompatible_baseline", lambda: compare(previous, first))
        self.assertEqual((self.root / "app.py").read_bytes(), b"pass")

    def test_cli_json_success_comparison_and_errors(self):
        self.write("app.py", "old")
        first = inventory(self.root)
        path = self.baseline(first)
        self.write("app.py", "new")
        status, stdout, stderr = self.cli(["inventory", str(self.root), "--baseline", str(path)])
        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout)["comparison"]["changes"], [{"path": "app.py", "change": "changed"}])
        for args in ([], ["inventory"], ["inventory", str(self.root), "--limit", "bad"],
                     ["inventory", str(self.root), "--offset", "-1"]):
            with self.subTest(args=args):
                status, stdout, stderr = self.cli(args)
                self.assertEqual(status, 2)
                self.assertEqual(stdout, "")
                self.assertEqual(json.loads(stderr)["error"]["code"], "invalid_arguments")

    def test_source_run_subprocess_entrypoint(self):
        self.write("app.py", "pass")
        result = subprocess.run([sys.executable, "-m", "universal_ir", "inventory", str(self.root)],
                                capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)["status"], "ok")
        self.assertEqual(result.stderr, b"")

    def test_missing_git_fails_closed(self):
        with patch("universal_ir.inventory.subprocess.run", side_effect=FileNotFoundError()):
            self.assert_error("missing_git", lambda: inventory(self.root))

    def test_ignore_failure_does_not_widen_scope(self):
        self.write(".gitignore", "private/\n")
        self.write("private/data.txt", "excluded")
        with patch("universal_ir.inventory.IgnoreRules.excluded",
                   side_effect=InventoryError("ignore_failure", "fixture evaluator failure")):
            status, stdout, stderr = self.cli(["inventory", str(self.root)])
        self.assertEqual(status, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(json.loads(stderr)["error"]["code"], "ignore_failure")

    def test_non_file_configuration_fails_without_opening(self):
        (self.root / ".uir/config/project.json").mkdir(parents=True)
        self.assert_error("invalid_configuration", lambda: inventory(self.root))

    def test_temporary_repository_cannot_be_created_inside_selected_root(self):
        with patch("universal_ir.inventory.gettempdir", return_value=str(self.root)):
            self.assert_error("invalid_root", lambda: inventory(self.root))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_relative_selection_cannot_escape_root(self):
        result = inventory(self.root)
        self.assert_error("invalid_path", lambda: view(result, selection="../outside"))

    def test_root_resolution_failure_returns_json_error(self):
        with patch("universal_ir.inventory.Path.resolve", side_effect=OSError("fixture inaccessible root")):
            status, stdout, stderr = self.cli(["inventory", str(self.root)])
        self.assertEqual(status, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(json.loads(stderr)["error"]["code"], "invalid_root")

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_windows_junction_is_a_boundary(self):
        target = self.base / "outside"
        target.mkdir()
        (target / "private.py").write_text("outside", encoding="utf-8")
        link = self.root / "junction"
        created = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
        if created.returncode:
            self.skipTest("Junction creation unavailable")
        result = inventory(self.root)
        self.assertEqual(self.entries(result)["junction"]["reason"], "link")
        self.assertNotIn("junction/private.py", self.entries(result))
        self.assertEqual((target / "private.py").read_text(encoding="utf-8"), "outside")

    def test_guidance_and_document_omissions_are_explicit(self):
        self.configure(documents=["README.md", "SECURITY.md"])
        self.write("README.md", "guide")
        self.write("SECURITY.md", "guide")
        result = inventory(self.root)
        compact = view(result, limit=1)
        self.assertEqual(compact["guidance"]["omitted"], 1)
        self.assertEqual(compact["document_links"]["omitted"], 1)
        self.assertEqual(view(result, full=True)["document_links"]["omitted"], 0)

    @unittest.skipIf(os.name == "nt", "Windows rejects wildcard filenames")
    def test_unsupported_portable_filename_is_not_silently_dropped(self):
        self.write("wild*.py", "pass")
        self.assert_error("unsupported_path", lambda: inventory(self.root))

    def test_unreadable_input_returns_no_success(self):
        self.write("app.py", "pass")
        original = os.open

        def deny(path, flags, *args, **kwargs):
            if Path(path).name == "app.py":
                raise PermissionError("fixture denied")
            return original(path, flags, *args, **kwargs)

        with patch("universal_ir.inventory.os.open", side_effect=deny):
            status, stdout, stderr = self.cli(["inventory", str(self.root)])
        self.assertEqual(status, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(json.loads(stderr)["error"]["code"], "unreadable_input")

    def test_detected_edits_retry_then_use_new_contents(self):
        self.write("app.py", "old")
        from universal_ir.inventory import capture as actual_capture
        calls = 0

        def mutate(root, rules):
            nonlocal calls
            result = actual_capture(root, rules)
            calls += 1
            if calls == 1:
                self.write("app.py", "new")
            return result

        with patch("universal_ir.inventory.capture", side_effect=mutate):
            result = inventory(self.root)
        self.assertEqual(calls, 4)
        self.assertEqual(result["snapshot"], inventory(self.root)["snapshot"])

    def test_continuously_changing_inputs_fail_without_partial_view(self):
        calls = 0

        def unstable(*args):
            nonlocal calls
            calls += 1
            return Capture({"changing": calls}, {})

        with patch("universal_ir.inventory.capture", side_effect=unstable):
            status, stdout, stderr = self.cli(["inventory", str(self.root)])
        self.assertEqual(calls, 6)
        self.assertEqual(status, 3)
        self.assertEqual(stdout, "")
        self.assertEqual(json.loads(stderr)["error"]["code"], "unstable_inputs")

    def test_disappearing_input_retries(self):
        from universal_ir.inventory import capture as actual_capture
        calls = 0

        def disappear(root, rules):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ChangedDuringCapture()
            return actual_capture(root, rules)

        with patch("universal_ir.inventory.capture", side_effect=disappear):
            self.assertEqual(inventory(self.root)["status"], "ok")
        self.assertEqual(calls, 3)


if __name__ == "__main__":
    unittest.main()
