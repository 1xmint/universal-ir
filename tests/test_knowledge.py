"""Evidence, attribution, history, and preservation checks for knowledge inspection."""

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
from universal_ir.inventory import InventoryError, canonical, identity, inventory
from universal_ir.knowledge import (
    FORMAT, MAX_RECORD_BYTES, RECORD_FORMAT, STORE, _history, inspect_knowledge,
    source_projection, validate_record,
)


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="uir-knowledge-test-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.config = {"version": 1, "project_id": "sample", "exclude": [], "documents": ["README.md"]}
        self.write(".uir/config/project.json", canonical(self.config) + b"\n")
        self.write("README.md", "# Purpose\nKeep café tenants apart.\n")
        self.write("src/main.py", "print('hello')\n")

    def write(self, path, data):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
        return target

    def reference(self, path="src/main.py"):
        data = (self.root / path).read_bytes()
        return {"kind": "file", "path": path, "content_id": "sha256:" + hashlib.sha256(data).hexdigest()}

    def body(self, *, logical="purpose", kind="ai_interpretation", scope=None, evidence=None, supersedes=None):
        scope = scope or ["."]
        origins = {
            "ai_interpretation": {"kind": kind, "host_id": "sample-host", "method": "fixture", "assumptions": []},
            "developer_statement": {"kind": kind, "host_id": "claimed-host", "event_id": "claimed-event", "actor_id": "claimed-alice"},
            "document_declaration": {"kind": kind},
        }
        return {"id": logical, "category": "purpose", "text": "Keep tenants apart.", "scope": scope,
                "origin": origins[kind], "input_id": identity(source_projection(inventory(self.root)["manifest"], scope))
                if kind == "ai_interpretation" else None,
                "evidence": evidence if evidence is not None else [] if kind == "developer_statement" else [self.reference()],
                "supersedes": supersedes or [], "state": "active"}

    def record(self, body, *, publish=True):
        unsigned = {"format": RECORD_FORMAT, "project_id": "sample", "body": copy.deepcopy(body)}
        record = dict(unsigned, record_id=identity(unsigned))
        path = f"{STORE}/{body['id']}/{record['record_id'][7:]}.json"
        if publish:
            self.write(path, canonical(record) + b"\n")
        return record, path

    def assert_error(self, code, call):
        with self.assertRaises(InventoryError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def inspection(self, **options):
        return inspect_knowledge(self.root, **options)

    def first(self, **options):
        return self.inspection(**options)["records"]["entries"][0]

    def test_matching_evidence_and_no_self_invalidation_or_target_writes(self):
        body = self.body()
        previous = inventory(self.root)
        record, _ = self.record(body)
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        output = self.inspection(full=True)
        entry = output["records"]["entries"][0]
        self.assertEqual(output["format"], FORMAT)
        self.assertEqual(entry["record_id"], record["record_id"])
        self.assertEqual(entry["evidence_status"], "matches")
        self.assertEqual(entry["source_projection"], body["input_id"])
        self.assertNotEqual(output["snapshot"], previous["snapshot"])
        self.assertEqual(output["coverage"]["model_calls"], 0)
        self.assertFalse(output["observation"]["atomic"])
        self.assertEqual(before, {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
        self.assertFalse((self.root / ".git").exists())
        self.assertFalse((self.root / ".uir/cache").exists())

    def test_unverified_statement_never_becomes_approved_and_future_scope_visible(self):
        body = self.body(kind="developer_statement", scope=["future"])
        body["category"] = "requirement"
        self.record(body)
        entry = self.first()
        self.assertEqual(entry["attribution"], "unverified_attribution")
        self.assertEqual(entry["disposition"], "pending_acceptance")
        self.assertEqual(entry["unresolved_scope"], ["future"])
        self.assertEqual(entry["body"]["origin"]["actor_id"], "claimed-alice")
        self.assertEqual(self.inspection()["coverage"]["acceptance"], "not_established")

    def test_restart_add_delete_edit_and_global_configuration_change(self):
        body = self.body(scope=["src"])
        self.record(body)
        self.write("outside.txt", "outside")
        self.assertEqual(self.first()["evidence_status"], "matches")
        added = self.write("src/new.rs", "fn main() {}")
        self.assertEqual(self.first()["evidence_status"], "changed")
        added.unlink()
        self.assertEqual(self.first()["evidence_status"], "matches")
        self.write("src/main.py", "print('changed')")
        self.assertEqual(self.first()["references"][0]["status"], "changed")
        (self.root / "src/main.py").unlink()
        self.assertEqual(self.first()["evidence_status"], "unresolved")
        self.write("src/main.py", "print('hello')\n")
        self.config["documents"] = []
        self.write(".uir/config/project.json", canonical(self.config) + b"\n")
        self.assertEqual(self.first()["evidence_status"], "changed")

    def test_ignore_controls_invalidate_even_when_scope_contents_unchanged(self):
        self.record(self.body(scope=["src"]))
        self.write(".gitignore", "outside/\n")
        self.assertEqual(self.first()["evidence_status"], "changed")

    def document_body(self):
        quote = "Keep café tenants apart."
        start = len("# Purpose\n".encode("utf-8"))
        ref = dict(self.reference("README.md"), kind="document", start_byte=start,
                   end_byte=start + len(quote.encode("utf-8")), quote=quote)
        body = self.body(kind="document_declaration", evidence=[ref])
        body["text"] = quote
        return body

    def test_document_byte_offsets_and_historical_statement_survive_edit(self):
        self.record(self.document_body())
        self.assertEqual(self.first()["evidence_status"], "matches")
        self.write("README.md", "# Changed intent\n")
        entry = self.first()
        self.assertEqual(entry["evidence_status"], "changed")
        self.assertEqual(entry["body"]["text"], "Keep café tenants apart.")
        self.assertEqual(entry["attribution"], "not_applicable")

    def test_removed_document_configuration_is_unresolved_not_rewritten(self):
        self.record(self.document_body())
        self.config["documents"] = []
        self.write(".uir/config/project.json", canonical(self.config) + b"\n")
        self.assertEqual(self.first()["evidence_status"], "unresolved")
        self.assertEqual(self.first()["issues"], [{"reason": "declaration_document_not_configured"}])

    def test_extreme_quote_offsets_fail_as_structured_invalid_knowledge(self):
        body = self.document_body()
        reference = body["evidence"][0]
        reference["start_byte"] = 10 ** 100
        reference["end_byte"] = reference["start_byte"] + len(reference["quote"].encode("utf-8"))
        self.record(body)
        self.assert_error("invalid_knowledge", self.inspection)

    def test_complete_structural_resolution_is_still_pending(self):
        initial, _ = self.record(self.body(kind="developer_statement"))
        branches = []
        for text in ("First.", "Second."):
            body = self.body(kind="developer_statement", supersedes=[initial["record_id"]])
            body["text"] = text
            record, _ = self.record(body)
            branches.append(record["record_id"])
        body = self.body(kind="developer_statement", supersedes=branches)
        body["text"] = "Claimed resolution."
        self.record(body)
        output = self.inspection(full=True)
        self.assertEqual(output["summary"]["competing_groups"], 0)
        head = next(entry for entry in output["records"]["entries"] if entry["history"] == "head")
        self.assertEqual(head["disposition"], "pending_acceptance")
        self.assertEqual(head["attribution"], "unverified_attribution")

    def test_unreadable_knowledge_does_not_return_partial_success(self):
        self.record(self.body())
        with patch("universal_ir.knowledge._read_bytes", side_effect=InventoryError("unreadable_input", "blocked")):
            self.assert_error("unreadable_input", self.inspection)

    def test_same_digest_wrong_quote_and_character_instead_of_byte_offset_rejected(self):
        body = self.document_body()
        body["evidence"][0]["start_byte"] += 1
        body["evidence"][0]["end_byte"] += 1
        self.record(body)
        self.assert_error("invalid_knowledge", self.inspection)

    def test_forks_remain_visible_with_pagination_and_unverified_withdrawal(self):
        initial, _ = self.record(self.body(kind="developer_statement"))
        for text in ("First proposed correction.", "Second proposed correction."):
            body = self.body(kind="developer_statement", supersedes=[initial["record_id"]])
            body["text"] = text
            body["state"] = "withdrawn"
            self.record(body)
        output = self.inspection(selected_id="purpose", limit=1, offset=2)
        self.assertEqual(output["summary"]["competing_groups"], 1)
        group = output["groups"]["entries"][0]
        self.assertTrue(group["competing_heads"])
        self.assertEqual(group["heads_total"], 2)
        self.assertEqual(group["heads_omitted"], 1)
        self.assertEqual(output["records"]["omitted"], 2)
        entries = self.inspection(full=True)["records"]["entries"]
        prior = next(entry for entry in entries if entry["record_id"] == initial["record_id"])
        self.assertEqual(prior["history"], "superseded")
        self.assertTrue(all(entry["disposition"] == "pending_acceptance" for entry in entries))
        self.assertEqual(prior["body"]["text"], initial["body"]["text"])

    def test_record_evidence_tracks_supersession_and_propagates_missing_source(self):
        initial, _ = self.record(self.body())
        summary = self.body(logical="summary", evidence=[{"kind": "record", "record_id": initial["record_id"]}])
        self.record(summary)
        self.assertEqual(self.first(selected_id="summary")["evidence_status"], "matches")
        correction = self.body(supersedes=[initial["record_id"]])
        correction["text"] = "A correction."
        self.record(correction)
        self.assertEqual(self.first(selected_id="summary")["evidence_status"], "changed")
        (self.root / "src/main.py").unlink()
        self.assertEqual(self.first(selected_id="summary")["evidence_status"], "unresolved")
        self.assertEqual(self.first(selected_id="purpose")["evidence_status"], "unresolved")

    def test_missing_revisions_are_unresolved_and_not_rebound(self):
        missing = "sha256:" + "0" * 64
        body = self.body(evidence=[{"kind": "record", "record_id": missing}], supersedes=[missing])
        self.record(body)
        entry = self.first()
        self.assertEqual(entry["evidence_status"], "unresolved")
        self.assertEqual(entry["missing_predecessors"], [missing])
        self.assertEqual(entry["references"][0]["reason"], "missing_revision")

    def test_cross_logical_supersession_rejected(self):
        initial, _ = self.record(self.body())
        self.record(self.body(logical="other", supersedes=[initial["record_id"]]))
        self.assert_error("invalid_knowledge", self.inspection)

    def test_cycle_and_long_history_validation(self):
        # A content-addressed cycle cannot be constructed normally; exercise graph checks directly.
        a, b = "a", "b"
        graph = {a: {"body": {"id": "purpose", "supersedes": [b], "evidence": []}},
                 b: {"body": {"id": "purpose", "supersedes": [], "evidence": [{"kind": "record", "record_id": a}]}}}
        self.assert_error("invalid_knowledge", lambda: _history(graph))
        graph = {str(i): {"body": {"id": "purpose", "supersedes": [str(i - 1)] if i else [], "evidence": []}}
                 for i in range(1500)}
        order, _, heads = _history(graph)
        self.assertEqual(len(order), 1500)
        self.assertEqual(heads["purpose"], ["1499"])

    def test_strict_schema_identity_paths_and_model_status_assertions(self):
        original = self.body()
        changes = [lambda b: b.update(category=[]), lambda b: b.update(scope=["../outside"]),
                   lambda b: b.update(scope=[".", "."]), lambda b: b.update(input_id="sha256:bad"),
                   lambda b: b.update(state="withdrawn"), lambda b: b.update(verified=True),
                   lambda b: b["origin"].update(approved=True),
                   lambda b: b.update(evidence=[dict(self.reference(), path=".uir/knowledge/records")]),
                   lambda b: b["origin"].update(assumptions=[True])]
        for change in changes:
            with self.subTest(change=change):
                body = copy.deepcopy(original)
                change(body)
                record, path = self.record(body, publish=False)
                self.assert_error("invalid_knowledge", lambda: validate_record(record, "sample", path))
        record, path = self.record(original, publish=False)
        for changed in (dict(record, project_id="foreign"), dict(record, record_id="sha256:" + "0" * 64),
                        dict(record, format="future")):
            self.assert_error("invalid_knowledge", lambda: validate_record(changed, "sample", path))
        self.assert_error("invalid_knowledge", lambda: validate_record(record, "sample", path.replace("purpose", "other")))

    def test_invalid_json_formatting_and_resource_bound_fail_without_partial_view(self):
        record, path = self.record(self.body())
        valid = canonical(record) + b"\n"
        cases = [b"\xff\n", valid.replace(b"\n", b"\r\n"), valid.rstrip(b"\n"),
                 b'{"format":"x","format":"x"}\n', b'{"bad":NaN}\n',
                 b"[" * 2000 + b"0" + b"]" * 2000 + b"\n", b" " * (MAX_RECORD_BYTES + 1)]
        for data in cases:
            with self.subTest(prefix=data[:20]):
                self.write(path, data)
                self.assert_error("invalid_knowledge", self.inspection)

    def test_boolean_offsets_and_missing_document_wording_rejected(self):
        for field in ("start_byte", "end_byte"):
            body = self.document_body()
            body["evidence"][0][field] = True
            record, path = self.record(body, publish=False)
            self.assert_error("invalid_knowledge", lambda: validate_record(record, "sample", path))
        body = self.document_body()
        body["text"] = "A paraphrase."
        record, path = self.record(body, publish=False)
        self.assert_error("invalid_knowledge", lambda: validate_record(record, "sample", path))

    def test_ignore_and_boundary_gaps_never_claim_empty_complete_knowledge(self):
        self.record(self.body())
        self.write(".gitignore", ".uir/knowledge/\n")
        output = self.inspection()
        self.assertFalse(output["coverage"]["complete"])
        self.assertEqual(output["coverage"]["gaps"][0]["reason"], "gitignore")
        self.assertEqual(output["summary"]["revisions"], 0)
        self.assert_error("unknown_knowledge", lambda: self.inspection(selected_id="purpose"))

    def test_linked_store_is_not_followed(self):
        outside = self.base / "outside"
        outside.mkdir()
        target = self.root / ".uir/knowledge"
        try:
            target.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Creating symlinks is unavailable.")
        output = self.inspection()
        self.assertFalse(output["coverage"]["complete"])
        self.assertEqual(output["summary"]["revisions"], 0)

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_windows_junction_store_is_a_gap(self):
        outside = self.base / "outside"
        outside.mkdir()
        target = self.root / ".uir/knowledge"
        subprocess.run(["cmd", "/c", "mklink", "/J", str(target), str(outside)],
                       capture_output=True, check=True)
        output = self.inspection()
        self.assertFalse(output["coverage"]["complete"])
        self.assertEqual(output["coverage"]["gaps"][0]["reason"], "link")
        self.assertEqual(output["summary"]["revisions"], 0)

    def test_checked_in_fictional_fixture(self):
        root = Path(__file__).resolve().parents[1] / "examples/fixtures/knowledge-project"
        output = inspect_knowledge(root, full=True)
        self.assertEqual(output["summary"]["revisions"], 4)
        self.assertEqual(output["summary"]["logical_ids"], 2)
        self.assertEqual(output["summary"]["competing_groups"], 1)
        self.assertEqual(output["summary"]["unverified_developer_statements"], 3)
        self.assertTrue(output["coverage"]["complete"])
        self.assertEqual(output["summary"]["evidence_status"], {"matches": 4})

    def test_empty_store_and_missing_project_id_are_distinct(self):
        self.assertTrue(self.inspection()["coverage"]["complete"])
        (self.root / ".uir/config/project.json").unlink()
        self.assert_error("knowledge_unavailable", self.inspection)

    def test_unexpected_store_files_fail(self):
        self.write(STORE + "/draft.txt", "not an immutable revision")
        self.assert_error("invalid_knowledge", self.inspection)

    def test_edit_during_read_reconciles_and_repeated_edits_fail_closed(self):
        from universal_ir import knowledge
        self.record(self.document_body())
        read = knowledge._read_bytes
        edited = False

        def once(root, entry, **kwargs):
            nonlocal edited
            data = read(root, entry, **kwargs)
            if kwargs.get("window") is not None and not edited:
                edited = True
                self.write("README.md", "Changed while inspecting.\n")
            return data

        with patch("universal_ir.knowledge._read_bytes", side_effect=once):
            self.assertEqual(self.first()["evidence_status"], "changed")
        attempts = 0

        def always(root, entry, **kwargs):
            nonlocal attempts
            data = read(root, entry, **kwargs)
            attempts += 1
            self.write("src/main.py", f"edit {attempts}\n")
            return data

        with patch("universal_ir.knowledge._read_bytes", side_effect=always):
            self.assert_error("unstable_inputs", self.inspection)

    def test_torn_invalid_record_is_retried_if_inputs_changed(self):
        from universal_ir import knowledge
        record, path = self.record(self.body())
        self.write(path, b"invalid\n")
        read = knowledge._read_bytes
        fixed = False

        def repair(root, entry, **kwargs):
            nonlocal fixed
            data = read(root, entry, **kwargs)
            if not fixed:
                fixed = True
                self.write(path, canonical(record) + b"\n")
            return data

        with patch("universal_ir.knowledge._read_bytes", side_effect=repair):
            self.assertEqual(self.first()["evidence_status"], "matches")

    def test_equivalent_checkouts_and_real_cli_contract(self):
        self.record(self.body())
        other = self.base / "other"
        for path in self.root.rglob("*"):
            destination = other / path.relative_to(self.root)
            if path.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(path.read_bytes())
        self.assertEqual(self.inspection()["snapshot"], inspect_knowledge(other)["snapshot"])
        process = subprocess.run([sys.executable, "-B", "-m", "universal_ir", "knowledge", str(self.root),
                                  "--id", "purpose", "--limit", "1"], capture_output=True, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["records"]["total"], 1)
        self.assertEqual(process.stderr, b"")

    def test_cli_errors_and_argument_limits(self):
        for arguments, code, format_name in [
            (["--limit", "0"], "invalid_arguments", FORMAT),
            (["--offset", "-1"], "invalid_arguments", FORMAT),
            (["--id", "../bad"], "invalid_arguments", FORMAT),
            (["--id", "missing"], "unknown_knowledge", FORMAT),
            (["--approved"], "invalid_arguments", "uir.inventory.v1"),
        ]:
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = main(["knowledge", str(self.root)] + arguments)
            self.assertEqual(status, 2)
            self.assertEqual(stdout.getvalue(), "")
            error = json.loads(stderr.getvalue())
            self.assertEqual(error["error"]["code"], code)
            self.assertEqual(error["format"], format_name)


if __name__ == "__main__":
    unittest.main()
