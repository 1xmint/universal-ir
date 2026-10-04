# Universal IR

A shared program format for AI to build, check, and change software across platforms.

## Vision

Give AI one shared way to build and change software. Check that the software follows its rules, then turn it into programs that run on different systems. People should always be able to inspect what it does.

The long-term ambition is one universal foundation for any kind of software, across languages, frameworks, and runtimes. It should make complex projects coherent for agents: show the big picture, connect it to relevant detail, and keep those views tied to current evidence. Support will grow through adapters and extensions whose boundaries are demonstrated.

Here, **IR** means **a shared program format**. In compiler terminology, it stands for *intermediate representation*: a form of a program that tools can work with and translate into other forms.

## The idea

Connect purpose, structure, behavior, and evidence in one shared representation. Use a graph to capture both nested parts and relationships across them: data, functions, rules, services, and their dependencies. Give agents a compact overview and expandable task views, rather than requiring every detail in one prompt.

For graph-managed programs, let AI propose small structured edits, check each candidate, and use target compilers to produce runnable software. Different targets would handle how supported programs run on a server, in a browser, or on another system.

For existing projects, the accepted design keeps source files authoritative and builds a rebuildable view of supported facts. Read-only inventory captures files, containment, optional configuration, document links, and current content identities, with optional verified local snapshot storage. A separate knowledge inspector reads existing committed records, traces evidence, and shows conflicting revisions. Authenticated recording and shared snapshots remain later increments; views stay tied to actual inputs.

Readable views would help people and agents understand a project, review a change, and trace behavior back to its rules and evidence. Source state, check results, deployments, and runtime observations would remain distinct.

The accepted delivery direction is [reusable core, CLI first, SDK later](docs/design/0002-cli-first.md). Existing coding agents will use the CLI through terminal tools; custom integrations can use a public SDK later. Both will share the same core behavior.

## Current state

This repository contains working read-only local inventory and knowledge inspection, documentation, examples, and quality tooling. It has no executable program format, semantic source adapter, state service, compiler, runtime, or stable public SDK. Broad software support, fast coherent views, and lower token costs are goals to test, not demonstrated results.

The [portable project-coherence specification](docs/specs/project-coherence.md) defines the broader first proof: inventory across languages, connected views, conversational project knowledge, and freshness. The [local inventory contract](docs/specs/local-inventory-v1.md), [local cache contract](docs/specs/local-cache-v1.md), and [knowledge inspection contract](docs/specs/knowledge-inspection-v1.md) implement bounded subsets in Python, with provisional versioned JSON and source-run CLI I/O. Conversational recording/approval, incremental extraction, deeper adapters, checked source edits, and compilation follow later; executable IR language and encoding remain open.

The [knowledge record specification](docs/specs/project-knowledge-v1.md) now defines evidence, attribution, revisions, and failure meanings before a writer or host integration is built. The [local measurement tool and baseline](benchmarks/README.md) record uncached/cold/warm costs on a small synthetic fixture; they do not demonstrate faster agent work or reduced tokens.

For a configured project with existing knowledge records, run `python -B -m universal_ir knowledge /path/to/project`. It reports matching/changed/unresolved evidence, claimed origin, unverified developer attribution, and competing included heads without choosing an approved requirement. Try the [working fictional example](examples/knowledge-inspection.md); no authoring or approval command is available yet.

The optional [host receipt verifier](docs/specs/host-receipts-v1.md) checks signed assertions under an explicitly pinned policy. The [offline demonstration](examples/host-receipts.md) uses fictional events and an ephemeral key. It does not authenticate a real conversation, change default knowledge attribution, or accept/write records. A concrete host adapter and serialized acceptance remain required before conversational recording.

An internal [harness verification tool](examples/harness-verification.md) now fixes the selected project, trust policy, receipt lookup, and clock outside model requests. Its narrow handler verifies registered receipts by identity and rejects authority substitution. The host still must isolate its trusted configuration from the model's other tools; human-event authentication and acceptance remain unimplemented.

The [prepared-candidate verifier](examples/prepared-receipts.md) now checks an external developer-claim assertion bound to its exact proposal and current review context. It rejects reuse after source or proposal changes, with a host-fixed handler accepting only a registered preparation identity. Its fictional demonstration establishes no real human event or accepted intent; no writer is available.

