"""External candidate evidence/history review, coherent observations, and no writes."""

from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
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
from universal_ir.inventory import ChangedDuringCapture, InventoryError, canonical, identity, inventory
from universal_ir.knowledge import inspect_knowledge, source_projection
from universal_ir.preparation import FORMAT, prepare_knowledge


class PreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="uir-preparation-test-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.config = {"version": 1, "project_id": "sample", "exclude": [], "documents": ["README.md"]}
        self.write(".uir/config/project.json", canonical(self.config) + b"\n")
        self.write("README.md", "# Project\nKeep café tenants apart.\n")
        self.write("src/main.py", "print('hello')\n")
        self.path = self.base / "candidate.json"
        self.body = {"id": "isolation", "category": "requirement", "text": "Keep tenants apart.",
                     "scope": ["src"], "origin": {"kind": "developer_statement", "host_id": "claimed-host",
                     "event_id": "claimed-event", "actor_id": "claimed-alice"}, "input_id": None,
                     "evidence": [self.reference()], "supersedes": [], "state": "active"}
        self.candidate = self.make_record(self.body)
        self.save()

    def write(self, path, data):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
        return target

    def reference(self, path="src/main.py"):
        return {"kind": "file", "path": path, "content_id": "sha256:" + hashlib.sha256((self.root / path).read_bytes()).hexdigest()}

    def make_record(self, body, *, project="sample"):
        unsigned = {"format": "uir.knowledge.v1", "project_id": project, "body": copy.deepcopy(body)}
        return dict(unsigned, record_id=identity(unsigned))

    def save(self, body=None):
        if body is not None:
            self.candidate = self.make_record(body)
        self.path.write_bytes(canonical(self.candidate) + b"\n")

    def store(self, record):
        return self.write(f".uir/knowledge/records/{record['body']['id']}/{record['record_id'][7:]}.json", canonical(record) + b"\n")

    def prepare(self, **kwargs):
        return prepare_knowledge(self.root, self.path, **kwargs)

    def assert_error(self, code, call):
        with self.assertRaises(InventoryError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def test_external_candidate_is_exact_pending_review_without_target_writes(self):
        before = {p.relative_to(self.base): p.read_bytes() for p in self.base.rglob("*") if p.is_file()}
        output = self.prepare()
        self.assertEqual(output["format"], FORMAT)
        self.assertEqual(output["candidate"]["record"], self.candidate)
        self.assertFalse(output["candidate"]["already_included"])
        evaluated = output["candidate"]["evaluation"]
        self.assertIsNone(evaluated["path"])
        self.assertEqual(evaluated["evidence_status"], "matches")
        self.assertEqual(evaluated["attribution"], "unverified_attribution")
        self.assertEqual(evaluated["disposition"], "pending_acceptance")
        self.assertEqual(output["authority"], {"approval": "not_established", "acceptance": "not_established", "writes": False, "model_calls": 0})
        self.assertFalse(output["observation"]["atomic"])
        self.assertEqual(before, {p.relative_to(self.base): p.read_bytes() for p in self.base.rglob("*") if p.is_file()})
        self.assertEqual(inspect_knowledge(self.root)["records"]["total"], 0)

    def test_prepare_identity_is_repeatable_but_candidate_and_base_are_bound(self):
        first = self.prepare()
        self.assertEqual(first["preparation_id"], self.prepare()["preparation_id"])
        self.save(dict(self.body, text="Changed wording."))
        changed = self.prepare()
        self.assertNotEqual(first["preparation_id"], changed["preparation_id"])
        self.write("src/new.py", "pass\n")
        again = self.prepare()
        self.assertNotEqual(changed["preparation_id"], again["preparation_id"])
        self.assertNotEqual(changed["preconditions"]["source_input_id"], again["preconditions"]["source_input_id"])

    def test_normalized_preparation_identity_is_portable_across_equivalent_checkouts(self):
        import shutil
        first = self.prepare()
        self.path.write_bytes((json.dumps(self.candidate, indent=2, ensure_ascii=False) + "\n").encode())
        formatted = self.prepare()
        self.assertEqual(first["preparation_id"], formatted["preparation_id"])
        self.assertNotEqual(first["observation"]["candidate_content_id"], formatted["observation"]["candidate_content_id"])
        copied = self.base / "other-checkout"
        shutil.copytree(self.root, copied)
        other = prepare_knowledge(copied, self.path)
        self.assertEqual(first["preparation_id"], other["preparation_id"])
        self.assertNotEqual(first["observation"]["root"], other["observation"]["root"])

    def test_expected_base_accepts_current_and_rejects_stale_restart(self):
        base = inventory(self.root)["snapshot"]
        self.assertEqual(self.prepare(expected_snapshot=base)["snapshot"], base)
        self.write("unrelated.txt", "manual edit\n")
        self.assert_error("stale_snapshot", lambda: self.prepare(expected_snapshot=base))
        self.assert_error("invalid_arguments", lambda: self.prepare(expected_snapshot="not-an-id"))

    def test_changed_and_missing_evidence_are_visible_not_accepted(self):
        self.write("src/main.py", "print('external edit')\n")
        self.assertEqual(self.prepare()["candidate"]["evaluation"]["evidence_status"], "changed")
        (self.root / "src/main.py").unlink()
        self.assertEqual(self.prepare()["candidate"]["evaluation"]["evidence_status"], "unresolved")

    def test_ai_interpretation_projection_and_future_scope_remain_explicit(self):
        body = dict(self.body, origin={"kind": "ai_interpretation", "host_id": "host", "method": "test", "assumptions": []},
                    input_id=identity(source_projection(inventory(self.root)["manifest"], ["src"])))
        self.save(body)
        self.assertEqual(self.prepare()["candidate"]["evaluation"]["evidence_status"], "matches")
        self.write("src/new.py", "pass\n")
        self.assertEqual(self.prepare()["candidate"]["evaluation"]["evidence_status"], "changed")
        self.save(dict(self.body, scope=["future"], evidence=[]))
        evaluated = self.prepare()["candidate"]["evaluation"]
        self.assertEqual(evaluated["unresolved_scope"], ["future"])
        self.assertEqual(evaluated["attribution"], "unverified_attribution")

    def test_exact_document_quote_and_current_document_link_are_checked(self):
        quote = "Keep café tenants apart."
        data = (self.root / "README.md").read_bytes()
        start = data.index(quote.encode())
        ref = dict(self.reference("README.md"), kind="document", start_byte=start,
                   end_byte=start + len(quote.encode()), quote=quote)
        self.save(dict(self.body, origin={"kind": "document_declaration"}, text=quote, evidence=[ref]))
        self.assertEqual(self.prepare()["candidate"]["evaluation"]["evidence_status"], "matches")
        wrong = dict(ref, quote="X" + quote[1:])
        self.save(dict(self.body, origin={"kind": "document_declaration"}, text=wrong["quote"], evidence=[wrong]))
        self.assert_error("invalid_knowledge", self.prepare)
        self.save(dict(self.body, origin={"kind": "document_declaration"}, text=quote, evidence=[ref]))
        self.write(".uir/config/project.json", canonical(dict(self.config, documents=[])) + b"\n")
        self.assertEqual(self.prepare()["candidate"]["evaluation"]["evidence_status"], "unresolved")

    def test_fork_preview_covers_actual_included_heads_without_changing_reader(self):
        left = self.make_record(dict(self.body, text="Left requirement."))
        right = self.make_record(dict(self.body, text="Right requirement."))
        self.store(left)
        self.store(right)
        heads = sorted([left["record_id"], right["record_id"]])
        before = inspect_knowledge(self.root, full=True)
        self.save(dict(self.body, supersedes=[left["record_id"]]))
        output = self.prepare()
        self.assertEqual(output["transition"]["included_heads_before"], heads)
        self.assertEqual(output["transition"]["uncovered_heads"], [right["record_id"]])
        self.assertTrue(output["transition"]["would_leave_competing_heads"])
        self.save(dict(self.body, supersedes=heads, state="withdrawn"))
        output = self.prepare()
        self.assertFalse(output["transition"]["would_leave_competing_heads"])
        self.assertEqual(output["transition"]["included_heads_after"], [self.candidate["record_id"]])
        self.assertEqual(output["candidate"]["evaluation"]["disposition"], "pending_acceptance")
        after = inspect_knowledge(self.root, full=True)
        self.assertEqual(before["groups"], after["groups"])
        self.assertEqual(before["records"], after["records"])

    def test_missing_predecessor_and_record_dependency_are_not_invented(self):
        missing = "sha256:" + "a" * 64
        self.save(dict(self.body, supersedes=[missing], evidence=[{"kind": "record", "record_id": missing}]))
        evaluated = self.prepare()["candidate"]["evaluation"]
        self.assertEqual(evaluated["evidence_status"], "unresolved")
        self.assertEqual(evaluated["missing_predecessors"], [missing])

    def test_matching_record_dependency_does_not_authenticate_its_claim(self):
        previous = self.make_record(dict(self.body, id="prior", evidence=[]))
        self.store(previous)
        self.save(dict(self.body, evidence=[{"kind": "record", "record_id": previous["record_id"]}]))
        reference = self.prepare()["candidate"]["evaluation"]["references"][0]
        self.assertEqual(reference["status"], "matches")
        self.assertEqual(reference["attribution"], "unverified_attribution")

    def test_cross_identity_supersession_and_bad_existing_store_fail_whole_preparation(self):
        other = self.make_record(dict(self.body, id="other"))
        self.store(other)
        self.save(dict(self.body, supersedes=[other["record_id"]]))
        self.assert_error("invalid_knowledge", self.prepare)
        self.save(self.body)
        self.write(".uir/knowledge/records/unexpected.json", b"{}\n")
        self.assert_error("invalid_knowledge", self.prepare)

    def test_existing_identical_candidate_is_reported_without_new_transition(self):
        self.store(self.candidate)
        result = self.prepare()
        self.assertTrue(result["candidate"]["already_included"])
        self.assertEqual(result["transition"]["operation"], "already_included")
        self.assertEqual(result["transition"]["included_heads_before"], result["transition"]["included_heads_after"])

    def test_ignored_store_and_evidence_keep_coverage_gaps(self):
        self.store(self.candidate)
        self.write(".gitignore", ".uir/knowledge/\nsrc/main.py\n")
        result = self.prepare()
        self.assertFalse(result["coverage"]["complete"])
        self.assertFalse(result["candidate"]["already_included"])
        self.assertEqual(result["candidate"]["evaluation"]["evidence_status"], "unresolved")

    def test_project_identity_configuration_and_schema_are_not_self_authorizing(self):
        wrong = self.make_record(self.body, project="another")
        self.path.write_bytes(canonical(wrong) + b"\n")
        self.assert_error("invalid_knowledge", self.prepare)
        self.save()
        self.candidate["body"]["approved"] = True
        self.path.write_bytes(canonical(self.candidate) + b"\n")
        self.assert_error("invalid_knowledge", self.prepare)
        self.save(self.body)
        (self.root / ".uir/config/project.json").unlink()
        self.assert_error("knowledge_unavailable", self.prepare)

    def test_transport_is_external_regular_bounded_and_strict_json(self):
        self.assert_error("invalid_candidate_input", lambda: prepare_knowledge(self.root, self.root / "README.md"))
        for path in (self.base / "missing.json", self.base, Path("bad\x00path")):
            self.assert_error("invalid_candidate_input", lambda: prepare_knowledge(self.root, path))
        for data in (b"{}", b"[]\n", b"null\n", b"true\n", b"0\n", b"{\n", b"\xff\n",
                     b'{"x":1,"x":2}\n', b'{"x":NaN}\n', canonical(self.candidate) + b"\r\n"):
            with self.subTest(data=data[:40]):
                self.path.write_bytes(data)
                self.assert_error("invalid_knowledge", self.prepare)
        self.path.write_bytes(b" " * (1024 * 1024 + 1))
        self.assert_error("invalid_candidate_input", self.prepare)

    def test_candidate_edit_mid_inspection_reconciles_before_publication(self):
        import universal_ir.preparation as preparation
        real = preparation._inspect_capture
        calls = 0

        def changed(*args, **kwargs):
            nonlocal calls
            result = real(*args, **kwargs)
            calls += 1
            if calls == 1:
                self.save(dict(self.body, text="New candidate wording."))
            return result

        with patch("universal_ir.preparation._inspect_capture", side_effect=changed):
            output = self.prepare()
        self.assertEqual(output["candidate"]["record"]["body"]["text"], "New candidate wording.")
        self.assertGreater(calls, 1)

    def test_source_edit_mid_inspection_retries_and_invalid_quote_is_not_misdiagnosed(self):
        import universal_ir.preparation as preparation
        real = preparation._inspect_capture
        calls = 0

        def changed(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                self.write("src/main.py", "manual edit\n")
                raise InventoryError("invalid_knowledge", "transient mismatch")
            return real(*args, **kwargs)

        with patch("universal_ir.preparation._inspect_capture", side_effect=changed):
            output = self.prepare()
        self.assertEqual(output["candidate"]["evaluation"]["evidence_status"], "changed")
        self.assertEqual(calls, 2)

    def test_repeated_changes_and_unreadable_candidate_return_no_partial_result(self):
        with patch("universal_ir.preparation._candidate_input", side_effect=ChangedDuringCapture()):
            self.assert_error("unstable_inputs", self.prepare)
        with patch("universal_ir.preparation._read_file", side_effect=PermissionError("blocked")):
            self.assert_error("unreadable_input", self.prepare)

    def test_candidate_disappearance_during_read_retries_without_partial_success(self):
        import universal_ir.preparation as preparation
        real = preparation._read_bytes
        calls = 0

        def disappeared(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise FileNotFoundError("changed during opened read")
            return real(*args, **kwargs)

        with patch("universal_ir.preparation._read_bytes", side_effect=disappeared):
            self.assertEqual(self.prepare()["status"], "ok")
        self.assertGreater(calls, 1)

    def test_stable_missing_or_invalid_root_is_diagnosed(self):
        self.assert_error("invalid_root", lambda: prepare_knowledge(self.base / "absent", self.path))
        self.assert_error("invalid_root", lambda: prepare_knowledge("bad\x00root", self.path))

    def test_fictional_real_cli_preview_leaves_stored_fork_unchanged(self):
        tool = Path(__file__).resolve().parents[1]
        process = subprocess.run([sys.executable, "-B", "examples/prepare_knowledge.py"],
                                 cwd=tool, capture_output=True, check=True)
        report = json.loads(process.stdout)
        self.assertEqual(report["accepted_resolution"], "not_established")
        self.assertEqual(report["real_user_approval"], "not_demonstrated")
        self.assertFalse(report["project_writes"])
        self.assertFalse(report["preparation"]["candidate"]["already_included"])
        self.assertFalse(report["preparation"]["transition"]["would_leave_competing_heads"])
        self.assertEqual(len(report["stored_heads_unchanged"]), 2)

    def test_candidate_link_and_windows_junction_are_rejected(self):
        link = self.base / "link.json"
        try:
            link.symlink_to(self.path)
        except OSError:
            if os.name != "nt":
                raise
        else:
            self.assert_error("invalid_candidate_input", lambda: prepare_knowledge(self.root, link))
        if os.name == "nt":
            directory = self.base / "linked"
            creation = subprocess.run(["cmd", "/c", "mklink", "/J", str(directory), str(self.path.parent)], capture_output=True)
            if creation.returncode != 0:
                self.fail("Windows junction test setup failed")
            try:
                self.assert_error("invalid_candidate_input", lambda: prepare_knowledge(self.root, directory / self.path.name))
            finally:
                directory.rmdir()

    def test_cli_success_and_error_envelopes_preserve_target(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["prepare-knowledge", str(self.root), str(self.path)])
        self.assertEqual(code, 0)
        self.assertFalse(stderr.getvalue())
        self.assertEqual(json.loads(stdout.getvalue())["format"], FORMAT)
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["prepare-knowledge", str(self.root), str(self.path), "--expected-snapshot", "sha256:" + "0" * 64])
        self.assertEqual(code, 2)
        self.assertFalse(stdout.getvalue())
        self.assertEqual(json.loads(stderr.getvalue())["error"]["code"], "stale_snapshot")
        with patch("universal_ir.preparation._candidate_input", side_effect=ChangedDuringCapture()), redirect_stderr(io.StringIO()):
            self.assertEqual(main(["prepare-knowledge", str(self.root), str(self.path)]), 3)

    def test_real_source_run_cli(self):
        tool = Path(__file__).resolve().parents[1]
        process = subprocess.run([sys.executable, "-B", "-m", "universal_ir", "prepare-knowledge", str(self.root), str(self.path)],
                                 cwd=tool, capture_output=True, check=True)
        self.assertEqual(json.loads(process.stdout)["candidate"]["record"], self.candidate)


if __name__ == "__main__":
    unittest.main()
