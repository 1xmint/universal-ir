# Roadmap

## Vision

Give AI one shared way to build and change software. Check that the software follows its rules, then turn it into programs that run on different systems. People should always be able to inspect what it does.

The long-term scope is a universal foundation for any kind of software, across languages, frameworks, and runtimes. We will start small, prove that changes work, and expand when evidence supports it. A narrow first adapter tests the foundation; it does not define its eventual limits.

## Guiding principles

- **Preserve meaning.** Translating a program must preserve its defined behavior.
- **Make changes checkable.** Reject invalid changes before they replace an accepted program.
- **Keep human inspection available.** Show behavior, rules, and changes in forms people can understand.
- **Reuse existing infrastructure.** Build on existing libraries, compilers, and runtimes where they fit.
- **Measure the whole task.** Count context, generation, checking, and repair when comparing token use. Correctness comes first.
- **Connect the big picture to detail.** Keep nested structure and relationships across it navigable without requiring everything in one model context.
- **Show freshness and evidence.** Tie findings to their inputs; detect external changes and reconcile after stopped operation.
- **Keep unknowns visible.** Distinguish established facts, declared intent, hypotheses, and bounded observations.

## Milestones

Checkboxes show completed work. Each implementation increment depends on its relevant contracts; these are completion gates, not promised dates. The first coherence proof can follow its specific implementation gate below without claiming that executable IR semantics or later consumer gates are complete.

### 0. Explain the idea

- [x] State the vision and current state in the README.
- [x] Describe the proposed architecture and its boundaries.
- [x] Walk through a task application and an administrator archive change.
- [x] Document contribution guidance and ordered milestones.
- [x] Add real development journeys for subscription and API users, agent handoffs, and decision records.
- [x] Add reproducible documentation checks and tests with pull-request CI.
- [x] Document the universal-foundation direction, complex-project views, and a proposed pause/resume adoption workflow.

**Purpose:** Give contributors a shared starting point.

**Done when:** The documentation lets a new reader explain the purpose, current state, and first implementation step. Those answers are available in the [README](README.md).

### 1. Define a small program format

- [ ] Define a versioned format for typed values, functions, references, and explicit effects.
- [ ] Document valid and invalid examples with clear expected interpretations.
- [ ] Specify operation and error meanings, capability boundaries, and deterministic fixture outcomes.
- [ ] Choose the implementation language and initial encoding; record the reasons and tradeoffs.
- [ ] Define reference identities, edit acceptance, version evolution, and compatibility rules.
- [ ] Specify shared relationships, provenance, source mappings, snapshot identity, and evidence categories without treating a partial source index as executable semantics.
- [ ] Specify overview and task-view selection, expansion, omissions, and freshness behavior.
- [x] Adopt reusable core, CLI first, SDK later ([decision 0002](docs/design/0002-cli-first.md)).
- [x] Adopt a universal foundation with connected views and explicit freshness goals ([decision 0004](docs/design/0004-universal-coherence.md)).
- [ ] Define setup and integration for a supported coding agent and an external API harness.
- [ ] Define supported existing-repository adoption, including source/graph authority, file mappings, freshness, and unsupported code.
- [ ] Choose the first deep semantic source adapter and its supported operations; specify its dependency invalidation beyond the initial inventory contract.
- [ ] Specify candidate checks, destination preconditions, interrupted application, and recovery guarantees for source changes.

**Purpose:** Establish precise meanings before writing the core.

**Done when:** Each example has an unambiguous interpretation, including what makes it valid or invalid. The minimum supported operations, version rules, and bounded adoption contract are documented with expected valid, stale, unsupported, and interrupted-operation outcomes. The [adoption proposal](docs/existing-repositories.md) lists the open specifications.

#### Portable project coherence specification

This is a documentation increment within milestone 1. The first working proof will inventory projects across languages before deep semantic adapters or checked source editing. It does not complete the full program-format milestone or any executable behavior gate.

