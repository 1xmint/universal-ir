# Coherent views of complex software

The universal-foundation direction is accepted in [decision 0004](design/0004-universal-coherence.md). The first inventory, knowledge, lifecycle, and collaboration contracts are specified in [portable project coherence](specs/project-coherence.md), under decisions [0005](design/0005-portable-project-state.md) and [0006](design/0006-conversational-knowledge.md). Broader semantic mechanisms below remain proposed. There is no working project index, state service, CLI, or compiler yet.

## What instantly coherent means

An agent should quickly find the project's purpose, structure, relevant behavior, applicable rules, available checks, and unresolved boundaries. Each answer should be expandable and traceable to the inputs and version it describes.

This is an access and correctness goal, not a promise that a model can understand an arbitrarily large system from one glance. Initial discovery, cold starts, reconciliation, and detailed analysis take work. A compact overview should reveal important dependencies and unknowns without claiming to contain every detail.

Measure time to a useful overview, time to a task-ready view, view size, retrieval cost, freshness, and successful changes. Faster access is useful only if the agent gets the right information.

## Nested structure and connections across it

A large project may contain products, subsystems, deployable services, packages, modules, functions, and expressions. Its behavior also crosses those boundaries: a permission rule affects several services; an event connects a producer and consumers; a schema connects storage, APIs, jobs, and migrations.

Use a graph for those relationships. A tree is one view of containment, not the only organization. The same component may appear in a deployment view, a domain view, and a task view without being duplicated as independent facts.

| View | Question it helps answer |
| --- | --- |
| Purpose | What are we building, for whom, and under which requirements? |
| System | Which subsystems exist and how do they communicate? |
| Component | What does this service or library own, expose, and depend on? |
| Behavior | How does this operation connect permissions, data, effects, and failure handling? |
| Implementation | Which declarations, references, and source regions implement the behavior? |
| Evidence | Which checks and observations support a claim, and for which version? |
| Change | What would this edit affect, preserve, invalidate, or leave unknown? |

Views must preserve links between levels. A service summary should lead to its interface and implementation; a function should lead back to its containing component and associated requirements. Views also need routes across levels, such as following a user request through an API, event, worker, and database.

Connections can form cycles: a worker changes data that drives another event, or several components share one policy. The graph must distinguish containment, calls, data flow, declared ownership, deployment, and observed causality. Being connected does not itself establish the same kind of dependency or prove that a change propagates along every edge.

For very large systems, views would group related components and expand them on demand. A boundary summary should expose the component's interfaces, known connections, and unknowns, with a path to underlying evidence. It must not hide an important relationship simply because it crosses a group boundary. Grouping and retrieval rules still need a precise specification and scale tests.

## Shared meaning with faithful extensions

The universal foundation would define identities, typed relationships, provenance, snapshots, changes, diagnostics, and evidence. Semantic extensions would describe concepts such as transactions, reactive interfaces, device access, distributed messages, and memory ownership.

Language and framework adapters would translate established facts into that foundation. Extensions must preserve distinctions that the common core cannot express. A source-backed relationship is not automatically a lowering into executable IR; compilation requires defined semantics and behavior checks for the supported subset.

For example, two languages' operations with the same display name need not have equivalent behavior. Unsupported concurrency or memory semantics must remain explicit rather than being flattened into a misleading common operation. Universal scope means extensibility toward any software domain; it does not establish present support for every language or runtime.

The foundation should admit domains beyond web applications: game simulation and rendering, embedded devices and timing, scientific computation and accelerators, compilers, and distributed infrastructure. Their extensions would need distinct behavioral contracts. A graph-shaped encoding alone cannot make those contracts equivalent or portable.

The eventual agent-facing encoding should be chosen through whole-task measurements. Keep the stored representation, views supplied to a model, and runnable target artifacts distinct. A compressed format that costs less to store may be unfamiliar to a model or require expensive expansions and repairs.

## Purpose, facts, hypotheses, and evidence

Code rarely establishes the complete reason for a feature or design choice. Declared requirements and decisions need an explicit home, ownership, and links to the relevant implementation. Updating an implementation should not silently rewrite its stated purpose to match.

