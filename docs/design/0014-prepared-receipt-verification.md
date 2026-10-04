# 0014: Bind external candidate assertions to their review context

**Status:** Accepted through the pull request adopting this increment.

## Context

[Decision 0013](0013-read-only-knowledge-preparation.md) makes proposals inspectable before storage. The earlier receipt binding identifies exact record content but cannot bind its reviewed source snapshot and structural history. A stored-record verifier also cannot review an external proposal without first storing it.

Review identity is not authority. We still need a real authenticated user-event host and serialized acceptance before any writer. Default inspection must continue to report developer claims as unverified and pending.

## Decision

Add a distinct, fixed Ed25519 binding for external candidate assertions. Its exact payload includes the preparation identity and supports only `approved`. Use a separate signature domain and format; reject the old binding at the new entry point and vice versa. Reuse existing strict encoding, pinned trust-policy, grants, revocation, clock, and cryptographic checks without changing the old contract.

The core reconstructs the candidate review from actual project inputs and external candidate bytes. Require its identity to match an independently supplied preparation pin and the signed payload. Bracket host transport reads with matching preparations and repeated transport observations. This remains optimistic observation, with bounded retries and no successful stale report.

Offer a provisional source-run CLI and an internal host-configured handler. The latter receives only a preparation identity from the model. Trusted construction fixes the project, policy/pin, clock, and copied review registry mapping that identity to candidate/record/receipt inputs. Configuration and signing access still require host isolation from other model tools.

The [versioned contract](../specs/prepared-receipts-v1.md) defines encoding, outputs, failures, and compatibility. No signer, live event authentication, registry consumption, accepted-head ledger, or writer is added.

## Alternatives and consequences

Extending the old payload in place would break its exact schema and make record-only and context-bound meanings ambiguous. A distinct binding preserves compatibility and prevents signature reuse across profiles.

Requiring a candidate to enter the store before verification would mutate the very review base it describes. External transport and a virtual overlay preserve the project and its existing history.

Full inventory binding is conservative: even unrelated included changes require another review. This verifier reconstructs inputs repeatedly; no efficiency benefit is claimed. Candidate publication also changes its full snapshot, so this live-review operation cannot serve as a historical accepted-intent resolver. That needs a separate durable acceptance contract.

An authentic host assertion can reference unresolved support or incomplete coverage. Report those conditions without claiming accepted intent or complete semantics. Signature validity does not prove a human event occurred or that the proposed requirement is correct.

## Validation

`tests/test_prepared_receipts.py` exercises exact external review, source/configuration/proposal changes, stored-candidate invalidation, profile/domain separation, tampering, subject matching, grants/revocation/expiry, optional-backend failure, races, strict transport, handler injection, copied registries, CLI failures, and unchanged fixtures. The fictional demonstration runs the real CLI and handler, then rejects changed wording with the old review.

Run the existing receipt, harness, preparation, knowledge, inventory, cache, cost, and documentation suites as compatibility checks. Required Windows/Linux CI runs the new suite after optional pinned crypto installation. Review related documents and Markdown rendering before checked publication. Only this verification increment is complete; live-host and acceptance gates remain open.