- [x] Record source authority, shared `.uir/` knowledge, local caches, immutable snapshots, and optional published collaboration ([decision 0005](docs/design/0005-portable-project-state.md)).
- [x] Record AI-prefilled purpose and attributable conversational knowledge ([decision 0006](docs/design/0006-conversational-knowledge.md)).
- [x] Specify inventory, views, lifecycle, conceptual operations, compatibility/trust, and failure outcomes.
- [x] Document solo, five-developer, merge-during-work, restart, and non-GitHub walkthroughs with acceptance cases.
- [x] Define the future local-only, Git-committed graph, and optional shared-cache cost comparison without claiming savings.

**Purpose:** Establish portable project knowledge and state boundaries before implementation.

**Done when:** The [specification](docs/specs/project-coherence.md), decisions, and related guides agree, their examples and failures are unambiguous, documentation checks and rendering review pass, and the update is published through the checked PR workflow.

**Following increments:** The bounded local inventory contract below specifies and implements initial configuration, content identity, filesystem/ignore behavior, view expansion, and CLI I/O, with optional external snapshots. Knowledge record/evidence schemas are specified; authenticated host bindings and checked acceptance remain gates before knowledge recording. Transport bindings, access controls, schedules, and retention are required before a remote release. Executable IR and compiler choices remain open.

#### Read-only local inventory prototype

- [x] Record Python prototype tooling and isolated Git ignore evaluation in [decision 0007](docs/design/0007-local-inventory-proof.md).
- [x] Specify version-1 configuration, content identity, filesystem boundaries, views, comparison, and CLI errors.
- [x] Implement a reusable inventory core with a source-run CLI adapter and no model calls or target-project writes.
- [x] Demonstrate mixed-language inventory, source-linked containment, document links, bounded expansion, and comparison after stopped-operation edits.
- [x] Test invalid inputs, omissions, boundaries, missing tools, baseline integrity, and detected concurrent edits on Windows and Linux through required CI.
- [x] Add persistent compatible local snapshots, full freshness verification, corruption recovery, and interrupted publication under [decision 0008](docs/design/0008-verified-local-snapshots.md).
- [x] Measure bounded uncached, cold-cache, and warm-cache costs before optimizing extraction; publish a reproducible script and [raw local baseline](benchmarks/README.md), including unmeasured costs.
- [ ] Add incremental extraction and dependency invalidation with correctness equivalent to full reconstruction.
- [ ] Implement durable conversational knowledge and host-attested provenance.
- [x] Specify immutable knowledge revisions, source/document evidence, attribution boundaries, supersession/conflicts, and observable failure outcomes under [decision 0009](docs/design/0009-knowledge-and-cost-gates.md).
- [x] Implement read-only knowledge validation and evidence/history inspection, including stale support, competing revisions, coverage gaps, and unverified attribution, under [decision 0010](docs/design/0010-read-only-knowledge-inspection.md).
- [x] Specify and implement explicit-policy signed receipt verification with optional pinned crypto, revocation/expiry checks, and a fictional offline host demonstration under [decision 0011](docs/design/0011-explicit-host-receipts.md).
- [x] Add a narrow host-configured verification tool that fixes project, policy, lookup, and clock outside model requests, with adversarial request tests under [decision 0012](docs/design/0012-pinned-harness-verification.md).
- [ ] Select and demonstrate one authenticated host receipt binding and a serialized stale/concurrent/interrupted acceptance protocol before shipping a knowledge writer.
- [ ] Evaluate optional model enrichment and task ranking against a deterministic retrieval and existing-agent baseline.

**Purpose:** Ship useful local structure and evidence before model enrichment or infrastructure.

