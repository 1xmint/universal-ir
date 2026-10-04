"""Protocol invariants under explicit test oracles, not real writer/security tests."""

from dataclasses import replace
from itertools import permutations
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.acceptance_model import Conditions, ModelError, Operation, Protocol, Record


READY = Conditions(True, True, True, True, True, True)


def candidate(record_id="r1", *, logical_id="retention", heads=(), supersedes=None, event=None, receipt=None, **options):
    record = Record(logical_id, record_id, heads if supersedes is None else supersedes)
    return Operation("sample", record, f"review-{record_id}", "source-1", heads,
                     receipt or f"proof-{record_id}", "host", event or f"event-{record_id}", **options)


def commit(world, operation):
    world.start(operation, READY)
    world.stage("record")
    world.stage("receipt")
    world.publish(READY)


class AcceptanceModelTests(unittest.TestCase):
    def assert_error(self, code, call):
        with self.assertRaises(ModelError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def base(self):
        world = Protocol()
        commit(world, candidate())
        return world

    def fork(self, *, event=None):
        base = self.base()
        alice, sally = base.restart(), base.restart()
        commit(alice, candidate("r2", heads=("r1",), event=event))
        commit(sally, candidate("r3", heads=("r1",), event=event))
        return base, alice, sally

    def test_default_conditions_cannot_approve_a_model_claim(self):
        world = Protocol()
        self.assert_error("attribution_required", lambda: world.start(candidate()))
        self.assertIsNone(world.active)
        self.assertFalse(world.markers)

    def test_every_unestablished_precondition_rejects_without_state_change(self):
        for field, code in (("authenticated_event", "attribution_required"), ("receipt_valid", "receipt_invalid"),
                            ("policy_current", "policy_not_current"), ("review_current", "stale_preparation"),
                            ("evidence_ready", "unresolved_evidence"), ("coverage_complete", "incomplete_coverage")):
            with self.subTest(field=field):
                world = self.base()
                before = world.resolve()
                self.assert_error(code, lambda: world.start(candidate("r2", heads=("r1",)), replace(READY, **{field: False})))
                self.assertEqual(world.resolve(), before)
                self.assertIsNone(world.active)

    def test_partial_and_complete_staging_do_not_activate_or_consume_events(self):
        for order in permutations(("record", "receipt")):
            for prefix in range(3):
                with self.subTest(order=order, prefix=prefix):
                    world = self.base()
                    before = world.resolve()
                    world.start(candidate("r2", heads=("r1",)), READY)
                    for kind in order[:prefix]:
                        world.stage(kind)
                    restarted = world.restart()
                    self.assertEqual(restarted.resolve(), before)
                    self.assertIsNone(restarted.active)
                    self.assertEqual(len(restarted.markers), 1)

    def test_all_prepublication_crash_prefixes_can_retry_once(self):
        for order in permutations(("record", "receipt")):
            for prefix in range(3):
                world, operation = self.base(), candidate("r2", heads=("r1",))
                world.start(operation, READY)
                for kind in order[:prefix]:
                    world.stage(kind)
                restarted = world.restart()
                commit(restarted, operation)
                self.assertEqual(restarted.resolve()["heads"], {"retention": ["r2"]})
                self.assertEqual(len(restarted.markers), 2)

    def test_missing_staging_blocks_commit_and_preserves_old_state(self):
        world = self.base()
        world.start(candidate("r2", heads=("r1",)), READY)
        world.stage("record")
        self.assert_error("incomplete_staging", lambda: world.publish(READY))
        self.assertEqual(world.resolve()["heads"], {"retention": ["r1"]})

    def test_after_commit_crash_and_response_loss_are_idempotent(self):
        world, operation = self.base(), candidate("r2", heads=("r1",))
        commit(world, operation)
        restarted = world.restart()
        before = restarted.resolve()
        self.assertEqual(restarted.start(operation), "already_committed")
        self.assertEqual(restarted.resolve(), before)
        self.assertEqual(len(restarted.markers), 2)
        self.assertIsNone(restarted.active)

    def test_historical_retry_does_not_require_new_source_or_authorize_new_work(self):
        world = self.base().restart()
        world.source_id = "source-2"
        self.assertEqual(world.start(candidate()), "already_committed")
        self.assertIsNone(world.active)
        self.assert_error("no_active_operation", lambda: world.stage("record"))
        self.assertEqual(world.resolve()["heads"], {"retention": ["r1"]})

    def test_source_changed_before_acceptance_rejects(self):
        world = self.base()
        world.source_id = "source-2"
        self.assert_error("stale_source", lambda: world.start(candidate("r2", heads=("r1",)), READY))
        self.assertEqual(world.resolve()["heads"], {"retention": ["r1"]})

    def test_source_changed_during_staging_rejects_at_commit_point(self):
        world = self.base()
        world.start(candidate("r2", heads=("r1",)), READY)
        world.stage("record")
        world.stage("receipt")
        world.source_id = "source-2"
        self.assert_error("stale_source", lambda: world.publish(READY))
        self.assertEqual(world.resolve()["heads"], {"retention": ["r1"]})

    def test_authority_and_support_are_rechecked_after_staging(self):
        for field in ("authenticated_event", "receipt_valid", "policy_current", "review_current", "evidence_ready", "coverage_complete"):
            world = self.base()
            world.start(candidate("r2", heads=("r1",)), READY)
            world.stage("record")
            world.stage("receipt")
            with self.assertRaises(ModelError):
                world.publish(replace(READY, **{field: False}))
            self.assertEqual(len(world.markers), 1)

    def test_two_actors_same_base_do_not_lose_an_update(self):
        world = self.base()
        alice, sally = candidate("r2", heads=("r1",)), candidate("r3", heads=("r1",))
        world.start(alice, READY)
        self.assert_error("busy", lambda: world.start(sally, READY))
        world.stage("record")
        world.stage("receipt")
        world.publish(READY)
        self.assert_error("stale_heads", lambda: world.start(sally, READY))
        self.assertEqual(world.resolve()["heads"], {"retention": ["r2"]})

    def test_same_event_for_different_operation_is_rejected_after_restart(self):
        world = self.base().restart()
        self.assert_error("event_conflict", lambda: world.start(candidate("r2", heads=("r1",), event="event-r1"), READY))
        self.assert_error("event_conflict", lambda: world.start(replace(candidate(), receipt_id="another-proof"), READY))
        self.assertEqual(len(world.markers), 1)

    def test_event_namespace_includes_host_and_project(self):
        world = self.base()
        next_operation = replace(candidate("r2", heads=("r1",), event="event-r1"), host_id="other-host")
        commit(world, next_operation)
        self.assertEqual(len(world.resolve()["events"]), 2)
        self.assert_error("project_mismatch", lambda: world.start(replace(candidate("r3", heads=("r2",)), project_id="other"), READY))

    def test_abort_does_not_consume_event_or_remove_prior_intent(self):
        world = self.base()
        world.start(candidate("r2", heads=("r1",), event="new-event"), READY)
        world.stage("record")
        world.abort()
        commit(world, candidate("r3", heads=("r1",), event="new-event"))
        self.assertIn("r2", world.records)
        self.assertNotIn("r2", world.resolve()["accepted"])
        self.assertEqual(world.resolve()["heads"], {"retention": ["r3"]})

    def test_pending_artifacts_cannot_silently_remove_a_requirement(self):
        world = self.base()
        pending = replace(candidate("r2", heads=("r1",)), record=Record("retention", "r2", ("r1",), "withdrawn"))
        world.start(pending, READY)
        world.stage("record")
        world.stage("receipt")
        self.assertEqual(world.resolve()["accepted"]["r1"].state, "active")
        self.assertEqual(world.resolve()["heads"], {"retention": ["r1"]})

    def test_explicit_withdrawal_keeps_prior_revision_as_history(self):
        world = self.base()
        operation = replace(candidate("r2", heads=("r1",)), record=Record("retention", "r2", ("r1",), "withdrawn"))
        commit(world, operation)
        resolved = world.resolve()
        self.assertEqual(resolved["heads"], {"retention": ["r2"]})
        self.assertEqual(resolved["accepted"]["r2"].state, "withdrawn")
        self.assertEqual(resolved["accepted"]["r1"].state, "active")
        self.assert_error("invalid_transition", lambda: Protocol().start(replace(candidate(), record=Record("retention", "r1", (), "withdrawn")), READY))

    def test_imported_branches_keep_both_heads_regardless_of_order(self):
        base, alice, sally = self.fork()
        forward, reverse = alice.merge(sally).resolve(), sally.merge(alice).resolve()
        self.assertEqual(forward, reverse)
        self.assertEqual(forward["heads"], {"retention": ["r2", "r3"]})
        self.assertEqual(base.resolve()["heads"], {"retention": ["r1"]})

    def test_resolution_must_cover_every_competing_head(self):
        _, alice, sally = self.fork()
        world = alice.merge(sally)
        self.assert_error("stale_heads", lambda: world.start(candidate("r4", heads=("r2",)), READY))
        self.assert_error("invalid_transition", lambda: world.start(candidate("r4", heads=("r2", "r3"), supersedes=("r2",)), READY))
        commit(world, candidate("r4", heads=("r2", "r3")))
        self.assertEqual(world.resolve()["heads"], {"retention": ["r4"]})
        self.assertEqual(set(world.resolve()["accepted"]), {"r1", "r2", "r3", "r4"})

    def test_import_does_not_rebase_the_local_source_observation(self):
        _, alice, sally = self.fork()
        alice.source_id, sally.source_id = "alice-dirty", "sally-source"
        merged = alice.merge(sally)
        self.assertEqual(merged.source_id, "alice-dirty")
        self.assertEqual(merged.resolve()["heads"], {"retention": ["r2", "r3"]})
        self.assert_error("stale_source", lambda: merged.start(candidate("r4", heads=("r2", "r3")), READY))

    def test_merged_event_conflict_has_no_timestamp_winner_or_partial_view(self):
        base, alice, sally = self.fork(event="same-event")
        merged = alice.merge(sally)
        self.assert_error("event_conflict", merged.resolve)
        self.assertEqual(len(merged.markers), 3)
        self.assertEqual(base.resolve()["heads"], {"retention": ["r1"]})

    def test_broken_committed_artifacts_do_not_revive_old_heads(self):
        for kind in ("record", "receipt"):
            world = self.base()
            operation = candidate("r2", heads=("r1",))
            commit(world, operation)
            if kind == "record":
                del world.records["r2"]
            else:
                del world.receipts["proof-r2"]
            self.assert_error("incomplete_commit", world.resolve)
            self.assert_error("incomplete_commit", lambda: world.start(candidate("r3", heads=("r2",)), READY))

    def test_identity_conflicts_never_overwrite_staged_artifacts(self):
        world = self.base()
        operation = candidate("r2", heads=("r1",), receipt="proof-r1")
        world.start(operation, READY)
        original = world.receipts.copy()
        self.assert_error("artifact_conflict", lambda: world.stage("receipt"))
        self.assertEqual(world.receipts, original)
        other = world.restart()
        other.records["r1"] = Record("other", "r1")
        self.assert_error("artifact_conflict", lambda: world.merge(other))

    def test_missing_cross_logical_and_cyclic_predecessors_fail(self):
        world = self.base()
        self.assert_error("invalid_transition", lambda: world.start(candidate("r2", heads=("r1",), supersedes=("missing", "r1")), READY))
        self.assert_error("invalid_transition", lambda: world.start(candidate("r2", logical_id="other", supersedes=("r1",)), READY))
        cyclic = Protocol()
        for operation in (candidate("a", supersedes=("b",)), candidate("b", supersedes=("a",))):
            cyclic.records[operation.record.record_id] = operation.record
            cyclic.receipts[operation.receipt_id] = operation.receipt_subject
            cyclic.markers[operation.operation_id] = operation
        self.assert_error("invalid_transition", cyclic.resolve)

    def test_marker_identity_and_duplicate_record_imports_fail(self):
        world = self.base()
        marker = next(iter(world.markers.values()))
        world.markers = {"wrong": marker}
        self.assert_error("invalid_marker", world.resolve)
        first, second = Protocol(), Protocol()
        commit(first, candidate(event="one"))
        commit(second, candidate(event="two", receipt="other-proof"))
        self.assert_error("duplicate_record", first.merge(second).resolve)

    def test_model_inputs_are_immutable_and_do_not_establish_real_identity(self):
        self.assert_error("invalid_model_input", lambda: Record("retention", "r1", ("b", "a")))
        self.assert_error("invalid_model_input", lambda: Record("retention", "r1", ("r1",)))
        self.assert_error("invalid_model_input", lambda: Conditions(authenticated_event="yes"))
        self.assert_error("invalid_model_input", lambda: replace(candidate(), action="stated"))
        with self.assertRaises(AttributeError):
            candidate().event_id = "replacement"

    def test_real_demo_reports_assumptions_and_inert_staging(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-B", "scripts/acceptance_model.py"], cwd=root, capture_output=True, check=True)
        report = json.loads(result.stdout)
        self.assertEqual(report["kind"], "abstract_protocol_model")
        self.assertEqual(report["before_marker_heads"], {})
        self.assertEqual(report["after_marker_heads"], {"retention": ["r1"]})
        self.assertEqual(report["retry_after_source_change"], "already_committed")
        self.assertEqual(report["markers"], 1)
        self.assertFalse(report["authority"]["project_writes"])
        self.assertEqual(report["authority"]["human_authentication"], "assumed_not_demonstrated")


if __name__ == "__main__":
    unittest.main()
