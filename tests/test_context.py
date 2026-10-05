"""Freshness, evidence, scope, budget, and real CLI checks for literal retrieval."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from universal_ir.__main__ import main
from universal_ir.context import MAX_FILE_BYTES, _read_text, task_context
from universal_ir.inventory import ChangedDuringCapture, InventoryError, inventory


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix="uir-context-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "project"
        self.root.mkdir()

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8") if isinstance(text, str) else text)
        return target

    def files(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def assert_code(self, code, function, *args, **kwargs):
        with self.assertRaises(InventoryError) as caught:
            function(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)

    def test_cross_component_matches_and_exact_source_locations(self):
        self.write("services/tasks/archive.ts", "start\r\nnext\r\nadmin\r\nARCHIVE task\r\nend\r\n")
        self.write("db/migrations/012.sql", "-- administrator archive state\n")
        self.write("ui/TaskPanel.py", "# unrelated text\n")
        result = task_context(self.root, "ARCHIVE admin", max_bytes=512)
        self.assertEqual(["db/migrations/012.sql", "services/tasks/archive.ts"],
                         [item["path"] for item in result["matches"]["entries"]])
        self.assertEqual(result["snapshot"], inventory(self.root)["snapshot"])
        for item in result["matches"]["entries"]:
            snippet = item["excerpt"]
            source = (self.root / item["path"]).read_bytes()
            self.assertEqual(source[snippet["start_byte"]:snippet["end_byte"]], snippet["text"].encode("utf-8"))
            self.assertEqual(item["content_id"], item["evidence"]["content_id"])
            self.assertEqual(result["snapshot"], item["evidence"]["snapshot"])
        self.assertIn({"from": "services", "to": "services/tasks"},
                      [{"from": edge["from"], "to": edge["to"]} for edge in result["relationships"]["entries"]])
        self.assertEqual("unknown", result["coverage"]["semantics"])
        self.assertEqual("hypothesis", result["matches"]["entries"][0]["classification"]["origin"])

    def test_unicode_casefold_literals_not_patterns_or_semantic_ranking(self):
        self.write("a.txt", "Straße payment\n")
        self.write("b.txt", "STRASSE paywall\n")
        result = task_context(self.root, "strasse PAY pay")
        self.assertEqual(["pay", "strasse"], result["selection"]["terms"])
        self.assertEqual(2, result["matches"]["total"])
        self.assertEqual(0, task_context(self.root, "pay*")["matches"]["total"])
        self.assertEqual(0, task_context(self.root, "billing")["matches"]["total"])

    def test_path_only_match_still_has_explained_excerpt(self):
        self.write("tasks/archive.py", "# no matching source text\n")
        item = task_context(self.root, "archive")["matches"]["entries"][0]
        self.assertEqual(["archive"], item["match"]["path_terms"])
        self.assertEqual([], item["match"]["content_terms"])
        self.assertIsNone(item["match"]["first_content_line"])
        self.assertEqual(1, item["excerpt"]["start_line"])

    def test_scope_ignores_configuration_guidance_and_unresolved_documents(self):
        self.write(".gitignore", "ignored/\n")
        self.write("ignored/secret.py", "archive")
        self.write("vendor/secret.py", "archive")
        self.write("README.md", "archive app")
        self.write("services/tasks.ts", "archive")
        self.write(".uir/config/project.json", json.dumps({"version": 1, "project_id": "demo",
                   "exclude": ["vendor"], "documents": ["README.md", "missing.md"]}))
        read = _read_text
        with patch("universal_ir.context._read_text", wraps=read) as calls:
            result = task_context(self.root, "archive", selection="services")
        self.assertEqual(["services/tasks.ts"], [call.args[1]["path"] for call in calls.call_args_list])
        self.assertEqual("demo", result["project"]["id"])
        self.assertEqual(["README.md"], [entry["path"] for entry in result["guidance"]["entries"]])
        self.assertEqual("unresolved", result["document_links"]["entries"][1]["status"])
        self.assertEqual("absent", result["document_links"]["entries"][1]["reason"])
        self.assertTrue({"ignored", "vendor"} <= {item["path"] for item in result["exclusions"]["entries"]})

    def test_opaque_and_oversized_files_keep_path_matches_and_visible_gaps(self):
        self.write("archive-large.bin", b"x" * (MAX_FILE_BYTES + 1))
        self.write("archive-nul.txt", b"archive\x00")
        self.write("archive-invalid.txt", b"archive\xff")
        self.write("archive-empty.txt", b"")
        result = task_context(self.root, "archive")
        self.assertEqual(4, result["matches"]["total"])
        self.assertEqual(1, result["coverage"]["text_searched"])
        self.assertEqual({"file_too_large": 1, "not_utf8": 1, "nul_bytes": 1}, result["coverage"]["gap_counts"])
        self.assertTrue(all(item["excerpt"] is None for item in result["matches"]["entries"]))

    def test_budget_truncates_at_utf8_boundary_and_reports_exact_range(self):
        self.write("a.txt", "hit " + "é" * 2000)
        self.write("b.txt", "hit " + "🧭" * 2000)
        result = task_context(self.root, "hit", max_bytes=129)
        self.assertLessEqual(result["excerpt_budget"]["used_bytes"], 129)
        self.assertEqual("h", result["matches"]["entries"][1]["excerpt"]["text"])
        exhausted = task_context(self.root, "hit", max_bytes=128)
        self.assertEqual("excerpt_budget_exhausted", exhausted["matches"]["entries"][1]["text_status"])
        excerpt = result["matches"]["entries"][0]["excerpt"]
        self.assertTrue(excerpt["truncated"])
        self.assertEqual(1, excerpt["end_line"])
        self.assertEqual((self.root / "a.txt").read_bytes()[:excerpt["end_byte"]], excerpt["text"].encode("utf-8"))
        roomy = task_context(self.root, "hit", max_bytes=65536)
        self.assertTrue(all(len(item["excerpt"]["text"].encode("utf-8")) <= 2048 for item in roomy["matches"]["entries"]))

    def test_line_window_uses_lf_and_tracks_long_line_clipping(self):
        self.write("a.txt", "one\ntwo\nthree\nfour\nfive\nhit\nseven\neight\nnine\n")
        excerpt = task_context(self.root, "hit")["matches"]["entries"][0]["excerpt"]
        self.assertEqual((4, 8), (excerpt["start_line"], excerpt["end_line"]))
        self.assertEqual("four\nfive\nhit\nseven\neight\n", excerpt["text"])
        self.write("a.txt", "x" * 3000 + " hit")
        item = task_context(self.root, "hit")["matches"]["entries"][0]
        self.assertTrue(item["excerpt"]["truncated"])
        self.assertNotIn("hit", item["excerpt"]["text"])
        self.assertEqual(1, item["match"]["first_content_line"])

    def test_pagination_is_repeatable_and_pin_rejects_offline_change(self):
        for index in range(4):
            self.write(f"{index}.py", "hit")
        first = task_context(self.root, "hit", limit=2)
        second = task_context(self.root, "hit", limit=2, offset=first["matches"]["next_offset"], expected_snapshot=first["snapshot"])
        self.assertEqual(["2.py", "3.py"], [item["path"] for item in second["matches"]["entries"]])
        self.assertIsNone(second["matches"]["next_offset"])
        self.write("new.py", "hit")
        (self.root / "0.py").unlink()
        self.assert_code("stale_snapshot", task_context, self.root, "hit", expected_snapshot=first["snapshot"])
        current = task_context(self.root, "hit")
        self.assertNotEqual(current["snapshot"], first["snapshot"])
        self.assertEqual(4, current["matches"]["total"])
        empty = task_context(self.root, "hit", offset=999)
        self.assertEqual([], empty["matches"]["entries"])
        self.assertEqual(4, empty["matches"]["omitted"])

    def test_identical_checkouts_have_same_facts_and_source_unchanged(self):
        self.write("a.py", "hit")
        self.write(".uir/knowledge/pending.json", '{"unverified": "hit"}')
        self.write(".env", "private=hit")
        before = self.files()
        other = self.base / "other"
        shutil.copytree(self.root, other)
        left, right = task_context(self.root, "hit"), task_context(other, "hit")
        self.assertEqual(left["snapshot"], right["snapshot"])
        self.assertEqual(left["matches"], right["matches"])
        self.assertNotEqual(left["observation"]["root"], right["observation"]["root"])
        self.assertEqual(before, self.files())
        self.assertIn(".env", [item["path"] for item in left["matches"]["entries"]])
        self.assertEqual("untrusted_project_data", left["coverage"]["source_text"])

    def test_parent_boundary_is_not_followed(self):
        self.write("nested/.git/HEAD", "ref: refs/heads/main")
        self.write("nested/secret.py", "hit")
        result = task_context(self.root, "hit")
        self.assertEqual(0, result["matches"]["total"])
        self.assertEqual("nested", result["boundaries"]["entries"][0]["path"])
        self.assert_code("invalid_selection", task_context, self.root, "hit", selection="nested")

    def test_read_race_retries_and_perpetual_race_returns_no_view(self):
        self.write("a.py", "old hit")
        read = _read_text
        changed = False
        def edit_once(root, entry):
            nonlocal changed
            if not changed:
                changed = True
                self.write("a.py", "new hit")
            return read(root, entry)
        with patch("universal_ir.context._read_text", side_effect=edit_once):
            result = task_context(self.root, "hit")
        self.assertEqual("new hit", result["matches"]["entries"][0]["excerpt"]["text"])
        with patch("universal_ir.context._read_text", side_effect=ChangedDuringCapture):
            self.assert_code("unstable_inputs", task_context, self.root, "hit")

    def test_change_after_search_is_caught_even_for_nonmatching_input(self):
        self.write("a.py", "hit")
        other = self.write("z.py", "other")
        read = _read_text
        count = 0
        def change_other(root, entry):
            nonlocal count
            text = read(root, entry)
            if entry["path"] == "z.py":
                count += 1
                other.write_bytes(f"changed {count}".encode())
            return text
        with patch("universal_ir.context._read_text", side_effect=change_other):
            self.assert_code("unstable_inputs", task_context, self.root, "hit")

    def test_unreadable_source_fails_and_does_not_become_a_gap(self):
        self.write("a.py", "hit")
        with patch("universal_ir.context.os.open", side_effect=PermissionError("denied")):
            self.assert_code("unreadable_input", task_context, self.root, "hit")

    def test_equal_size_timestamp_edit_cannot_reuse_old_excerpts(self):
        target = self.write("a.py", "old hit")
        original = target.stat()
        read = _read_text
        changed = False
        def edit_once(root, entry):
            nonlocal changed
            if not changed:
                changed = True
                target.write_bytes(b"new hit")
                os.utime(target, ns=(original.st_atime_ns, original.st_mtime_ns))
            return read(root, entry)
        with patch("universal_ir.context._read_text", side_effect=edit_once):
            result = task_context(self.root, "hit")
        self.assertEqual("new hit", result["matches"]["entries"][0]["excerpt"]["text"])

    def test_transient_read_error_reconciles_before_reporting_and_cli_instability(self):
        target = self.write("a.py", "old hit")
        read = _read_text
        changed = False
        def temporary_failure(root, entry):
            nonlocal changed
            if not changed:
                changed = True
                target.write_bytes(b"new hit")
                raise InventoryError("unreadable_input", "temporary replacement")
            return read(root, entry)
        with patch("universal_ir.context._read_text", side_effect=temporary_failure):
            result = task_context(self.root, "hit")
        self.assertEqual("new hit", result["matches"]["entries"][0]["excerpt"]["text"])
        out, err = io.StringIO(), io.StringIO()
        with patch("universal_ir.context._read_text", side_effect=ChangedDuringCapture), redirect_stdout(out), redirect_stderr(err):
            code = main(["context", str(self.root), "--query", "hit"])
        self.assertEqual(3, code)
        self.assertEqual("", out.getvalue())
        self.assertEqual("uir.context.v1", json.loads(err.getvalue())["format"])

    def test_argument_bounds_scope_and_configuration_changes(self):
        for query in ("", " ", "x" * 257, "bad\x00", "\ud800", " ".join(str(i) for i in range(17))):
            self.assert_code("invalid_arguments", task_context, self.root, query)
        for args in ({"limit": 0}, {"limit": 51}, {"limit": True}, {"offset": -1},
                     {"max_bytes": 127}, {"max_bytes": 65537}, {"expected_snapshot": "fake"}):
            self.assert_code("invalid_arguments", task_context, self.root, "hit", **args)
        self.assert_code("invalid_path", task_context, self.root, "hit", selection="../other")
        self.assert_code("invalid_selection", task_context, self.root, "hit", selection="absent")
        before = task_context(self.root, "hit")
        self.write(".uir/config/project.json", json.dumps({"version": 1, "project_id": "changed", "exclude": [], "documents": []}))
        self.assert_code("stale_snapshot", task_context, self.root, "hit", expected_snapshot=before["snapshot"])
        self.write(".uir/config/project.json", "{}")
        self.assert_code("invalid_configuration", task_context, self.root, "hit")

    def test_bounded_diagnostics_do_not_hide_their_total(self):
        for index in range(25):
            self.write(f"{index:02}.bin", b"\x00")
        result = task_context(self.root, "missing")
        self.assertEqual({"total": 25, "omitted": 5}, {key: result["coverage"]["gaps"][key] for key in ("total", "omitted")})
        self.assertEqual(20, len(result["coverage"]["gaps"]["entries"]))
        self.assertEqual(0, result["matches"]["total"])

    def test_real_cli_success_and_redirection_preserve_selected_project(self):
        self.write("a.py", "hit\n")
        before = self.files()
        process = subprocess.run([sys.executable, "-B", "-m", "universal_ir", "context", str(self.root),
                                  "--query", "hit", "--max-bytes", "128"], capture_output=True, check=True)
        result = json.loads(process.stdout)
        self.assertEqual("uir.context.v1", result["format"])
        self.assertEqual(1, result["matches"]["total"])
        self.assertEqual(b"", process.stderr)
        self.assertEqual(before, self.files())
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            exit_code = main(["context", str(self.root), "--query", "hit", "--expected-snapshot", "sha256:" + "0" * 64])
        self.assertEqual(2, exit_code)
        self.assertEqual("", out.getvalue())
        self.assertEqual("stale_snapshot", json.loads(err.getvalue())["error"]["code"])


if __name__ == "__main__":
    unittest.main()