**Completed subset:** The [prototype contract](docs/specs/local-inventory-v1.md) and [working walkthrough](examples/local-inventory.md) describe the implemented inventory subset. Every invocation reconstructs current inputs; matching consecutive captures are an optimistic observation, not an atomic snapshot against arbitrary writers. Full program-format, coherence, and consumer-release milestones remain incomplete.

**Cache increment:** The [cache contract](docs/specs/local-cache-v1.md) adds explicitly selected external storage, compatible reuse only after full local verification, recovery diagnostics, and whole-file publication. It does not complete incremental extraction or the broader sharing contract; no cost savings are claimed.

**Knowledge and measurement increment:** The [knowledge contract](docs/specs/project-knowledge-v1.md) specifies records, dependencies, receipt payload requirements, views, and failure meanings. It does not implement attribution or acceptance. The [measurement tool](benchmarks/README.md) publishes nine samples from one synthetic Windows run; extraction/freshness and cache subphases remain grouped, with no general savings claim.

**Reader increment:** The [knowledge inspector](docs/specs/knowledge-inspection-v1.md) and [working example](examples/knowledge-inspection.md) validate existing records and report evidence, structural history, gaps, and pending attribution. They do not establish effective accepted intent, authenticate conversation, or write records. Full coherence and program-format milestones remain open.

**Receipt increment:** The [explicit-policy verifier](docs/specs/host-receipts-v1.md) authenticates signed host assertions under a caller-pinned policy, with a fictional offline demonstration. It does not establish a real developer channel, consume approval events, change default attribution, or accept records. The [acceptance protocol draft](docs/specs/knowledge-acceptance-draft.md) records required serialization, commit/recovery, and event-registry outcomes; these remain unimplemented.

**Harness verification increment:** The [host-configured tool](docs/specs/harness-verification-v1.md) keeps trust selections outside its two-identity model request and demonstrates rejection of authority substitution. It is an internal verification adapter, not a public SDK, host/process sandbox, authenticated human channel, signer, or writer. The live-user and acceptance gate remains unchecked.

**Next gates:** Demonstrate a concrete authenticated user-event host adapter with protected signer/policy parameters and implement the serialized stale/concurrent/interrupted acceptance protocol before recording conversational requirements; then ship checked recording and a real agent walkthrough. Broaden and separate cost measurements before incremental scan optimization. Keep GLiNER-family models and Jev as optional evaluation candidates rather than dependencies. Coherence increments and executable IR have separate acceptance evidence; inventory/cache/reader/receipt progress cannot complete interpreter or compiler gates.

### 2. Build the core

- [ ] Build a parser and validator for the defined format.
- [ ] Build a reference interpreter for small supported programs.
- [ ] Deliver an initial CLI over the supported core operations, with documented automation results and failure behavior.
- [ ] Add structured edits that check their starting version and validate the result before acceptance.
- [ ] Build the first source adapter and rebuildable snapshots with source-linked overview and task views.
- [ ] Demonstrate the specified language-independent inventory, declared relationships, conversational knowledge, and local lifecycle before deep semantic adapters or source editing.
- [ ] Detect active and offline changes, invalidate affected findings, and publish only coherent refreshed snapshots.
- [ ] Add candidate source checks and the specified application protocol while preserving unrelated code and dirty files.
- [ ] Add core behavior tests to the existing CI, including unsupported effects and execution limits.

**Purpose:** Prove that the format can represent, run, and safely change programs.

**Done when:** Small programs run with expected results. Invalid programs, broken references, and stale edits are rejected. A failed graph edit leaves the previous accepted program intact. Source-adoption tests demonstrate declared preservation, freshness, unsupported-operation, and recovery guarantees, including changes made while stopped. Compiler execution and source navigation have distinct support boundaries.

### 3. Generate a useful application

