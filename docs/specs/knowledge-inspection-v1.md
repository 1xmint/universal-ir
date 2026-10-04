# Read-only knowledge inspection, version 1

**Status:** Implemented bounded prototype under [decision 0010](../design/0010-read-only-knowledge-inspection.md). This reads the [knowledge record contract](project-knowledge-v1.md); it does not implement acceptance, authenticated attribution, a writer, or executable IR.

## Operation and inputs

Run from the Universal IR checkout with Python 3.12+ and Git:

~~~sh
python -B -m universal_ir knowledge /path/to/project
python -B -m universal_ir knowledge /path/to/project --id tenant-isolation --limit 20 --offset 0
python -B -m universal_ir knowledge /path/to/project --full
~~~

Use `.venv\Scripts\python` on Windows if using the repository's development environment. The selected project needs version-1 `.uir/config/project.json` with a nonempty `project_id`. No Git repository or provider account is needed. This operation writes no selected-project files, executes no project scripts, fetches nothing, and calls no model. `-B` also disables Python bytecode writes in the tool checkout. There is no knowledge cache option or ongoing monitoring.

Inspect included immutable revisions at `.uir/knowledge/records/<logical-id>/<digest>.json`. Validate exact schema, project/content identities, literal paths, origins, quoted UTF-8 byte lengths, references, LF/final-newline formatting, and filename agreement. Unknown fields, including model-supplied approval/status fields, are invalid. Files in this store must use the record layout; directories are limited to the store and logical-ID level. Store parents must be directories or reported filesystem boundaries. Other `.uir/knowledge/` content, such as future receipts, is inventoried but not interpreted.

Each included record is limited to 1,048,576 bytes. Larger records return `invalid_knowledge`. This bounds individual JSON/quote reads, not total workspace size or scan time. Empty logical-ID directories are allowed. A missing store in an otherwise configured, unobstructed workspace produces an empty inspected set. An ignored, excluded, linked, nested-repository, or special-file boundary at an ancestor or inside the store produces explicit incomplete coverage; it never produces a complete empty-set claim. Ignore rules are not widened to recover hidden records.

## Publication and freshness

Use the inventory's isolated Git ignore evaluator and capture rules. For each of up to three attempts:

1. Capture the inventory manifest and filesystem metadata tokens.
2. Read included records and any currently matching document quote windows. Check parent links/junctions, regular-file identity, bytes/content digest, and opened-file metadata. Compute the complete included history and evidence view.
3. Capture again. Publish only if both manifests and metadata tokens match. If an inspection validation error occurred on changed inputs, retry rather than diagnosing a transient torn record as stable invalid data.

Detected changing inputs exhaust attempts with `unstable_inputs`. A stable invalid record fails the whole knowledge operation; it cannot return a successful partial record set. An independent `inventory` request can still succeed with its narrower meaning. Each successful view identifies the actual inventory snapshot and the observation interval. Matching captures are optimistic evidence of observed inputs, not an atomic filesystem snapshot or protection against arbitrary writers restoring identical bytes/metadata. Findings may become stale immediately after verification.

The inventory extractor and its snapshot contract are unchanged. Knowledge files change the inventory snapshot; AI source projections follow the exact metadata-excluding rules in the record specification, so saving an ordinary record does not invalidate its own interpretation. Configuration and all ignore controls still participate.

## Output

Success is one JSON object on stdout, format `uir.knowledge-view.v1`, status `ok`, and exit 0. The output is provisional, not a stable SDK/API. Arrays have deterministic identity/path ordering where applicable; timestamps and checkout paths are observations rather than reusable identity.

| Field | Meaning |
| --- | --- |
| `project_id`, `snapshot` | Configured project and current inventory content identity. |
| `observation` | Resolved checkout root, UTC start/verification timestamps, `matching_captures_around_knowledge_reads`, and `atomic: false`. |
| `coverage` | Whether the record store has observed gaps; bounded gap entries and total/omitted counts; attribution verifier `unavailable`, acceptance `not_established`, history `included_revisions_only`, semantics `unknown`, zero model calls, and record byte limit. Complete means no detected store boundary/omission, not complete knowledge of the project's meaning. |
| `summary` | Counts across all included revisions, logical IDs, competing groups, evidence states, and unverified developer statements, even when a logical ID is selected. |
| `selection` | Requested logical ID, offset, limit, and full mode. |
| `records` | Selected total, omitted count, and record details, including exact body and record path. |
| `groups` | Selected logical groups, omitted count, competing-head flags, and bounded head IDs with total/omitted counts. |

`--id` selects one logical identity and its included history, not one alleged accepted winner. Default limit is 20, range 1..200; offset is nonnegative and paginates records. Group summaries start at their first group, independent of record offset, so an explicitly selected conflict remains visible even on an empty revision page. Full mode returns every included revision, group, head, and gap; limit/offset still must be valid but do not truncate it. Normal mode may contain large statement bodies: count bounds are not token bounds. Omissions are explicit, including when conflict heads do not fit; `--full` or further record pages expose them.

