# Portable project coherence and collaboration

**Status:** Accepted design specification, revision 0, under [decision 0005](../design/0005-portable-project-state.md) and [decision 0006](../design/0006-conversational-knowledge.md).

This specifies required behavior for the broader first coherence proof. The [local inventory version-1 contract](local-inventory-v1.md) implements a bounded subset: read-only capture, containment, configured document links, bounded views, and comparison, extended by [verified local snapshot storage](local-cache-v1.md). It explicitly limits freshness to optimistic consecutive captures on a trusted filesystem. Persistent knowledge, incremental extraction, sharing, and remote awareness remain unimplemented. Operation names and record categories here remain conceptual; the narrower contracts record the prototype's Python tooling, JSON, hashing, storage, and CLI I/O without selecting executable IR encoding or remote bindings.

## Purpose and first-proof boundary

Give an existing coding agent a coherent view of its actual project, durable project knowledge, and awareness of published revisions without requiring a server, GitHub, or model calls for deterministic inventory. Preserve the universal foundation across languages and software domains.

The first proof inventories files across languages, connects containment and explicitly declared relationships, and presents evidence-linked knowledge. Language and role classification are hypotheses unless backed by a declared mapping. It does not resolve arbitrary calls, types, effects, runtime behavior, or complete change impact.

Deep semantic adapters, checked application-source edits, executable IR, target compilation, deployment, and live sharing of uncommitted work are later increments. The long-term [architecture](../architecture.md) and consumer release gates still apply. A completed inventory prototype would not complete the interpreter or application milestones.

## Authority and repository storage

Existing source is authoritative for implemented behavior. Durable declarations describe stated intent; agreement with source requires evidence. The derived graph describes identified inputs and never repairs its freshness by overwriting them. IR-native graph ownership of generated artifacts is a separate future mode.

The following layout describes an adopting project, not directories to create in Universal IR today:

~~~text
project/
  application files and existing documentation
  .uir/
    config/       shared project identity, scope, extraction versions, document links
    knowledge/    durable declarations, attributed interpretations, relationships
    cache/        local snapshots, extraction results, local evidence and drafts
~~~

Commit the shared configuration and durable knowledge through the project's ordinary review workflow. Exclude `.uir/cache/` from version control and inventory. Linked project documents can remain in their current locations; a declaration must not be duplicated into competing authorities merely to fit this layout.

The implemented cache subset refines placement under [decision 0008](../design/0008-verified-local-snapshots.md): explicitly selected external storage preserves read-only discovery and version-1 input identity. The repository-local layout above remains a broader design, not an implemented initialization command. Shared configuration and future durable knowledge retain their committed `.uir/` location; cache deletion cannot erase them.

Knowledge can include an explicitly labeled AI interpretation as well as a developer declaration. Persistence or a Git merge does not silently promote an interpretation into a developer statement. Local task drafts and uncommitted work are not automatically uploaded. Only selected project knowledge travels; capturing a complete chat history is not required.

The graph is a reusable derived artifact, not a required generated diff in every source commit. Local storage, exported artifacts, CI artifacts, and a future shared service can supply snapshots through the same compatibility contract. A server outage or deleted cache cannot destroy durable intent or prevent local reconstruction.

Initialization may create the specified metadata and cache only within authorized setup. Discovery itself does not modify application files, project manifests, formatting, or existing agent guidance; it does not install dependencies or execute project scripts. Existing metadata must be inspected rather than replaced. Invalid configuration blocks the affected operation with a diagnostic instead of silently widening scope.

## Inventory and workspace boundaries

Inventory an explicitly selected root and configured inclusions. Respect the project's applicable ignore rules and explicit exclusions. Always exclude Git internals and the local cache. Record exclusion rules and unresolved boundaries; do not claim knowledge of excluded contents.

Record included regular files, directories, relative paths, content identities, configuration, shared declarations, and linked documents. Include relevant uncommitted and included untracked files. Preserve path spelling and source bytes; do not normalize or rewrite application files to produce matching results. Linked external roots, submodules, and symbolic-link targets require explicit inclusion; otherwise show them as boundaries rather than silently following them.