- [ ] Define the minimum data, permission, and interface extensions needed by the worked example.
- [ ] Build TypeScript and PostgreSQL targets for the project task application.
- [ ] Generate its initial behavior and the administrator archive change.
- [ ] Check behavior and permissions through server requests, including requests that bypass the interface.
- [ ] Demonstrate a short setup-to-prompt workflow in a user's new project.
- [ ] Demonstrate a real change or fix in a supported existing project while preserving unrelated code and its build/test workflow.
- [ ] Demonstrate external edits, stop/edit/restart reconciliation, cache reconstruction, and stale-proposal rejection in that workflow.
- [ ] Demonstrate navigation from an overview through relevant nested and cross-component relationships, with explicit unknowns.
- [ ] Demonstrate an external API harness invoking the CLI and consuming its results without requiring an SDK.

**Purpose:** Show that one connected representation can produce a useful application.

**Done when:** The generated application passes behavior and permission checks before and after the archive change. Accepted changes include any required data migration and readable explanation. The new-project, existing-project, and external-harness consumer journeys pass their documented checks within explicit support boundaries. Existing-source adoption meets the [demonstration cases](docs/existing-repositories.md#required-demonstration); conceptual walkthroughs alone do not complete this gate.

### 4. Measure the benefit

- [ ] Publish a reproducible comparison against ordinary AI file editing.
- [ ] Use the same tasks, model configuration, acceptance checks, and attempt limits; document approach-specific tools.
- [ ] Report correctness, total tokens, repair attempts, latency, and review effort.
- [ ] Measure setup effort and cover both new-project work and changes or fixes in existing projects.
- [ ] Measure cold discovery, warm startup verification, offline-change reconciliation, active refresh, view retrieval, and context size.
- [ ] Run the specified local-only, Git-committed graph, and optional shared-cache comparison, including total five-developer and infrastructure costs.
- [ ] Include a complex-project scenario with nested and cross-component relationships; document scale, coverage, and omissions.
- [ ] Include failed outcomes and explain how measurements were collected.

**Purpose:** Find out whether the representation makes correct changes easier or cheaper.

**Done when:** Someone else can rerun the comparison and inspect both the results and their limits. A finding of no improvement still completes the experiment.

### 5. Demonstrate portability

- [ ] Add a WebAssembly target for the supported computational core.
- [ ] Document which operations are supported and which require unavailable host capabilities.
- [ ] Run matching behavior tests against the reference interpreter and WebAssembly runtime.

**Purpose:** Prove that a shared program can execute through different targets.

**Done when:** The same supported programs pass matching tests in both runtimes. Unsupported operations are reported explicitly. This milestone does not promise that the full task application runs unchanged in WebAssembly.

### 6. Expand from evidence

- [ ] Add domain extensions only for concrete use cases.
- [ ] Add source adapters and semantic extensions across languages, frameworks, runtimes, and domains with explicit meanings and ownership boundaries.
- [ ] Improve the model editing interface using measured failures and costs.
- [ ] Add a public SDK over the same core when a concrete embedding use case justifies it.
- [ ] Add compatibility tests and document boundaries for each addition.

**Purpose:** Grow coverage without losing precise meanings or reliable changes.

**Done when:** Each accepted addition has a use case, documented boundaries, and passing compatibility tests. Track subsequent expansion as separate increments.

## Current boundaries

The repository contains read-only local inventory, knowledge inspection, and optional explicit-policy receipt verification, external snapshot storage, a source-run CLI, a local cost measurement tool/report, documentation, examples, and quality tooling. Its versioned prototype output is provisional; there is no stable SDK or executable IR API. Reusable core, CLI first, SDK later, consumer journeys, universal coherence, portable existing-source state, and conversational knowledge are accepted. The coherence and knowledge specifications, bounded inventory/cache/reader/receipt subsets, and small local cost baseline are complete; the full milestones are not. Compiler language, final IR encoding, deeper adapters, knowledge writing/live user-event adapters, incremental extraction, source application/recovery, and remote bindings remain later work.

See the [architecture](docs/architecture.md) and [worked example](examples/project-tasks.md) for the proposed design.
