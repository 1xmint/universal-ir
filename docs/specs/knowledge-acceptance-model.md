# Knowledge acceptance: logical contract and executable model

**Status:** Accepted design/model increment under [decision 0015](../design/0015-acceptance-protocol-model.md). The protocol below is proposed production behavior. Only the in-memory development model is executable. No durable acceptance ledger, writer, authenticated human channel, or effective-intent reader is implemented.

## Purpose and limits

Make an approved declaration survive restart and collaboration without allowing a pending file, stale proposal, or repeated event to replace earlier intent. Source remains authoritative for implementation; a declaration cannot make a source file revert to an old cached state.

The [acceptance draft](knowledge-acceptance-draft.md) describes the overall host and transaction boundary. This contract fixes logical rules and examples without choosing physical commit, durability, locking, storage, or user-channel primitives. Real implementation must prove those separately. No production operation may treat the model's results or its test conditions as authorization.

## Four different states

| State | Meaning |
| --- | --- |
| External proposal | Exact candidate under review; no project enrollment or event consumption |
| Staged artifacts | Candidate/receipt bytes retained for a transaction; inert without a complete published decision |
| Committed history | Complete immutable decision and its required artifacts, bound to the original reviewed base |
| Currently verified intent | Historical decisions evaluated under the selected current authority policy, with source-support freshness reported separately; needs a future resolver |

The model represents the first three with symbolic records and assumes valid historical authority for its simulated published decisions. It does not implement the fourth. Existing `knowledge` still reports included structural history and unverified/pending developer claims.

## Decision information and identity

A future immutable decision must bind the following information. This is a required logical schema, not a chosen wire encoding or executable CLI syntax:

| Information | Required binding |
| --- | --- |
| Project and logical statement | Exact project identity and the record's logical identity |
| Artifacts | Full candidate record ID, exact receipt ID, and references needed to reconstruct original review evidence |
| Review | Preparation identity, original full inventory snapshot, and scoped source projection |
| Accepted base | Identified catalog of committed decisions used for review, plus exact accepted heads for this logical statement |
| Transition | Exact supersession and active/withdrawn state, already bound by the record ID |
| Host event | Project/host/event key, actor, approved action, and authenticated event binding; actor and complete origin must match the record/receipt |
| Trust observation | Independently pinned policy identity and the host's verification observation; a saved success flag is not proof |

The original accepted catalog must identify its marker set and dependencies so an importer can reconstruct that base rather than compare against today's merged heads. A catalog identity binds project, version, and sorted marker identities; its required referenced decisions must be available. A future signed review must cover this catalog, directly or through a specified included snapshot. A model-supplied catalog/head list is not a trusted base.

Operation identity must cover the full normalized decision input, including artifact, review, accepted-base, and event bindings. Exclude local paths, retry time, process ID, and mutable result labels. Identical normalized inputs give the same identity. Changed wording, event, proof, reviewed base, or requested transition is a different operation requiring its own eligible authorization. Digests identify content; they grant no permission.

The development model hashes a distinct `uir.acceptance-model-operation.v1` object containing symbolic project, record, preparation, source, expected-head, receipt, host/event, and action fields. Its record token stands for complete validated content. `review_current` stands for all original review/catalog checks. These abstractions omit production proof/catalog encodings; the model's digest must never be reused as a durable decision ID.

## State transition rules

1. **Acquire serialization.** One transaction owns a checkout's acceptance boundary. A contender receives a bounded busy result or waits according to a future lock contract. GitHub membership is not the boundary.
2. **Recognize an exact committed retry.** Verify the stored complete operation and its identity. Return its historical committed outcome without staging another decision or consuming another event. This acknowledges history; it does not reapprove the statement under current source or policy.
3. **Validate new work.** Require actual authenticated event, exact eligible receipt, current independently pinned policy, current reviewed inputs/catalog, complete required evidence, and complete acceptance coverage. A future scope can be explicitly approved without claiming nonexistent supporting evidence. Unknown semantics cannot become established facts through acceptance.
4. **Check heads and event use.** Expected accepted heads must equal the current set under serialization. Supersession must include every head being replaced, with all predecessor references in the same logical history. Withdrawal needs an existing head. The event key is `(project, host, event)`; only an exact completed operation retry can reuse it. Actor/action changes cannot bypass the key.
5. **Stage immutable artifacts.** Existing identity with different contents is a conflict, never an overwrite. Partial or complete staging has no effect on accepted history and consumes no event. Failed/aborted work can remain inspectable as pending artifacts.
6. **Reconcile at publication.** Recheck authority, review freshness, source, heads, event use, and artifact completeness before the commit point. Failed checks preserve the previous committed set. Serialization among participating writers does not freeze arbitrary source editors.
7. **Publish one complete decision.** Advancing accepted history and consuming the event have one logical commit point. A future reader derives event use from the same complete decision set, or from a transactional index whose equivalence is proven. An independently updated event file cannot be the sole authority.