Inventory binary or unrecognized files as opaque entries with an identity and location. An unreadable included file must be reported; it cannot be silently omitted from a purportedly complete inventory. An extension-based language label or path-based role such as test, service, or generated code is a classification hypothesis. It cannot establish execution semantics or ownership by itself.

Established first-proof relationships are containment, configuration-selected document links, and explicit knowledge references whose targets resolve within the inspected inputs. A declaration that two services communicate is a declared relationship, not a compiler-confirmed call. Unresolved targets remain visibly unresolved; no fabricated target is substituted.

## Records and snapshot identity

The conceptual record categories are project, workspace, file, relationship, knowledge, evidence, and snapshot. The minimum information is defined below; these labels do not fix serialized field names.

| Record | Required information |
| --- | --- |
| Project configuration | Shared project identity, declared root/scope rules, extraction configuration and versions, linked documents. |
| Workspace | Local checkout identity, actual input snapshot, optional published base, developer attribution when supplied. |
| File | Project-relative location, content identity, included or boundary status, and classification with its origin. |
| Relationship | Endpoints, relationship kind, origin, supporting references, input dependencies, and resolved or unresolved status. |
| Knowledge | Stable record identity, statement and scope, origin, supporting evidence, lifecycle status, and explicit revision or supersession links. |
| Evidence | Origin, inspected inputs, locations or observation reference, method, scope, and relevant environment when applicable. |
| Snapshot | Design-format version, project/scope identity, input manifest, extraction compatibility information, and graph result identity. |

A source manifest identifies relevant input contents, configuration, exclusions, declared knowledge, and extraction versions. Directory membership is an input so additions and deletions can be detected. A Git revision is an optional locator for published source, not a substitute for the manifest. Different extraction rules or relevant configuration can require different graph snapshots for the same commit.

Published snapshots are immutable. Preparing updated findings does not mutate an agent's previously returned snapshot. References and locations identify their snapshot; a deleted or ambiguously renamed source target must not be rebound to unrelated code. Metadata declarations have stable record identities and explicit revision history. File locations are snapshot-qualified and do not promise semantic identity through arbitrary external renames.

For identical inputs and compatible deterministic extraction, established facts must be equivalent. Machine-specific paths, checkout identity, producer identity, observation time, and independently generated AI interpretations do not have to be byte-identical and must not be mistaken for established extraction differences. Keep AI interpretations and observations distinguishable from deterministic graph results.

## Views and evidence

An overview identifies purpose and its origin, included structure, relevant declared connections, available project guidance, snapshot identity, scope, freshness, and unresolved boundaries. Detail views expand selected files, components, declarations, or relationships while retaining routes back to the overview and evidence.

A view must identify its selection scope and visible omissions. When a size limit truncates results, provide an explicit continuation or expansion reference and an omission indication. No matches within a bounded selection cannot establish that no relationships exist elsewhere. Known unresolved endpoints remain navigable as unresolved records.

Views may expose supported source excerpts, but an excerpt and an inferred explanation have different evidence status. Checking graph structure or successfully extracting files is not evidence that tests pass, permissions hold, or a deployment is current. Historical observations keep their exact input and environment references and cannot become evidence for a different version.

## Lifecycle and freshness

Local freshness, extraction support, remote awareness, and artifact availability are separate dimensions. A current local inventory can contain unknown behavior and can be behind a newer remote branch. Unsupported deep analysis does not make independent file navigation impossible.

| Local state | Required meaning |
| --- | --- |
| Uninitialized | No usable configuration and local representation have been established. |
| Reconciling | Inputs are being inspected; any previous view is labeled historical. |
| Current within scope | The published view matches inputs verified at the stated observation boundary. |
| Stale | Known changes invalidate dependent findings; they cannot be served as current. |
| Blocked | An input or capability prevents the requested operation; report scope and recovery. |
| Stopped | Monitoring is inactive; persisted findings require reconciliation before current use. |

First discovery inventories the selected inputs, extracts established facts, resolves declared references where possible, and publishes a coherent snapshot. It can do this without any paid model call. The host may subsequently request AI interpretation of that evidence; interpretation is a separate, attributable operation.

