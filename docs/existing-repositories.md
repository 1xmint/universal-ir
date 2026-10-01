# Existing-repository adoption and freshness

**Status:** Broader adoption proposal. Existing-source authority, portable storage, inventory-first scope, conversational knowledge, and lifecycle requirements are accepted in decisions [0005](design/0005-portable-project-state.md) and [0006](design/0006-conversational-knowledge.md), with the [project-coherence specification](specs/project-coherence.md). The [local inventory prototype](specs/local-inventory-v1.md) implements read-only capture, bounded structural views, document links, and comparison after external edits. Persistent caches, conversational knowledge, deeper semantics, and checked source application remain future work.

## Scope and ownership

Let an existing agent work in a user's project without converting it wholesale or replacing its framework and checks. Preserve current files and unrelated human work while exposing coherent, versioned relationships.

The accepted existing-source policy keeps source files authoritative for implemented behavior. The graph is a rebuildable, source-backed view. Declared requirements describe stated intent, but agreement with implementation needs evidence. A current graph may be the main agent entry point without replacing either authority.

For future IR-native projects, the accepted executable graph would be authoritative for generated artifacts. Mode and ownership boundaries must be explicit. A mixed project would need declared file or module ownership; automatic bidirectional editing of source and executable IR is outside the initial proposal.

The first coherence proof inventories projects across languages and connects containment, explicit declarations, and attributable project knowledge. It does not perform deep semantic analysis or checked source edits. A later source-editing proof needs a deeply supported language and small set of operations; TypeScript remains a candidate, not an accepted adapter choice. Inventory must not be presented as complete language semantics.

Shared configuration and durable knowledge travel in a committed `.uir/` area, with ignored local caches. Working views belong to checkouts and snapshots rather than GitHub members. Optional shared published snapshots require input compatibility, integrity, and accepted provenance; local reconstruction remains available. The specification separates observed upstream revision from graph readiness and local freshness.

## Discover without rewriting

Discovery would inventory the selected workspace, project guidance, configuration, dependencies, known build and test entry points, generated files, and supported source. Report excluded paths and unresolved inputs. Respect explicit workspace boundaries; submodules and linked external projects need declared inclusion.

Discovery must not run arbitrary project scripts, reformat files, install dependencies, replace agent instructions, or modify the project's manifests. Any tool-owned configuration and cache locations must be specified and distinguishable from application files. Authorized execution remains a host responsibility.

Use deterministic language tooling for established syntax, symbols, types, and references where available. Record the adapter and compiler compatibility versions. Unresolved dependencies, configuration errors, and unknown framework conventions must appear in diagnostics. An optional model interpretation remains a labeled hypothesis.

Existing build or test failures belong in the baseline. A project with baseline failures must not be labeled healthy, and an edit must not claim a fully green result by ignoring them. Acceptance must specify the target behavior and how relevant new failures are detected.

## Snapshot and evidence contract

A snapshot should identify relevant input contents and workspace scope, not just the Git commit. Include relevant uncommitted and included untracked files, configuration, manifests, dependency resolution inputs, declarations, and extractor versions. The exact manifest and hashing scheme remain to be specified.

Each fact or relationship needs evidence provenance, relevant source locations, and the snapshot it describes. Source positions are version-specific. Preserve identity across a known transformation where justified; ambiguous external renames or rewrites must not silently redirect old references to a different declaration.

Before publishing a current snapshot, verify that its inputs did not change during extraction. Retry or report an unstable workspace when a coherent snapshot cannot be obtained. Publish a coherent version rather than a mixture of facts from different file versions.

Cached extraction may be reused only when its relevant inputs match. A timestamp or watcher notification alone is insufficient evidence of unchanged contents. Cache deletion or incompatibility must allow rebuilding from the authoritative inputs.

## Active and stopped operation

| State | Meaning for the agent |
| --- | --- |
| Uninitialized | No usable project representation exists. |
| Reconciling | Inputs are being inspected; a prior snapshot may be available only as historical information. |
| Current within scope | The published snapshot matches its verified inputs within the declared scope. |
| Stale | Known input changes invalidate some current findings; dependent edits cannot proceed. |
| Blocked | Unsupported or unresolved inputs prevent a requested operation; explain the affected scope and recovery. |
| Stopped | No monitoring is occurring; persisted findings are historical until reconciled on restart. |

Support coverage is separate from freshness. A current view can explicitly contain unresolved relationships. A blocked operation need not make every independent operation unusable.

While active, watchers can trigger invalidation and refresh. They are accelerators, not the sole correctness guard. Requests and edit acceptance must verify relevant input freshness, even if no event arrived. Exported signatures, module resolution, configuration, or dependency changes may invalidate dependent facts, not only the edited file.

Current means verified at the declared observation boundary, not guaranteed unchanged forever. An independent writer can change a file after verification. Snapshot references and application preconditions must carry that limitation; monitoring responsiveness is a measured property.

The living representation should expose stable published snapshots while preparing refreshed findings separately. Do not mutate an agent's existing snapshot into a different version underneath it. Targeted invalidation and checks should avoid rerunning every expensive analysis on every keystroke, but uncertain dependency boundaries require conservative refresh or an explicit unknown. The dependency and consistency algorithms remain open.

When stopped, the tool cannot know about new edits. On restart it should enumerate the current included inputs, detect additions, deletions, and content or configuration changes, and compare them with the persisted snapshot. It may reuse verified extraction, refresh affected dependencies, or rebuild when invalidation cannot be bounded.