For the first modeled operation, action is only `approved`, matching the prepared receipt profile. `stated` would require a separately demonstrated exact-utterance contract. This increment does not broaden the current signed profiles or add an acceptance API.

## Staging and the review snapshot

Current preparation binds the full inventory snapshot. Storing its candidate changes that snapshot. Therefore a writer cannot stage into the active store and then blindly rerun `verify-preparation` with the old pin; it will correctly report a stale live review.

The physical writer must specify an acceptance capture/publication profile: where inert staging lives, which transaction-owned bytes are excluded or accounted for, how changes to unrelated included inputs still invalidate review, and when the final observation occurs. It must preserve both the original reviewed manifest and the exact published artifacts. Any change to capture meaning requires versioned compatibility evidence. This model assumes that guard succeeds; it does not implement an exclusion rule or waive freshness checks.

After publication, verify historical approval against the preserved reviewed manifest/catalog and exact artifact bindings, not by pretending the old snapshot is current. Today's source freshness is a separate observation. The existing live-review verifier remains unchanged and cannot resolve historical acceptance.

Changed current source can make support stale or reveal a discrepancy; it does not silently withdraw or rewrite a declared requirement. Missing current authority stays visibly unresolved. Neither condition licenses a reader to revive an older declaration by dropping later committed history.

## Recovery and event reuse

| Interruption or retry | Required outcome |
| --- | --- |
| Before staging, after either artifact, or after all artifacts but before the decision | Previous committed set survives; staged artifacts remain inert; no event consumed |
| After complete publication but before response | Restart finds the same complete decision; exact retry acknowledges it once |
| Source or policy changes after complete publication | Historical retry can acknowledge the past decision; it grants no new current approval or write |
| Same event reused for different wording, action, receipt, review, or transition | Reject conflict; never treat it as an exact retry |
| Missing/corrupt artifact named by a committed decision | Report incomplete committed history; never silently omit the decision and revive an older head |
| Lock owner stops or crashes | A real host must prove bounded recovery/release on supported filesystems; the model merely clears its ideal lock on restart |

An aborted transaction does not reserve an event. It may need a new proof/review if inputs changed. Reusing an immutable artifact ID with different contents is still invalid, even when the previous transaction never committed.

In the model, a failed publication leaves the operation active until explicit `abort` or restart; staged artifacts remain inert. A real host must specify bounded failure cleanup and lock release rather than relying on this idealized lifecycle.

Atomic visibility and crash durability are different obligations. The model assumes both. A real implementation must test process interruption, failed writes, unsupported filesystems, and its stated power-loss guarantees, including required flushes. No rename, database, lock, directory, or network storage primitive is selected here.

## Published collaboration and import

Combine complete histories by immutable identity without a timestamp winner. Alice and Sally can independently accept successors of the same base in separate checkouts. Their merged history has both heads; a later authorized resolution must cover all heads. Importing history does not rebase source or make another checkout's source token current.

Deduplicate identical decisions. For different decisions using the same project/host/event key, report event conflict and preserve both for diagnosis; no partial accepted view or automatic winner. Distinct events can produce legitimate competing heads. Missing prerequisites, invalid identities, cycles, cross-logical ancestry, or conflicting contents block complete resolution instead of producing a plausible reduced history.

Production import must additionally verify authenticated markers/receipts, original review/catalog evidence, producer trust, completeness, and compatibility. A JSON object, repository file, committed success label, or model-created marker is insufficient. If current policy/proof is unavailable or revoked, preserve history and expose unresolved authority. Do not silently restore older intent. The model merges only simulated locally committed histories and supplies no such proof verification.

## Executable evidence and remaining gates

Run `python -B scripts/acceptance_model.py` for a fixed abstract demonstration and `python -m unittest discover -s tests -p test_acceptance_model.py -v` for the model scenarios. Use the environment paths in [CONTRIBUTING](../../CONTRIBUTING.md#local-checks). All dependencies are standard-library; no Git, source project, crypto, API key, or model call is needed by this script.

Tests enumerate both artifact staging orders and every prepublication prefix, plus stale inputs/prerequisites, contenders, response loss, event reuse, withdrawal, forks, resolution, and incomplete/conflicting histories. These are bounded scenarios, not exhaustive verification or physical/security evidence. Default conditions reject new work; named true conditions are test oracles, not a host interface.

Before a writer ships, demonstrate a concrete protected authenticated approval channel, final durable/proof/catalog encodings, real historical verification, accepted-intent reader behavior, capture/staging rules, cross-process serialization, commit/durability, and Windows/Linux recovery. Keep these gates open in the [roadmap](../../ROADMAP.md). The [walkthrough](../../examples/acceptance-protocol.md) makes the modeled cases concrete.