Per-record results preserve the exact claimed origin and show:

| Result | Meaning |
| --- | --- |
| `attribution` | Developer statements always `unverified_attribution`; other origins `not_applicable`. A host name or committed record is not authentication. |
| `evidence_status` | `unresolved` if a referenced input/revision/predecessor is unavailable, document declaration is no longer linked, or a dependency has unresolved support; otherwise `changed` if support/projection changed or a referenced revision is superseded/competing; otherwise `matches`. Unresolved takes precedence over changed. Empty evidence for a developer claim can match an empty evidence set while attribution remains unverified. |
| `history` | `head`, `superseded`, or `forked` in the included structural supersession graph. These are not accepted-intent states. |
| `disposition` | Developer claims and all successor/withdrawal claims are `pending_acceptance`. Other initial active records are `active`; that means an active recorded statement, not approved or proved intent. |
| `source_projection` | Current scoped projection ID for AI interpretations, otherwise null; the body retains its recorded ID. |
| `references` | Exact reference payloads with match/change/unresolved reasons and referenced-record attribution where available. Never silently rebind a pinned revision. |
| `issues` | Explicit reasons for missing predecessors, changed source projection, or a declaration document removed from configuration. |
| `missing_predecessors`, `successors` | Routes through included structural history and explicit missing IDs. |
| `unresolved_scope` | Declared paths absent from the included inventory or represented as boundaries. |

Document quotations are validated against currently matching file bytes using zero-based, end-exclusive UTF-8 byte offsets. A wrong quotation against the identified bytes is invalid knowledge. Changed/missing files preserve historical text and report changed/unresolved support; the reader cannot verify a historical quote without its historical bytes. A declaration's exact quoted path must remain in configuration's document list to have resolved current declaration support. No inferred statement is promoted to developer intent.

The combined supersession/record-evidence graph must be acyclic. Supersession across included logical identities is invalid. Missing record IDs remain unresolved because this reader cannot identify their absent project/identity. Competing included heads remain visible, including roots with no common predecessor. A later record superseding all heads can change the structural graph, but stays pending and establishes no authorized resolution. No effective accepted-intent set or textual contradiction detection is computed. Prior statements remain inspectable even when an unverified successor claims withdrawal.

## Failures

Runtime errors emit one JSON error object on stderr in `uir.knowledge-view.v1`, with no successful stdout. Argument-parser failures before command dispatch retain the existing `uir.inventory.v1` error envelope. Errors have `code` and `message`. Exit 2 covers argument, configuration, readability, knowledge schema, and selection errors; exit 3 is `unstable_inputs`.

| Code/outcome | Meaning and next action |
| --- | --- |
| `knowledge_unavailable` | No configured project identity; a future setup flow is needed. The inspector does not initialize configuration. |
| `invalid_knowledge` | Stable malformed/oversized records, identity/path mismatch, invalid quoted bytes, cross-logical supersession, or cycles. Correct the record outside this operation; no partial knowledge result is published. |
| `unknown_knowledge` | Selected logical ID has no included revisions. Check broader coverage and selection, not an assumed absence from hidden content. |
| `invalid_arguments` | Invalid selection, limits/offsets, unsupported flags, or missing arguments. |
| Inventory errors | Existing `invalid_root`, `invalid_configuration`, `unsupported_path`, `unreadable_input`, or Git-tool errors retain their meanings. |
| `unstable_inputs` | Repeated changes prevent a coherent observation. Retry when stable or inspect a frozen tree. |
| Success with gaps/unresolved evidence | Inspectable partial coverage, not silent success of full knowledge/acceptance. Agents must check coverage, evidence, and attribution independently. |

No accept, record, resolve, receipt, or model flags exist. The authenticated host binding and serialized stale/concurrent/interrupted acceptance gate in the record specification remains required before introducing a writer.

The separate [verify-receipt operation](host-receipts-v1.md) can inspect a signed assertion under a caller-pinned policy. It leaves this operation's default attribution unchanged and supplies no accepted-intent resolver, live user-event binding, or writer.

The separate [preparation operation](knowledge-preparation-v1.md) evaluates an external candidate through an optional in-memory overlay using the same reader logic. Ordinary inspection never receives that overlay and remains unchanged. A proposed structural successor is not stored or accepted.

## Acceptance evidence

`tests/test_knowledge.py` exercises record integrity/schema, fictional fixture counts/forks, byte-offset quotes, source/configuration/ignore changes, missing/dependent references, long/cyclic history, pending withdrawals, coverage gaps, link/junction boundaries, races and torn-record retry, equivalent checkouts, real CLI behavior, and target preservation. Required Windows/Linux CI runs these tests alongside inventory/cache/cost and documentation checks. This demonstrates the bounded reader, not lower agent tokens, complete semantic understanding, or authenticated collaboration. See the [working walkthrough](../../examples/knowledge-inspection.md).