Reuse cached extraction only after relevant input and compatibility checks. Watchers can trigger invalidation but cannot replace freshness verification. Changes to scope, documents, declarations, or extraction rules invalidate their dependents. Unknown dependency boundaries require conservative refresh or a visible limitation, not an unsupported claim of complete incremental analysis.

A request for a current view must verify its relevant inputs even when no watcher event arrived. A request to inspect a historical snapshot may retain that snapshot's original contents, but must label it historical rather than presenting it as the present workspace.

On restart, compare the current included inputs with persisted state, including additions, deletions, changed configuration, and uncommitted edits. Reuse verified results, refresh affected relationships, and reconstruct from inputs when the cache is absent or incompatible. Do not overwrite intervening user work to restore an old snapshot.

Before publication, verify that extraction used a coherent set of inputs. If inputs changed during extraction, retry or return an unstable-input diagnostic; no mixed-version result may be labeled current. Current means verified at the stated boundary, not guaranteed unchanged forever in the presence of independent writers.

## Conversational project knowledge

The existing agent host supplies model reasoning, authentication, permissions, budget, and any conversation integration. The core stores and validates attributed records; it does not acquire provider credentials or independently read every agent's chat.

After inventory, the agent may prefill a project-purpose interpretation supported by identified files and documents. This is useful provisional knowledge, not a claim that the developer's intention was conclusively recovered from code. Normal conversation can refine it without a separate onboarding questionnaire.

| Origin | Required treatment |
| --- | --- |
| Extracted fact | Identify the deterministic method and exact inputs; only claim what the method establishes. |
| Declared document | Reference the document version and relevant statement; distinguish stated intent from implementation agreement. |
| AI interpretation | Identify the host/model method when available, supporting inputs, scope, and unresolved assumptions. |
| Host-attested developer statement | Reference the project-relevant utterance or approved declaration and its host-supplied attribution. |
| Observation | Identify the checked or observed inputs, method, outcome, scope, and environment. |

Origin and lifecycle status are different. An interpretation remains inferred even when current. A developer declaration remains declared even when implementation conflicts with it. Record proposed, current, stale, superseded, or conflicting status as appropriate; supersession preserves the prior record rather than erasing its origin.

A model cannot promote its own inference by asserting that a developer approved it. Developer provenance requires host-attested evidence or an explicitly approved declaration. An AI paraphrase of an utterance must remain identifiable as an interpretation of that utterance unless its content is established as the declaration. Hosts without that provenance capability can still submit attributed interpretations.

Capture selected project-relevant goals, requirements, and decisions, not every transient task instruction. Sharing those records follows ordinary project review. Distinct or contradictory developer statements must be surfaced for resolution; recency alone does not silently replace a requirement. An explicit correction can supersede an interpretation through conversation while retaining its history.

When supporting inputs change, mark dependent interpretations and summaries stale and allow the host to refresh them. Refresh need not call a model for unaffected records. Changed code must not silently rewrite declared intent. Report a known discrepancy when there is evidence; inventory alone cannot discover every behavioral violation of a requirement.

The subsequent [knowledge record specification](project-knowledge-v1.md) defines prototype schemas, source projections, attribution/history dimensions, and failure outcomes. It remains documentation: a host proof binding and checked acceptance protocol must be demonstrated before a writer or verified developer provenance ships. See the [correction and collaboration walkthrough](../../examples/knowledge-lifecycle.md).

## Shared snapshots and local fallback

Snapshot exchange is optional and provider-independent. Uncommitted overlays remain local by default. Exporting a snapshot for a published revision must identify that exact revision's inputs; a dirty local snapshot cannot be mislabeled as the branch revision. Shared snapshot contents do not overwrite local source, configuration, or declarations on import.

Before reusing a supplied snapshot, establish design-format support, project and scope match, input identities, extraction compatibility, complete referenced artifacts, byte integrity, and accepted producer provenance. Integrity proves that received bytes match an identity, not that the producer's findings are correct. Trust is an explicit local or project-configured decision, not an assertion supplied by the artifact itself.

Results from an untrusted producer cannot become established current findings merely because their hashes match. Re-extract locally or retain them only as untrusted information. Imported observation or model records retain their original status, method, and scope; downloading them does not make them locally reproduced evidence.

