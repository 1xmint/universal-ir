# Read-only knowledge preparation, version 1

**Status:** Implemented bounded preparation under [decision 0013](../design/0013-read-only-knowledge-preparation.md). Uses the [knowledge record schema](project-knowledge-v1.md) and [inspection rules](knowledge-inspection-v1.md). This is a provisional core/CLI contract, not a stable public SDK or writer.

## Purpose and inputs

Review an exact proposal before storing it. The source-run CLI reads one complete `uir.knowledge.v1` record from a selected external file. Its project identity must match current project configuration; its record digest must cover exact body, scope, origin, evidence, supersession, and state. No hashing or origin field confers approval.

~~~sh
python -B -m universal_ir prepare-knowledge /path/to/project /outside/project/candidate.json
~~~

Add `--expected-snapshot sha256:<digest>` to require a previously observed inventory base; replace the placeholder with its actual lowercase digest. Quote paths containing spaces. Python 3.12+ and Git suffice, with no optional crypto or model calls. The operation creates no project configuration, directories, candidates, receipts, keys, or cache. Hosts prepare transport separately outside the active store.

The candidate must be an existing regular file outside the resolved project, without links/junctions in any path component, at most 1 MiB. Require strict UTF-8 JSON, LF, and a final newline; reject duplicate keys, non-finite values, unsupported fields/versions, and invalid identity or schema. A candidate filename need not match its content ID because it is transport, not a durable record location. The complete record is validated against its hypothetical canonical store path.

## Evaluation and consistent publication

For each of up to three attempts, capture current included inputs, read the external candidate, and inspect existing records with a virtual candidate overlay. Resolve evidence and combined dependency/history rules using the same reader code, including currently matching document byte quotations. Capture the project again and reread candidate bytes/digest/metadata. Publish only when both project captures and candidate observations match. An error on changing inputs retries; a stable malformed input fails without a partial successful report.

This is an optimistic observation on a trusted filesystem, not an atomic snapshot or protection against hostile path replacement/restored metadata. No watcher runs after publication. Source, configuration, ignore controls, and included knowledge changes affect the full inventory snapshot. The operation still scans the project; incremental extraction and performance improvements are not implemented.

An absent candidate is added only to the in-memory overlay. An identical included revision is evaluated in place and labeled `already_included`. Existing malformed included records still block the whole operation. Ignore boundaries are not widened: hidden/linked store portions appear as coverage gaps, and ignored evidence remains unresolved. Candidate scope may include future paths; report them separately from evidence whose target is unavailable.

## Result

Success is one JSON object on stdout, format `uir.knowledge-preparation.v1`, status `ok`, exit 0.

| Field | Meaning |
| --- | --- |
| `project_id`, `snapshot` | Current configured project and actual inventory content identity, excluding the external proposal. |
| `candidate` | Exact record, `already_included`, and reader-style `evaluation` of the overlay. Its path is null when unstored; an included candidate retains its real path. |
| `transition` | `meaning: included_structural_history_only`, operation `proposed_addition` or `already_included`, actual included heads before, preview heads after, heads not named in supersession, and whether the preview leaves competing heads. These are not accepted-intent heads. |
| `preconditions` | `format: uir.knowledge-preparation-input.v1`, project, exact record ID, full inventory snapshot, current scoped source projection ID, and included structural heads before the proposal. |
| `preparation_id` | Canonical SHA-256 of `preconditions`. Equivalent normalized candidates and identical inputs produce the same identity; times and external filename/formatting are excluded. |
| `coverage` | Record-store completeness/gaps and `semantics: unknown`; does not establish complete understanding or acceptance readiness. |
| `authority` | `approval: not_established`, `acceptance: not_established`, `writes: false`, and zero model calls. |
| `observation` | Resolved project root, start/verification times, raw candidate byte content ID, `matching_captures_and_candidate_reads`, and `atomic: false`. |

Evidence remains `matches`, `changed`, or `unresolved`. Matching means the identified support/projection matches within its scope, not that the proposal is true. Claimed developer events remain `unverified_attribution`; withdrawals, developer claims, and successors remain pending. A structural preview covering every included fork head is still neither an authorized resolution nor a replacement for a declaration.

For an already-included candidate, before/after structural heads are equal. `uncovered_heads` always means heads absent from the candidate's supersession list, including the candidate itself if it is an existing head; it is descriptive, not a requirement to supersede itself. A proposed new head without supersession can leave competing history. Missing predecessors are unresolved; cross-logical supersession and invalid combined dependency cycles fail. Dependencies on superseded/competing revisions retain the reader's changed-support meaning.

The full snapshot is a conservative review base: an unrelated included file can invalidate `--expected-snapshot` even if scoped source projection is unchanged. All declarations receive the current scoped source projection as a preparation precondition, while only AI interpretations carry a recorded `body.input_id`. No accepted-head ledger exists; a future writer must obtain accepted-state preconditions independently. Preparation IDs are identities, not capabilities to approve/write or guarantees of future freshness.

## Failures and next gate

Dispatched errors use this format on stderr, `status: error`, `error.code/message`, with no successful stdout. Exit 2 covers stable argument/input/evaluation/base failures; exit 3 is `unstable_inputs`. Parser failures before dispatch retain the existing inventory envelope.

| Code | Meaning |
| --- | --- |
| `invalid_candidate_input` | Missing, nonregular, inside-project, linked/junction, oversized, or unrepresentable external candidate path. |
| `invalid_knowledge` | Stable malformed candidate/store, bad identity/schema/quote, or invalid proposed history/dependencies. |
| `knowledge_unavailable` | No configured project identity; this operation does not initialize it. |
| `stale_snapshot` | Stable current project differs from the expected review base; refresh and review the new context. |
| `invalid_arguments` | Invalid expected digest or CLI arguments. |
| Inventory/read failures | Existing root, configuration, ignore/Git, and readability failures retain their meaning. |
| `unstable_inputs` | Repeated project/candidate changes prevent a coherent observation; retry on stable inputs. |

Stable missing input is an error; disappearance during an opened read retries. Error reports cannot activate the candidate or alter prior project knowledge. Success with changed/unresolved support or gaps is an inspectable review, not successful acceptance.

The [fictional walkthrough](../../examples/knowledge-preparation.md) demonstrates this subset. Separate [prepared receipt verification](prepared-receipts-v1.md) now checks an external host assertion bound to the reconstructed preparation. A live host must still review exact wording, scope, and transition through an authenticated human channel, establish its own trust, and recheck current accepted heads/source under the [acceptance protocol](knowledge-acceptance-draft.md). Unique event consumption, serialization, recovery, accepted-state derivation, and writing remain later gates. Default `knowledge` and `verify-receipt` behavior is unchanged.