Read-only [knowledge preparation](examples/knowledge-preparation.md) now reviews a complete external candidate against current evidence and included history before it enters project storage. It returns exact wording, a structural transition preview, and input-bound preconditions. A preview does not approve, authenticate, or write the proposal; the real user and acceptance gates remain open.

## Try the first working command

With Python 3.12+ and Git installed, run from this checkout:

~~~sh
python -m universal_ir inventory /path/to/your/project
~~~

On Windows, the repository's development environment can use `.venv\Scripts\python -m universal_ir inventory "C:\path\to\your\project"`.

The command leaves the selected project untouched and returns a bounded JSON overview with containment, guidance candidates, classification hypotheses, content identity, freshness, and exclusions. Expand an included directory with `--path services`; save `--full` output for later `--baseline` comparison. It also works on non-Git folders, but requires the Git executable for ignore rules. Each request rescans contents; there is no ongoing monitoring.

Add `--cache-dir /outside/project/cache` to persist verified snapshots in an external local directory. Missing or damaged snapshots are reconstructed; unavailable storage is reported alongside the fresh local view. A cache hit still performs full source verification and does not imply faster startup. See the [working walkthrough](examples/local-inventory.md) for setup, storage, comparison, harness integration, and limitations.

## Intended use in your own projects

The intended setup is: install the CLI, connect a supported new or existing project to your coding agent, and start prompting it to do development work. Universal IR would give the agent a coherent program structure and tools to inspect, change, and check it.

- **Coding subscription:** Keep using your existing coding agent and authentication. Its terminal tools invoke the Universal IR CLI while it creates a project, changes a feature, or fixes a supported existing repository.
- **API-backed harness:** Register the CLI as a tool in your existing model loop. Use its structured results and checks to guide work; adopt a public SDK later if a direct integration is useful.

The full consumer workflows remain planned. The inventory and knowledge readers can be invoked today from the source checkout; there is no packaged installer or automatic agent integration. The broader design lets the existing agent prefill purpose and refine it through conversation while keeping interpretations and developer declarations distinguishable. This prototype inspects existing records but does not write or authenticate them. Local inspection makes no model calls; AI interpretation and agent work have separate costs to measure.

The [coherence specification](docs/specs/project-coherence.md) covers local and optional shared views, including awareness of published changes before a graph is ready. The broader [adoption proposal](docs/existing-repositories.md) covers future checked source changes, whose application guarantees still need contracts and demonstration.

The [real development examples](examples/using-with-ai.md) explain both journeys. The [accepted product-use decision](docs/design/0003-real-development-workflows.md) records the goal. To help build Universal IR itself, use the [contribution guide](CONTRIBUTING.md).

## Start here

- [Roadmap](ROADMAP.md): milestones and what it takes to complete them.
- [Architecture](docs/architecture.md): proposed parts and how they connect.
- [Coherent project views](docs/coherence.md): nested structure, cross-cutting relationships, and different kinds of state.
- [Portable project-coherence specification](docs/specs/project-coherence.md): repository storage, conversational knowledge, lifecycle, and collaboration contracts.
- [Local inventory prototype](examples/local-inventory.md): working commands, with the [versioned contract](docs/specs/local-inventory-v1.md).
- [Knowledge inspection](examples/knowledge-inspection.md): working evidence/history views and a fictional fixture, with the [versioned contract](docs/specs/knowledge-inspection-v1.md).
- [Host receipt verification](examples/host-receipts.md): optional signed assertion checks and the remaining live-host/acceptance boundary.
- [Harness verification wiring](examples/harness-verification.md): a working model-facing verification tool with host-owned settings and explicit isolation limits.
- [Knowledge preparation](examples/knowledge-preparation.md): review an external proposal while preserving current records and conflicting history.
- [Prepared review verification](examples/prepared-receipts.md): verify an exact external host assertion and reject reuse after the review changes.
- [Existing-repository adoption](docs/existing-repositories.md): proposed freshness and checked-change lifecycle.
- [Project task example](examples/project-tasks.md): one application and a change to its rules.
- [Complex-project example](examples/complex-project.md): connected services, offline edits, and source versus runtime state.
- [Real development examples](examples/using-with-ai.md): using a coding subscription or API harness for your own projects.
- [Development readiness](docs/development.md): quality gates, review policy, and GitHub controls.
- [Design decisions](docs/design/README.md): durable records of accepted choices and tradeoffs.
- [Contributing](CONTRIBUTING.md): how to help refine and build the project.

## License

[MIT](LICENSE), copyright 2026 1xmint.