| Supplied artifact state | Required outcome |
| --- | --- |
| Compatible, complete, intact, accepted producer | Reuse applicable results after input verification; derive local differences separately. |
| Missing or unavailable | Report unavailability and reconstruct locally when the required inputs are available. |
| Unknown format or incompatible extraction | Decline reuse with the compatibility reason; use supported local extraction. |
| Missing referenced content or integrity mismatch | Reject the artifact as a reusable result; do not publish it as current. |
| Untrusted producer | Do not treat findings as established; locally reconstruct or label them untrusted. |
| Required local inputs unavailable | Report the affected scope as blocked; do not claim a reconstructed current view. |

Local fallback does not magically provide unavailable remote source. A client may have a current local view and only a last-known remote view. Network transfer, input verification, and local overlay extraction remain costs even on a shared-cache hit.

## Published revisions and remote awareness

Identify a remote stream by project, provider or transport, and branch/ref. Track its last verified revision and observation status separately from graph availability: pending, available, unavailable, or rejected. The local view keeps its own source snapshot and published base.

An event is a hint to reconcile the stream, not authority to overwrite its observed head. Verify the current revision through the configured transport. Duplicate events must be harmless; delayed events and older builder completions must not move a latest-view pointer backward. A newer authoritative ref update, including a verified force push, can legitimately change history; commit ancestry alone cannot establish observation order.

If the branch advances from C1 to C2 while its graph is pending, report that C2 has been observed and keep the C1 artifact identified as historical. Publish an artifact under its exact input identity. Advertise it as the current branch graph only after verifying that the branch still names those inputs. If C3 is now the observed head, completing C2 extraction cannot relabel C2 as latest.

Reconcile on reconnection or an explicit upstream check and use a transport-appropriate periodic check to recover missed events while monitoring. Exact schedules, retry budgets, and provider bindings are implementation contracts; no instant-delivery guarantee is established. When offline or unavailable, report last-known remote state and observation time rather than claiming it is current.

Remote advancement can prompt comparison with local work, but does not modify the checkout, rebase a branch, establish a merge conflict, or validate the combined program. Compare known changed files and declared relationships and expose unknown semantic impact. Integrating source and checking the combined result remain separate authorized work.

Git refs and fetching can supply published revision discovery across Git hosts. Provider webhooks can accelerate it. Without Git, local inventory and content-based snapshots still work; remote streams require an explicitly configured revision source or remain unavailable. GitHub accounts and PR numbers are optional attribution and navigation, not core graph identities.

## Conceptual operations and failures

Every result identifies its input snapshot or explicitly reports why none is available, its scope, outcome, evidence origins, omissions, and actionable diagnostics. A failure preserves existing source and the prior snapshot as history; it does not relabel that snapshot as current. The table defines behavior, not command names or invocation syntax.

| Operation | Input | Output and failure behavior |
| --- | --- | --- |
| Initialize | Selected root, scope, setup authorization, existing project guidance | Shared setup proposal and initialized metadata when authorized; conflicts or invalid setup are reported without replacing existing project files. |
| Inventory | Current included inputs and extraction configuration | Coherent inventory snapshot, file classifications, resolved declarations and unknowns; unreadable or unstable inputs block affected completeness claims. |
| Refresh | Prior snapshot and current inputs | New immutable snapshot or verified reuse, change/invalidation report; stale or incompatible cache triggers reconstruction. |
| Inspect views | Snapshot, selection, expansion or size limits | Overview or detail with provenance, freshness, omissions and continuation; unresolved targets and unsupported analysis remain explicit. |
| Record knowledge | Attributed statement, scope, supporting references, expected knowledge revision | Proposed or authorized durable revision and links; stale revisions, absent provenance for claimed declarations, or conflicting statements cannot silently overwrite records. |
| Exchange snapshots | Exact snapshot, transport, compatibility and trust policy | Applicable imported results or authorized published artifact; unavailability, incompatibility, integrity or trust failure yields diagnostics and local fallback where possible. |
| Observe upstream | Configured revision stream and last observation | Verified published revision, independent artifact status, and comparison boundaries; disconnected results retain last-known status without altering local files. |

