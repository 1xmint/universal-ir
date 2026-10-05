# Knowledge acceptance protocol draft

**Status:** Proposed design for the next increment. No writer, acceptance ledger, lock implementation, or live user-event adapter exists. The [receipt verifier](host-receipts-v1.md) authenticates assertions under a caller-pinned policy; it does not implement this protocol.

The subsequent [logical contract and executable model](knowledge-acceptance-model.md) now specify decision information, inert staging, exact retries, event conflicts, and imported-history outcomes under explicit assumptions. Only that in-memory development model runs; no physical transaction or effective-intent reader is implemented. This draft retains the host/platform gates.

The optional [WebAuthn review assertion component](webauthn-review-v1.md) now checks a host-configured credential against exact current preparation. Its software-credential tests do not establish real enrollment, protected review display, or human authentication; stage 1 and all physical transaction gates remain open.

## Required boundary

A trusted host owns actual user authentication, selected conversation events, signing access, policy distribution, and project write permission. A model may propose a complete candidate; it cannot choose the trust pin, approve itself, supply a trusted event registry, or bypass acceptance checks. `stated` requires exact authenticated utterance and attributable scope/transition; otherwise require explicit approval of the complete proposed statement. Signed claims from a fictional test signer do not demonstrate a real developer channel.

Before a writer is accepted, select and demonstrate one concrete host adapter with an authenticated human-event boundary, a model tool schema that fixes trusted parameters outside model arguments, and an isolated signer. General shell access to host secrets or policy administration defeats that boundary. A provider-independent harness is the first candidate, with subscription-host adapters following when their actual event/permission contracts can be demonstrated.

The internal [harness verification tool](harness-verification-v1.md) now implements the narrow request/pinned-configuration part for verification only. It supplies no actual event channel, signer isolation, durable event consumption, or acceptance; it does not satisfy this writer gate.

Read-only [candidate preparation](knowledge-preparation-v1.md) now validates and previews an external record against current inputs and included structural history. It supplies a review base before storage, not approved/accepted heads or an authenticated action. Stage 1's user action and all transaction stages remain unimplemented.

Separate [prepared-candidate verification](prepared-receipts-v1.md) now binds a signed host assertion to that exact reconstructed review and rejects stale context. Its host-fixed registry is a verification lookup, not an authenticated event registry or accepted-head ledger. Publication changes the live full snapshot; this verifier cannot derive historical accepted intent afterwards. A writer needs durable reviewed-base/acceptance records and a separately specified resolver. Stage 1's actual human event and all transaction stages remain open.

## Candidate and preconditions

A candidate must carry the exact versioned record, evidence references, expected current source/inventory projection, and expected accepted heads for its logical identity. The host retains the base conditions outside an untrusted model's approval claim. Record/receipt IDs cover exact wording, scope, origin, and supersession. Approval of a changed record requires a fresh host assertion; hashes are identity, not permission.

Validate current source and required references before acceptance. Reject unresolved/changed evidence when it is a candidate precondition; keep earlier declared requirements despite later implementation changes. A declaration about a future path may have unresolved scope when deliberately approved, but cannot claim evidence from an unavailable file. Specify that distinction in the writer contract rather than treating all unknowns as success or banning future intent.

Expected heads must match the accepted state while holding the project/checkout acceptance lock. Candidate supersession must cover the transition being authorized. Resolving a fork requires every competing accepted head, not a chosen newer child. Keep unverified candidates and all prior revisions visible without allowing them to remove accepted intent. Independent logical statements can contradict; textual contradiction detection is not supplied by structural validation.

## Proposed transaction stages

1. **Prepare outside active storage.** Build canonical candidate/receipt bytes and identity, validate schema/references, and collect trusted user action. This grants no source write or accepted knowledge state.
2. **Serialize acceptance.** Acquire a cross-process, project/checkout-scoped host-controlled lock. Specify Windows/Linux behavior, bounded contention/failure reporting, crash release, and filesystem support. GitHub membership is not a lock or workspace identity.
3. **Reconcile under the lock.** Verify fresh source, pinned current policy, exact approval, expected accepted heads, and complete evidence. Reject stale source/heads for reconciliation. The lock serializes Universal IR writers; arbitrary external source writers still require explicit optimistic observation limits or stronger frozen-input conditions.
4. **Check durable event use.** Key registry entries by project/host/event. An identical completed record/action/receipt retry is idempotent; a different record or action for the same event is rejected. Registry identity/history must travel with accepted state and cannot be supplied solely by a model. Define merged-branch conflicting-event outcomes too.
5. **Stage immutable artifacts.** Store candidate, receipt, and proposed acceptance decision without changing the effective accepted set. Protect paths, compare existing bytes by identity, preserve unrelated source/dirty files, and never overwrite a prior revision.
6. **Publish one acceptance marker.** Define an atomic commit point covering the exact artifact IDs, base heads/source conditions, and event use. Only a complete, verified marker can advance effective accepted intent. Files alone or a partial set cannot activate a declaration.
7. **Recover and report.** Classify crashes before/after the commit point, retry the same operation safely, retain complete committed acceptance, and leave uncommitted artifacts pending. Never repair source backwards to match a cached graph. Release the lock and return an inspectable result.

Before implementation, fix marker/event/lock schemas and storage, exact commit/durability primitives, validation order, operation identity, orphan handling, and reader derivation. The current reader shows structural history only; a future accepted-intent resolver must distinguish bare records, staged artifacts, committed markers, and currently verifiable host assertions. If imported accepted branches diverge, expose competing heads instead of inventing a global last writer.

## Required executable evidence

| Case | Required outcome before shipping a writer |
| --- | --- |
| Authenticated user states or approves exact candidate | Host assertion binds the actual event and complete record; model cannot substitute signer/policy/event parameters. |
| Wording, scope, predecessor, or source base changes | Reject stale/unauthorized candidate; previous accepted set survives. |
| Two processes accept the same base | Serialization and expected-head checks prevent lost updates; losing candidate requires reconciliation. |
| Same operation retried after response loss | Return the same committed result; no duplicate acceptance/event use. |
| Same event used for another statement/action | Reject conflict, including after restart/import. |
| Crash during staging or before marker | Previous accepted set remains; partial artifacts stay pending and recoverable. |
| Crash after marker but before response | Complete accepted result survives and can be recovered idempotently. |
| Revoked/expired/unavailable policy or bad proof | No new accepted declaration. Imported/offline claims remain visibly unverified where proof cannot be established. |
| Two published branches contain accepted knowledge forks | Preserve both and require authorized resolution covering all heads. |
| External edits, ignored evidence, unsafe paths, failed filesystem write | Fail closed for acceptance; preserve unrelated source and prior complete state. |

This draft is reviewable preparation for the writer gate, not completion evidence. Choose primitives only after the live-host boundary and platform failure tests can be reproduced. The full program-format and coherence milestones remain open.
