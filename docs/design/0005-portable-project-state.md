# 0005: Portable project state and optional collaboration

**Status:** Accepted

**Accepted:** September 30, 2026

## Context

The maintainer approved a documentation-only specification for a core that works locally with optional shared snapshots and remote-change awareness. The earlier [universal-coherence direction](0004-universal-coherence.md) left source authority, repository storage, and collaboration boundaries open.

A team shares published code and durable project knowledge, but individual checkouts and uncommitted changes differ. Rebuilding derived information need not involve a model call. Sharing compatible extraction can reduce repeated work, but verification, transfer, storage, and infrastructure still have costs that must be measured.

## Decision

- Existing source describes implemented behavior; committed project declarations describe stated intent. A source-backed graph is derived from identified inputs and never overwrites newer source to restore an old view.
- Use a committed `.uir/` area for configuration and durable knowledge, with ignored local caches. Link existing documents rather than requiring duplicated authorities.
- Publish immutable snapshots identified by relevant input contents, scope, configuration, and extraction versions. Git commits are optional published-source locators, not sufficient cache identities for dirty workspaces.
- Identify working views by checkout and snapshot, with optional developer attribution. Do not partition state solely by GitHub member.
- Treat extracted graphs as reusable artifacts instead of requiring them in each source commit. Compatible results may come from local storage, CI artifacts, or a future shared service; correctness retains local reconstruction.
- Track observed published revisions separately from graph readiness. Reconcile notifications and reconnects; delayed events and extraction results must not regress the latest verified view.
- Cover merged revisions and published branches. Keep uncommitted work local by default; opt-in live collaboration is a later extension.
- Begin with inventory across languages, connected views, and evidence-linked knowledge. Deep semantic adapters, checked source editing, executable IR, and compilers remain later increments of the universal foundation.

## Consequences

The [project-coherence specification](../specs/project-coherence.md) defines conceptual operation inputs, outputs, failures, lifecycle, sharing compatibility, and acceptance scenarios. It creates no executable commands, wire format, public API, runtime, or hosted service.

This resolves the existing-source authority and storage choices left open in [0003](0003-real-development-workflows.md) and [0004](0004-universal-coherence.md). The eventual executable graph remains authoritative for graph-managed generated artifacts. No automatic bidirectional source/IR ownership is adopted.

Local operation, Git hosts, and non-Git folders share the same content-based view concepts. Provider integrations are adapters. A remote outage limits awareness of remote state, not access to available local inputs. A content digest establishes integrity, not producer correctness; imported findings need explicit trust and compatibility.

Exact metadata schemas, encoding, identity algorithms, supported filesystem behavior, CLI syntax, transport bindings, access controls, and scheduling require later implementation contracts. This does not select the implementation language or final executable IR encoding.

## Alternatives considered

A graph committed alongside each source change travels through ordinary Git but adds generated diffs, history, and merge work. A mandatory shared service can centralize extraction and notification but adds availability and operational dependencies. The chosen architecture permits reusable shared artifacts while preserving a local path.

Live uncommitted sharing adds concurrent-draft coordination beyond published revision awareness. It is deferred rather than treated as necessary for the first proof. Inventory-first validates portable relationships and lifecycle without claiming language-specific execution semantics.

## Validation

The specification includes solo, five-developer, merge-during-work, restart, and non-GitHub walkthroughs. Future implementation must exercise current versus historical views, dirty inputs, missing caches, incompatible or untrusted artifacts, reordered notifications, and unsupported behavior.

The cost protocol compares local-only, Git-committed graph, and optional shared-cache approaches across cold/warm starts, small edits, broad invalidation, and five-developer reuse. It counts all client and infrastructure work. [Bazel remote caching](https://bazel.build/remote/caching) is a reproducible-cache precedent, not measured evidence for Universal IR.