The restart response must identify whether reconciliation completed, what changed, what was invalidated, and which boundaries remain unresolved. If inputs keep changing, report that a current view is unavailable. Never silently serve a pre-pause view as current or reset user files to make them match the cache.

Performance depends on repository size, dependency scope, and changes made while stopped. Measure cold indexing, warm startup verification, offline-change reconciliation, and active refresh separately. No constant-time or zero-latency restart guarantee is proposed.

## Prepare, check, apply, and refresh

The recommended core owns edit preconditions and validation rules. The CLI exposes them; the agent host owns model prompts, permissions, and authorized command execution. A context-only operation remains useful, but is not the complete checked-change workflow.

1. Reconcile inputs and return a task view with its snapshot, evidence, omissions, and unknowns.
2. Receive a bounded edit proposal identifying its base, relevant source identities or regions, expected input, and permitted scope.
3. Reject stale bases, ambiguous mappings, unsupported transformations, and out-of-scope changes before modifying the destination.
4. Prepare candidate files in an isolated workspace. Preserve original encoding, line endings, formatting, and bytes outside the allowed edits; do not reprint whole source files by default.
5. Have the authorized host run the specified checks against the exact candidate. Record observed outcomes and environment; a model's statement that tests passed is not evidence.
6. If checks alter relevant candidate inputs, invalidate previous results and check the resulting candidate again. Failed candidate validation leaves the destination unchanged.
7. Reverify destination preconditions and execute the documented application protocol. Reconcile the resulting source and return the new snapshot with evidence.

Include unrelated dirty files in preservation checks. Do not erase a user's edits to reproduce a Git baseline. Changes to generated, vendored, or minified files, and creates, deletes, or renames, require explicit supported operations and scope.

Source acceptance and application need distinct guarantees. An isolated candidate can be rejected without touching the destination. Applying multiple files to an arbitrary live filesystem is not automatically atomic. A cooperating lock does not prevent independent editors from writing. The implementation must specify conflict detection, interrupted writes, recovery, and whether live application is supported. Never restore a preimage over newly detected human edits.

Permission-sensitive behavior requires checks at the actual trusted execution boundary. Source type checks alone cannot establish permissions, behavioral correctness, absence of effects, or deployment safety.

## Unsupported parts and useful diagnostics

Report support by operation, construct, and adapter version, rather than declaring an entire language understood. An unresolved runtime call may allow source navigation while blocking an effect-preserving transformation. Foreign-language or unavailable dependency code can remain an opaque boundary with known interfaces and explicitly unknown behavior.

Diagnostics should identify the requested operation, affected source or relationship, reason, evidence, scope of the limitation, and useful recovery. Distinguish stale inputs, invalid source, unsupported syntax or semantics, missing dependencies, ambiguous identity, failed checks, and application conflicts.

Refreshing a graph cannot resolve every unknown. External services, dynamic loading, reflection, and runtime configuration may require declared contracts or bounded observations. Preserve the unknown when sufficient evidence is unavailable. Ordinary host edits outside this workflow must not be labeled Universal IR-validated changes.

## Required demonstration

Use a real existing project and retain its original build and test workflow. Publish the fixture or reproducible setup, supported operations, original snapshot, proposed change, resulting diff, diagnostics, and actual check results.

| Scenario | Observable completion condition |
| --- | --- |
| First adoption | Useful overview and source-linked task view appear; discovery rewrites no application files. |
| Cross-project archive permission fix | Target behavior and denied direct requests pass checks; unrelated bytes and user edits remain intact. |
| External edit after proposal | Dependent proposal is rejected as stale; destination is not overwritten. |
| Stop, edit manually or with another agent, restart | Added, changed, and deleted inputs are reconciled before a view is presented as current. |
| Configuration or exported-type change | Affected dependent relationships are refreshed or invalidated. |
| Change during extraction | No mixed-version view is published as current. |
| Unknown runtime dependency | Navigation remains bounded; unsupported behavioral claims or edits return a scoped diagnostic. |
| Existing failing checks | Baseline failures remain visible; target evidence and new failures are reported separately. |
| Candidate failure or interrupted application | Documented preservation and recovery guarantees are exercised without overwriting concurrent user edits. |
| Missing or incompatible cache | Representation is reconstructed from authoritative inputs. |

These are future acceptance cases, not passing tests. The [complex-project walkthrough](../examples/complex-project.md) adds cross-service navigation and different runtime states. Measure all discovery, refresh, context, model, check, and repair costs against ordinary agent editing before claiming an improvement.

## Open specifications and references

The [coherence specification](specs/project-coherence.md) settles ownership, storage, first-proof scope, conceptual records and operations, lifecycle outcomes, provenance, optional sharing, and published collaboration. The [inventory contract](specs/local-inventory-v1.md) now defines initial configuration, content identity, filesystem behavior, compatibility, view expansion, and CLI I/O. Knowledge/host integration and persistent caching remain gates. Before source editing, define the deep adapter, support matrix, semantic identities, invalidation, and application/recovery protocol. Remote release also needs transport, access, trust, scheduling, and retention contracts. Performance remains to be measured.

Useful existing work includes [TypeScript compiler services](https://github.com/microsoft/TypeScript/wiki/Using-the-Compiler-API), [versioned LSP edits and declared failure handling](https://raw.githubusercontent.com/microsoft/language-server-protocol/gh-pages/_specifications/lsp/3.17/types/workspaceEdit.md), and [static analysis limitations](https://codeql.github.com/docs/writing-codeql-queries/about-data-flow-analysis/). These are references, not dependencies or claims of current compatibility.