Diagnostics distinguish invalid configuration, unreadable inputs, stale findings or knowledge revisions, unstable inputs, unresolved references, unsupported analysis, incompatible artifacts, integrity failures, untrusted provenance, and remote unavailability. They identify the operation, affected scope, evidence, and recovery rather than marking an entire repository unusable without explanation.

## Walkthroughs

The identifiers C1, C2, S1, and S2 below are symbolic examples, not a serialized format or observed results.

### Solo project and inferred purpose

An agent inventories an application's source and linked README, producing S1. It finds billing-related files and proposes that the project manages subscription billing, linked to those inputs. The view labels that purpose inferred. The developer says the goal is billing infrastructure for several businesses and tenant isolation is essential. The host records the attributable requirement and supersedes the earlier interpretation where appropriate.

If a file changes, dependent findings refresh and relevant interpretations become stale. The tenant-isolation declaration remains. A later semantic adapter or check might establish a violation, but the first inventory cannot prove that every request enforces isolation.

### Five developers on separate checkouts

Five developers clone the same project configuration, durable knowledge, and C1 source. Compatible extraction yields equivalent established facts. Each checkout has a separate identity and local cache; one developer can also have multiple independent worktrees. Shared C1 extraction may be reused after verification.

Alice's local edits produce her own S1, while Bob's checkout remains at its own inputs. Neither is silently treated as the other's files. Published branch snapshots can be shared, with developer attribution, without automatically uploading unpublished changes.

### Sally merges while Alice works

Sally's merge advances the published branch from C1 to C2. Alice's agent learns that C2 is observed while its graph is still pending. Alice's S1 remains a view of her actual working files. A shared builder supplies a compatible C2 artifact, or Alice obtains the source and extracts it locally.

The agent compares C1, C2, and S1 within known coverage and reports potential interactions and unknowns. It does not label Alice rebased or her tests passing against C2. If C3 arrives before C2 extraction finishes, the C2 artifact remains valid historical evidence but cannot become the current-branch pointer. Source integration requires subsequent authorized work.

### Stop, edit elsewhere, and restart

The tool stops after S1. Another editor adds a file, deletes an old file, and changes scope configuration; a developer makes an uncommitted edit. On restart, reconciliation finds all included input changes, invalidates dependent facts and interpretations, and produces S2 when inputs are stable. It preserves the intervening edits. A request that expects affected S1 inputs is stale.

If the cache was deleted, S2 is reconstructed from source, configuration, and durable knowledge. If an included file is unreadable or inputs keep changing, report the scope and retain S1 only as history.

### No GitHub or no Git

A GitLab or self-hosted Git project can use refs and fetching; webhooks are optional transport adapters. A project with no Git can initialize shared metadata, inventory its folder, exchange explicit snapshot artifacts, and refresh locally. Without a configured remote revision source it has no upstream-awareness claim. No account, remote service, or paid model call is required for local deterministic inventory.

## Acceptance scenarios

These are requirements for the broader coherence implementation. Only the bounded inventory cases identified in the [local prototype contract](local-inventory-v1.md) are exercised today; that evidence does not complete the lifecycle, sharing, knowledge, or semantic requirements below.

| Scenario | Expected outcome |
| --- | --- |
| Identical compatible inputs on two machines | Equivalent established facts; attribution and independent AI interpretations stay separate. |
| One developer has dirty or included untracked files | A distinct working snapshot; published revision is not falsely assigned to those inputs. |
| Restart after additions, deletions, and configuration edits | Changes are reconciled before current use; unrelated bytes remain intact. |
| Missing or incompatible local cache | Reconstruction succeeds when inputs are available; no durable declarations are lost. |
| Inputs change during extraction | Retry or report instability; no mixed-version current view. |
| Observed upstream head advances before extraction finishes | New revision is visible with pending artifact status; local source is untouched. |
| Duplicate or reordered notification | Reconcile the ref; no stale event or builder result regresses its current view. |
| Missed notification, reconnect, or verified force push | Reconcile authoritative stream state, including non-ancestral updates; retain history separately. |
| Remote unavailable or no configured upstream | Local operations continue; remote state is last-known or unavailable. |
| Supplied snapshot missing, incompatible, corrupt, or untrusted | Decline unsafe reuse with the specific reason; extract locally where inputs allow. |
| Purpose inferred and then corrected by the developer | Attribution and history remain; correction changes the relevant knowledge without inventing approval. |
| Model claims its own inference was developer-approved | It is not promoted without host-attested evidence or an explicitly approved declaration. |
| Known implementation evidence conflicts with a requirement | Show the discrepancy; do not rewrite the requirement to match source. |
| Unknown language semantics or unresolved relationship | Inventory/navigation remains bounded; unsupported behavioral claims are not made. |
| Bounded view hides some relationships | Omissions and expansion are explicit; absence in the view is not asserted as absence in the project. |