The existing agent can prefill purpose from inspected evidence, then refine it through normal developer conversation. Store those interpretations with their supporting inputs and scope. A host-attested developer statement or approved declaration has a different origin; an AI paraphrase and a model's claim of approval do not automatically establish developer intent. Capture selected project knowledge rather than requiring a complete chat archive or manual questionnaire.

Committed `.uir/` configuration and durable records travel with the project, including links to existing documents. Local caches and drafts remain separate. Source-derived facts and summaries are versioned views, while developer requirements retain their authority when code changes. Known discrepancies should be surfaced; the first file inventory cannot discover every behavioral violation.

Each relationship should identify its origin and scope. Distinguish compiler-resolved facts, syntactic facts, declared contracts, inferred hypotheses, and test or runtime observations. An agent hypothesis may suggest where to investigate; it must not become a confirmed fact merely by being stored.

Findings should include the inputs, source locations where applicable, extraction method, and snapshot they describe. Unknown call targets and unavailable dependency behavior remain visible. Missing evidence is not evidence that an effect or dependency does not exist.

Links from checks to requirements also need origins: an agent claiming that a test covers a requirement is a proposal until reviewed or otherwise established. Passing a test establishes its observed outcome, not every associated business rule.

## Several kinds of state

The system needs separate records with explicit relationships, rather than one undifferentiated live state.

| State | What it describes | Freshness boundary |
| --- | --- | --- |
| Declared intent | Requirements, goals, decisions, and constraints | Version of the declarations; implementation agreement still needs evidence. |
| Development source | Current files, project configuration, and relevant dependencies | Content and configuration of the inspected workspace. |
| Derived representation | Extracted facts, relationships, and summaries | The exact source snapshot and adapter inputs used to build it. |
| Candidate change | Proposed edits and their resulting files | Base snapshot, candidate snapshot, and allowed edit scope. |
| Check evidence | Diagnostics and observed test outcomes | Exact checked candidate, check plan, and recorded environment. |
| Build and deployment | Produced artifacts and a deployed version | Artifact identity, build inputs, and deployment evidence. |
| Runtime observation | Events or measurements from a running system | Environment, observation time, coverage, and known collection limits. |

A source edit does not prove a deployment changed. A deployment does not prove its database matches a proposed migration. Runtime telemetry is optional, bounded evidence; it cannot promise immediate visibility into every external change or private state.

When inputs change, affected findings lose current status until refreshed. Historical check results remain useful history but cannot be shown as passing checks for a different candidate. A changed requirement can invalidate a summary or coverage relationship even if no source file changed.

For systems spanning repositories or environments, a view must identify which snapshots and configurations it joins. A workspace snapshot is not automatically a coherent release of the whole system. Cross-project connections need declared compatibility boundaries; unavailable repositories and environments remain explicit gaps.

## A focused view with expandable boundaries

For an archive-permission fix, an agent would receive the requirement, relevant operations, resolved references, affected data, known checks, applicable project guidance, and important unknowns. The view would carry a snapshot and a description of how its contents were selected.

The agent could expand a dependency or ask for additional source and evidence. Truncation and omitted relationships must be visible. Budget limits must not turn an incomplete dependency view into a claim that no other dependencies exist.

Summaries should be derived from identified inputs and refreshed when those inputs change. A model-generated summary needs the same freshness and evidence boundaries as other inferred content. Storing a summary does not remove the cost of verifying or updating it.

## Validation across scales

Use the [complex-project walkthrough](../examples/complex-project.md) to define concrete navigation and change scenarios. Check that a reader or agent can move from a system overview to relevant detail, follow cross-service relationships, and find unknowns without losing the snapshot or evidence trail.

The [coherence specification](specs/project-coherence.md) defines required first-proof lifecycle, attribution, sharing, and remote-awareness outcomes. The broader [adoption proposal](existing-repositories.md) adds future checked source changes. Concrete schemas, retrieval algorithms, source application guarantees, performance budgets, and runtime integrations remain later implementation contracts.
