# Proposed architecture

The compiler/runtime behavior in this document remains proposed. A read-only local inventory subset is implemented under [decision 0007](design/0007-local-inventory-proof.md) and its [versioned contract](specs/local-inventory-v1.md), with optional verified local snapshots under [decision 0008](design/0008-verified-local-snapshots.md). Read-only knowledge inspection now follows [decision 0010](design/0010-read-only-knowledge-inspection.md); broader coherence, authenticated recording, source-editing, and sharing mechanisms remain unimplemented.

## The flow

The shared foundation aims to cover any kind of software through faithful adapters and semantic extensions. This direction is accepted in [decision 0004](design/0004-universal-coherence.md). Actual language, framework, and runtime support requires bounded demonstrations.

The following flow describes future IR-native programs whose executable graph owns generated artifacts:

~~~text
Human intent and examples
          |
          v
AI proposes structured edits <--- Problems found by checks
          |                               ^
          v                               |
Candidate program graph ------------> Checks
                                          |
                                    Accepted version
                                          |
                                          v
                                   Target compilers
                                          |
                                          v
                                   Runnable software
~~~

Readable views describe both the accepted program and proposed changes. An edit is accepted only after its required checks pass. A failed edit preserves the previous accepted version.

## Where the coding agent fits

An existing agent host owns the model conversation, authentication, tool permissions, and budget. Universal IR would provide the program representation, edit interface, checks, and compilers. The model might run remotely while those tools run locally.

A local CLI is the first entry point, so existing coding agents can call tools through terminal commands. The source-run inventory CLI now implements a bounded inspection operation; a public SDK will follow later for custom hosts. This priority is accepted in [decision 0002](design/0002-cli-first.md). See the [working inventory walkthrough](../examples/local-inventory.md) and broader [usage journeys](../examples/using-with-ai.md).

The core owns program representation, validation, editing, interpretation, and compilation behavior. The CLI is an adapter over that core, and the future SDK will use the same behavior. Exact commands, automation outputs, diagnostics, and exit behavior must be specified before CLI release.

The intended user installs the tool into their development environment, connects a supported project and coding agent, and prompts the agent to do work. An API harness can invoke the CLI as a tool before an SDK is available. The host owns repository creation, general command execution, and deployment authorization; Universal IR provides the supported representation and checkable operations. These consumer journeys are accepted in [decision 0003](design/0003-real-development-workflows.md).

## Adopting existing repositories

Existing-source adoption has a different ownership flow. [Decision 0005](design/0005-portable-project-state.md) keeps source files authoritative and derives a rebuildable, versioned graph. The [coherence specification](specs/project-coherence.md) defines the inventory-first contract; the broader [adoption proposal](existing-repositories.md) retains future source-editing work:

~~~text
Current source and project configuration
                  |
              Source adapters
                  |
       Source-backed graph and evidence <--- Declared intent and rules
                  |
       Overview and expandable task views
                  |
       Candidate source edits and checks
                  |
       Guarded application and reconciliation
~~~

Source-backed facts are not automatically executable IR. The first proof covers inventory across languages and declared relationships, not resolved runtime semantics. Supported lowering, deep adapters, and checked source application still need defined contracts and behavior checks.

For graph-managed generated artifacts, the accepted graph remains the source of truth. For existing source, the derived graph is the agent view of identified authoritative inputs. Never treat independently edited source and cached facts as simultaneous authorities. Preserve unrelated code and the project's build and test workflow.

## Portable knowledge and collaboration

Shared configuration and durable project knowledge live in a committed `.uir/` area in adopting projects. Local caches are ignored and each checkout has its own working view. Extracted graphs are reusable artifacts, not required source-commit diffs. Import requires matching inputs, compatible extraction, integrity, and accepted producer provenance; integrity alone cannot establish correctness.

The implemented [local cache subset](specs/local-cache-v1.md) uses explicitly selected external storage to preserve target-project read-only behavior and inventory identity. It stores only manifests after full current-source verification, with new checkout observations on every call. It neither authenticates producers nor imports findings without local reconstruction. Repository-local placement, incremental extraction, and shared transport remain later contracts.

Optional shared builders or artifact stores can reuse published-revision work. Observed branch revision, graph readiness, and local source freshness are separate. Notifications prompt reconciliation; delayed events or older extraction results cannot regress the latest verified view. A remote merge can be reported before its graph is ready without making a local checkout appear rebased.

