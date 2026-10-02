# Project knowledge records and attribution

**Status:** Accepted specification increment under [decision 0009](../design/0009-knowledge-and-cost-gates.md). No knowledge reader, writer, receipt verifier, or agent-host adapter is implemented. Inventory still treats these files as ordinary opaque source. This contract does not select an executable IR encoding or expose a public API.

## Purpose and authority

Keep useful project purpose, requirements, and decisions across development sessions. Let an existing agent propose explanations from evidence, and let developers correct them in normal conversation. Preserve the difference between an interpretation, a document's declaration, and a verified developer statement.

Source files own implemented behavior. Knowledge owns recorded statements about intent; agreeing with implementation needs separate evidence. A structurally valid record or matching hash is not proof of truth, approval, or authorship. The existing host owns model calls, consent, trusted developer identity, and the decision to capture a project-relevant statement. Do not store complete chat logs, credentials, or transient task instructions by default.

## Storage and record shape

An adopting project must have version-1 configuration with a nonempty `project_id` before knowledge can be accepted. Store immutable revisions in `.uir/knowledge/records/<id>/<record-digest>.json`, committed through ordinary project review. The filename is the hexadecimal part of `record_id`. Local drafts stay outside durable records. Never create this layout in Universal IR merely to document it.

The envelope has exactly `format`, `project_id`, `record_id`, and `body`. Format is `uir.knowledge.v1`; project identity must match configuration. Compute `record_id` as SHA-256 of canonical UTF-8 JSON containing `format`, `project_id`, and `body`, using the [inventory canonical encoding](local-inventory-v1.md#identity-and-evidence). Do not include `record_id` in its own hash. Unknown fields/versions, duplicate keys, non-finite numbers, and invalid UTF-8 fail validation. Durable records use LF and a final newline.

| Body field | Exact meaning |
| --- | --- |
| `id` | Stable, project-local logical identity matching `[a-z][a-z0-9_-]{0,63}`. Revisions keep this identity. |
| `category` | One of `purpose`, `requirement`, `decision`, or `summary`. Category does not confer authority. |
| `text` | Nonempty UTF-8 statement. Exact approved wording is part of identity. |
| `scope` | Nonempty, unique list of literal project-relative paths, including `.` for the whole project. Use inventory path rules. Future/absent paths may be declared but must remain unresolved in views. |
| `origin` | Exactly one of the shapes below. It records a claim of origin; verification is separate. |
| `input_id` | Source-evidence projection ID below for an AI interpretation; null for a declaration. |
| `evidence` | Ordered list of the reference shapes below. Empty only for a developer statement without source evidence. |
| `supersedes` | Unique list of predecessor record IDs for the same logical identity and project; empty for its initial revision. |
| `state` | `active` or `withdrawn`. Withdrawal retains the text/history and requires the same authority as changing that declaration. |

All fields are required. Lists preserve declared order in identity. A withdrawn revision must supersede at least one predecessor. Do not infer requirements from category, recency, a Git author string, or the act of committing a record.

Origins have these exact fields:

- AI interpretation: `kind: ai_interpretation`, nonempty `host_id`, nonempty `method`, and `assumptions` (a list of strings). A host/model label is descriptive attribution, not proof of approval. An interpretation needs at least one source or record reference.
- Document declaration: `kind: document_declaration`. Require one document reference whose quoted text equals `text` exactly. That path must be in the configured document list. The result is a document's stated intent, not authenticated conversational approval. Paraphrases remain AI interpretations.
- Developer statement: `kind: developer_statement`, nonempty `host_id`, `event_id`, and `actor_id`. These are host-scoped opaque strings, not GitHub membership partitions or authentication proof by themselves. Acceptance requires the separate host check below.

Evidence has these exact alternatives:

- File: `kind: file`, `path`, and `content_id`, where the digest hashes exact file bytes.
- Document: `kind: document`, `path`, `content_id`, `start_byte`, `end_byte`, and `quote`. Offsets are zero-based, end-exclusive integers with `0 <= start_byte < end_byte`; the selected bytes must decode as UTF-8 and equal the quote. Keep the original document in place.
- Record: `kind: record` and `record_id`, referencing an immutable revision in the same project.

Every digest uses `sha256:` plus 64 lowercase hexadecimal characters. Integer offsets exclude booleans. File/document evidence must identify an included regular file when accepted; it cannot target `.uir/knowledge/` or that directory itself. Use record references for durable knowledge dependencies rather than hashing a record as its own source. Unavailable or changed evidence is visible in inspection and cannot be silently rebound. Runtime observations, test coverage claims, and compiler facts retain separate future contracts; this format cannot establish them merely through text.

## Source dependencies without circular identity

AI interpretations use an input projection derived from a fresh inventory. Its exact fields are `format: uir.knowledge-input.v1`, `extractor`, `ignore_engine`, `configuration`, `controls`, `scope`, `entries`, and `omissions`.

Copy extractor, ignore engine, effective configuration, and all control hashes from the inventory. Copy the record's scope list. Include inventory entries/omissions within any scope path, in their original order, except paths equal to `.uir` or beginning `.uir/`. Include `.` when in scope. A path is within `.` unconditionally, or within another scope when equal to it or starting with that path plus `/`. Hash the projection with the same canonical encoding.

This is an evidence-input ID, not an inventory snapshot or an executable graph. Configuration and ignore controls remain dependencies even though metadata entries are excluded. Knowledge dependencies use explicit record references. Excluding `.uir/` entries avoids an interpretation invalidating itself merely because it is persisted. For the same reason, source metadata outside configuration/control hashes must use explicit file references when relevant.

Scoped additions, removals, edits, boundaries, and omission changes alter the projection. Global configuration/ignore-control changes conservatively invalidate it. Ignored contents, unlisted external inputs, and runtime state remain unknown. Evidence matching means the identified inputs match; it does not mean a model's interpretation is correct or exhaustive. A changed input marks an interpretation stale and allows a new proposal; it never silently rewrites a declaration or triggers a paid model call.

## Host attribution boundary

A trusted host verifier must be configured outside model-supplied records. The host binds project, exact record ID/wording, actor, event, and action (`stated` for an exact utterance or `approved` for explicit approval of the proposed wording). Scope and supersession are covered by the record ID. Merely approving a general task does not approve every generated requirement.

The conceptual receipt payload has exactly `format: uir.knowledge-receipt.v1`, `project_id`, `record_id`, `host_id`, `event_id`, `actor_id`, `action`, and a UTC `recorded_at` timestamp. A future binding must specify authenticated transport or signature proof, host trust configuration, replay handling, revocation, and offline verification. No binding or proof encoding is selected in this increment, so no implementation may label a claimed receipt verified yet.

Receipts refer to the completed record ID; records do not embed receipt hashes. This avoids a circular hash dependency. A host may retain the selected utterance/proof or a privacy-preserving verifiable reference; a whole conversation archive is not required. A bare receipt payload, a hash of a transcript, or a model's `approved: true` assertion is insufficient. Changing one byte of a record requires fresh approval of that new ID.

On an authenticated live host channel, the future adapter may verify an exact user event or explicit confirmation. On import or offline restart, verify through the selected binding; otherwise retain `unverified_attribution`. Missing/unsupported proof must not downgrade the record's claimed origin to hide the problem or treat it as authoritative intent. An agent without a supported host can still submit labeled interpretations and document links.

## History, conflicts, and working views

Keep all revisions. Supersession references must exist and stay within the same project/logical identity. The combined supersession and record-evidence dependency graph must be acyclic, including no self-reference. There is no numeric latest revision or timestamp-based winner. Concurrent children of the same predecessor are competing heads; display the fork until an explicit resolution supersedes all competing heads. A source merge or byte-valid record does not resolve meaning automatically.

Acceptance of a declaration's correction, withdrawal, or resolution requires authorized evidence covering that transition. An unverified head or AI paraphrase cannot remove the previously accepted declaration from effective intent. Keep it visible alongside pending candidates. Separate logical identities can also disagree; record a reported conflict with evidence and seek an explicit resolution. Text contradiction detection is not established by this specification.

Views report separate dimensions: claimed origin; attribution (`verified`, `unverified_attribution`, or `not_applicable`); evidence (`matches`, `changed`, or `unresolved`); history (`head`, `superseded`, or `forked`); and disposition (`active`, `withdrawn`, or `pending_acceptance`). These are computed results, not trusted status fields supplied by the model. Show counts, omissions, snapshot identity, source projection identity where applicable, and routes to evidence/history. A bounded view cannot silently omit a conflict affecting the selected requirement.

Document declaration evidence that changes becomes unresolved/changed and cannot be presented as the current document's exact words. Retain the historical declaration until explicit revision; do not replace it with whatever a new file happens to say. If changed code may violate a developer requirement, keep the requirement and surface the discrepancy as an interpretation or reproduced check, with its own evidence. Inventory alone cannot prove the violation or compliance.

## Acceptance operations and failures

The following are conceptual operations, not executable command names or a public API:

| Operation | Inputs and outcome |
| --- | --- |
| Inspect | Fresh inventory, durable revisions, and optional verified host context produce bounded attributed/evidence-linked views. Unverified attribution and unknown behavior remain visible. |
| Propose | Candidate text, scope, origin, evidence, and predecessor IDs produce an immutable draft/record ID for review; proposing writes no application source and grants no approval. |
| Accept | Explicit authorized action plus expected inventory/projection and predecessor heads validate references and attribution, then publish one complete revision. A changed base/head rejects the candidate for reconciliation. |
| Refresh | Changed evidence produces stale markers and optional new interpretation proposals. The host decides whether to call a model; declared requirements remain intact. |
| Resolve/withdraw | Explicitly approved successor covers all relevant heads and preserves them as history. Unverified or partial resolution remains pending. |

Before any writer ships, its binding and application protocol must prove expected-head checks, stale-input rejection, concurrent acceptance, interrupted writes, and preservation of the prior accepted set. Cross-process compare-and-publish requires serialization or an equivalent atomic protocol; writing an immutable file alone does not settle competing acceptance. These are implementation gates, not supplied features.

Malformed records, digest mismatches, invalid origins, cross-project references, and cycles return `invalid_knowledge` without replacing accepted state. Unavailable referenced revisions/evidence are `unresolved_evidence` during inspection and block dependent acceptance. Unsupported host proof returns `unverified_attribution`; attempted declaration acceptance returns `attribution_required`. Changed inputs/heads return `stale_candidate`; unresolved competing heads return `knowledge_conflict`. A knowledge inspection failure cannot silently yield a complete knowledge view; independent file inventory may still succeed with its own narrower scope.

## Observable acceptance cases

| Case | Expected outcome |
| --- | --- |
| Billing purpose inferred from identified files | AI origin, source projection/evidence, explicit assumptions; never a developer declaration. |
| Developer corrects it to tenant isolation | New exact statement and verified host action required; preserve the inference and its supersession history. Without a binding, attribution remains unverified. |
| Model supplies a plausible developer ID and claimed approval | Reject declaration acceptance; IDs and hashes are not authentication. |
| Approved wording or scope edited after receipt | Old receipt cannot verify the new record ID. |
| Knowledge record saved, application inputs unchanged | Inventory snapshot changes, but source projection remains equal; no self-induced interpretation staleness. |
| New file within purpose scope, including after stopped operation | Projection changes; interpretation is stale. Rebuild/refresh before claiming evidence matches. |
| Source changes while requirement stays unchanged | Keep declared intent. Report changed support or a supported discrepancy; do not infer that the requirement was withdrawn. |
| Referenced revision superseded or unavailable | Dependent summary becomes stale/unresolved; never silently points to another revision. |
| Two developers refine the same record independently | Preserve both heads and show conflict; require explicit resolution, not recency. |
| Cache deleted or service unavailable | Durable records survive; inspect through local inventory and available proof, with unknowns visible. |
| Invalid/replayed proof or interrupted/stale write | No new accepted declaration; preserve the previous accepted set. Exact binding/application tests are required before implementation. |

This specification completes only the record/evidence/lifecycle design increment. The next gate is one concrete host binding plus the writer's concurrency/recovery protocol and executable acceptance tests. Performance, complete semantic understanding, and reduced agent tokens remain unproven. See the [worked lifecycle](../../examples/knowledge-lifecycle.md) and [local cost baseline](../../benchmarks/README.md).