## Future cost comparison protocol

Compare three implementations of the same inventory and knowledge contract: local-only caches, a graph committed alongside source, and an optional shared cache with local working views. The committed-graph arm is an experimental alternative, not the default architecture. Include the cost of producing, committing, transferring, reviewing, and resolving conflicts in those artifacts.

Use identical application and shared-knowledge inputs, extraction versions, view requests, knowledge tasks, model configuration when used, correctness checks, and attempt limits. Exclude generated graph/cache outputs from extraction in every arm so storing the graph cannot make it its own input. Publish fixture manifests, output exclusions, and exact environment/tool versions. Include mixed-language projects and five separate checkouts with overlapping published inputs and distinct working edits. List unknowns and excluded content rather than inflating coverage.

| Scenario | Setup and comparison boundary |
| --- | --- |
| Cold start | Empty local caches; record shared-cache empty and populated cases separately, including the work that populated it. |
| Warm start | Unchanged inputs and existing compatible caches; count freshness verification rather than assuming it is free. |
| Small edit | Change one included file; count extraction, invalidation, affected interpretation refresh, and view retrieval. |
| Broad invalidation | Change scope, linked guidance, or extraction configuration; count conservative rebuilding and resulting unknowns. |
| Five-developer reuse | Start from common C1, make separate working edits, publish C2, and request refreshed views; aggregate every client and shared builder. |

Record CPU time, peak memory, disk reads/writes, total transferred bytes, cache storage, retained Git-history growth, and builder/service work. Separate model input/output tokens, interpretation, supplied context, retries, and repair from deterministic extraction and freshness checks. Report cache hits, misses, rejected artifacts, and the conditions for each.

Report wall-clock latency for overview, detail, restart, remote awareness, and graph availability separately, with per-run results and distributions. Record review/setup effort, extraction correctness, attribution correctness, stale-view failures, omissions, and unsuccessful outcomes. Aggregate costs across all five developers and infrastructure rather than shifting work to a server and omitting it.

Deterministic inventory is designed to need no model calls. AI interpretation and agent use still consume tokens, and cached interpretations can require refresh. Sharing can reduce repeated extraction but adds verification, transfer, and infrastructure costs. Actual prices, when reported later, need dated configurations; no savings or performance thresholds are claimed by this specification.

## Completion and later implementation gates

This documentation increment is complete when the specification, decision records, architecture, roadmap, and usage guidance agree; examples and failure outcomes are unambiguous; documentation checks and rendering review pass; and the update is published through the checked PR workflow. It does not complete the full program-format milestone.

The local prototype now specifies initial configuration, JSON encoding, content identity/canonicalization, filesystem and ignore behavior, extraction compatibility, pagination, and CLI I/O. Durable knowledge schemas, host provenance integration, cache compatibility, and persistent workspace identity remain gates before those operations are implemented. Before remote release, define transport bindings, access controls, trust configuration, scheduling, and artifact retention. These are explicit later gates, not permission to infer semantics or hide incompatibility.

## Supporting references

[Bazel remote caching](https://bazel.build/remote/caching) shows reproducible outputs shared through action identities and content-addressed storage. It motivates compatible-input reuse; it does not establish Universal IR performance or require adopting Bazel.

[Git fetching](https://git-scm.com/docs/git-fetch) provides remote ref and object discovery. [GitHub webhook guidance](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks) includes recovery for missed deliveries, and [GitLab webhook events](https://docs.gitlab.com/user/project/integrations/webhook_events/) provide another provider example. These motivate revision reconciliation and optional notification adapters, not a dependency on a particular host.