The same concepts support Git hosts and non-Git folders. Without a configured upstream, local operation still works but has no remote-awareness claim. Shared services are optional; uncommitted work remains local by default. See the [sharing and collaboration contracts](specs/project-coherence.md#shared-snapshots-and-local-fallback).

The first consumer release needs a demonstrated, bounded existing-project workflow, including changes made while stopped and rejection of stale proposals. Universal scope is a foundation goal, not a claim that every adapter already exists.

## Coherence at several scales

Connect purpose, structure, supported behavior, and evidence. A complex system has nested components and relationships that cross them: events, data, permissions, interfaces, migrations, and checks. Use a graph behind tree views, system overviews, and task-focused expansions.

The [coherence proposal](coherence.md) defines those views and their evidence boundaries. An agent should move from the big picture to relevant source and back, with visible omissions and unknowns. A compact summary must not claim exhaustive runtime understanding or complete change-impact coverage.

Declared intent needs explicit ownership. Compiler facts, syntax, hypotheses, contracts, and observations need distinguishable provenance. Changes to either code or declarations may invalidate derived relationships and summaries.

[Decision 0006](design/0006-conversational-knowledge.md) lets the existing agent prefill purpose from evidence and refine knowledge through normal conversation. Host-attested developer statements remain distinct from model interpretations. A model cannot establish approval merely by claiming it occurred, and changed code cannot silently rewrite a declared requirement. Host provenance integration is still to be implemented.

The [knowledge record contract](specs/project-knowledge-v1.md), under [decision 0009](design/0009-knowledge-and-cost-gates.md), specifies immutable revisions, scoped source projections, explicit evidence, and separate attribution/history states. Source projections exclude knowledge metadata to prevent self-invalidation. The separate [knowledge reader](specs/knowledge-inspection-v1.md) now validates included records, traces matching/changed/unresolved support, and displays competing structural heads with unverified claims. Matching inventory captures bracket its record/quote reads. It does not compute effective approved intent; live authenticated user-event integration and checked acceptance concurrency/recovery remain gates before writing.

[Decision 0011](design/0011-explicit-host-receipts.md) now adds a separate [signed receipt verifier](specs/host-receipts-v1.md) under an explicit caller-pinned trust policy. Signature verification authenticates a host assertion under that policy; it does not prove a live user event, consume approval, resolve accepted intent, or write knowledge. A concrete host adapter and the [acceptance draft](specs/knowledge-acceptance-draft.md) remain gates. Default reader attribution stays unchanged; optional crypto is loaded only by receipt verification.

[Decision 0012](design/0012-pinned-harness-verification.md) adds an internal [host-configured verification tool](specs/harness-verification-v1.md). It fixes project, policy/pin, receipt lookup, and clock outside its model-visible request and rejects authority-changing fields at the handler. Hosts must separately protect their configuration/process from other model tools. This bounded adapter authenticates neither real human events nor host administrators and leaves the live-user/acceptance gates open.

[Decision 0013](design/0013-read-only-knowledge-preparation.md) adds read-only [external candidate preparation](specs/knowledge-preparation-v1.md). A virtual overlay uses the reader's validation/evidence/history logic to make exact proposals reviewable before storage. It reports current inputs and included structural heads, not accepted-intent state. Preparation itself neither approves a candidate nor verifies a receipt.

[Decision 0014](design/0014-prepared-receipt-verification.md) adds separate [prepared-candidate assertion verification](specs/prepared-receipts-v1.md). A distinct signature profile binds the exact record and reconstructed review context; a host-configured handler fixes review lookup and trust settings outside its single-identity model request. Changed source or proposal requires a fresh live review. Signature validity does not establish a real human event or accepted intent; historical resolution, authenticated review, and serialized acceptance remain later gates.

[Decision 0015](design/0015-acceptance-protocol-model.md) adds an [abstract acceptance model](specs/knowledge-acceptance-model.md) as development tooling. It separates staged artifacts, published decisions, and historical acknowledgements; tests retain competing imported heads and reject incomplete commits or conflicting event use. Authentication, locks, atomicity, and durability are assumptions supplied by tests. Real host integration, historical verification, and physical acceptance remain unimplemented; the default reader and signed profiles are unchanged.

[Decision 0016](design/0016-webauthn-review-assertions.md) adds optional [WebAuthn review assertion checks](specs/webauthn-review-v1.md). A trusted host fixes the credential, actor/event, origin, clock, and exact preparation before a fresh challenge is generated. Verification requires signed presence/verification flags and current review context; no enrollment, protected browser UI, receipt issuance, event consumption, or acceptance is implemented. A separate local review host is the first candidate integration, with isolation and a real developer ceremony still to demonstrate. Software-credential tests prove protocol checks, not human consent.

## Lifecycle and different kinds of state

Source snapshots, derived findings, candidate changes, check results, built artifacts, deployments, and runtime observations describe different things. Link them by identity and evidence; refreshing source does not establish that production changed.

The proposed lifecycle detects active changes, marks affected findings stale, and verifies relevant inputs before serving current views or accepting dependent edits. Watchers help responsiveness; content and configuration verification provide the freshness guard.

When stopped, no monitoring occurs. On restart, reconcile current included inputs with persisted state, detect additions and deletions as well as edits, and reuse only verified cached extraction. Rebuild affected relationships or the whole view when required. Do not overwrite source to restore the old graph or show pre-pause results as current.

Publishing a coherent refreshed snapshot requires detecting input changes during extraction. Report unstable or unsupported scopes clearly. Discovery and refresh latency must be measured; immediate access to a warm view is not a zero-cost cold-start guarantee. See the [complex-project walkthrough](../examples/complex-project.md).

## The program graph

A graph is a set of connected parts. Here, those parts describe a program and the connections show how they depend on one another.

The small executable core would represent typed values, functions, references, and effects. Shared identity, provenance, snapshot, and relationship contracts would also support source-backed views. Extensions would describe application data, permissions, interfaces, and other domain-specific behavior without flattening unsupported semantics.

- **Stable identities:** Graph-managed parts retain identity through known edits such as renaming. References use those identities rather than display names. Source locations are snapshot-specific; ambiguous external changes must not silently redirect an identity to different code.
- **Types:** Values and operations declare the kinds of data they accept and produce. Checks reject incompatible connections.
- **Effects:** Reading stored data, changing it, contacting a service, or accessing a device is explicit. Declaring an effect does not itself grant permission to perform it.
- **Permissions:** Rules describe who may perform protected actions. Target integrations must enforce those rules at trusted execution boundaries.

The accepted graph is the source of truth for generated artifacts. Existing libraries can be connected through adapters with documented interfaces and effects. The project does not need to rewrite every dependency into its own format.

## Editing and checking

An AI editor would receive the relevant parts of the graph and propose a bounded change against an identified version. The system would apply the edit to a candidate, check it, and accept it as a new version only if the required checks pass.

Checks would cover references, types, supported operations, and declared effects. Application extensions would add permission and behavior checks. Tests and simulation would check selected outcomes; proofs could establish specific properties where practical.

Checks cannot automatically establish that an unclear request matches the user's intention. Assumptions and unresolved choices must remain visible. Edit conflicts and missing information must be reported rather than silently guessed away.

For existing source, validate a bounded candidate against identified inputs and attach actual check outcomes to that exact candidate. Failed candidate checks leave the destination unchanged. Live multi-file application, concurrent editors, interrupted writes, and recovery require their own specified guarantees; do not assume arbitrary filesystem writes are atomic. Unsupported source semantics must restrict the claims made about a change.

Accepting a graph version, building artifacts, and deploying an application are separate steps. A valid graph does not by itself establish that a migration or deployment will succeed. Target tests must check observable behavior, runtime capability enforcement, and defined failure handling. Permission-sensitive updates must use a documented consistency model so a permission check and protected mutation cannot silently disagree.

## Extensions and targets

The core stays small. Extensions add concepts such as database transactions, reactive interfaces, or GPU operations, with documented meanings and rules for connecting them.

Each target declares which operations and capabilities it supports. Unsupported operations must be rejected explicitly. A shared format does not mean that every program can run on every device.

The first application targets would produce TypeScript and PostgreSQL artifacts for the [task example](../examples/project-tasks.md). A later WebAssembly target would cover the computational core. Existing compiler infrastructure may support future targets as requirements become clear.

Generated code is an output of the accepted graph. Changes to generated outputs must be represented in the graph or in a declared external dependency before they become durable program changes. Persistent data changes also require an explicit migration, with checks defined by the application target.

## Human inspection

Readable code, diagrams, change summaries, and execution traces would expose what the program does. Views should link back to the exact graph version and parts they describe.

A summary such as "project administrators can now archive tasks" must be backed by the relevant permission rule and checks. Explanations alone are not evidence that behavior is correct.

## What we will measure

The primary comparison is the cost of completing a correct change. Measurements include context and generation tokens, verification and repair work, latency, and review effort. A shorter encoding is useful only if the complete process benefits.

The [local inventory baseline](../benchmarks/README.md) measures the narrower current core in fresh workers, retaining raw attempts and missing measurements. Its small synthetic run supports no general speedup or agent-token claim. Full-task and sharing comparisons remain future experiments.

Python is selected for the local inventory prototype, with SHA-256 identities and provisional JSON/CLI contracts. The implementation reconstructs each inventory, matches consecutive captures, and makes optimistic filesystem observation limits explicit. Optional local snapshots are persisted and reused only after full verification; they do not yet reduce extraction work. It has no automatic host knowledge integration or model dependency. Compiler language, final IR encoding, incremental extraction, deeper adapters, authenticated knowledge acceptance, source application guarantees, and remote bindings remain open. Keep the reasons for accepted choices in [design decisions](design/README.md).

## Existing ideas to learn from

- [MLIR](https://mlir.llvm.org/docs/LangRef/) describes typed operations, extensible dialects, and multiple forms of the same program representation.
- [WebAssembly Component Model](https://component-model.bytecodealliance.org/composing-and-distributing/composing.html) provides interfaces and composition between components originating in different languages.

These are design references, not current project dependencies. Follow the [roadmap](../ROADMAP.md) for the order of implementation.
