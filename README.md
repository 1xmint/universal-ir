# Universal IR

A shared program format for AI to build, check, and change software across platforms.

## Vision

Give AI one shared way to build and change software. Check that the software follows its rules, then turn it into programs that run on different systems. People should always be able to inspect what it does.

The long-term ambition is one universal foundation for any kind of software, across languages, frameworks, and runtimes. It should make complex projects coherent for agents: show the big picture, connect it to relevant detail, and keep those views tied to current evidence. Support will grow through adapters and extensions whose boundaries are demonstrated.

Here, **IR** means **a shared program format**. In compiler terminology, it stands for *intermediate representation*: a form of a program that tools can work with and translate into other forms.

## The idea

Connect purpose, structure, behavior, and evidence in one shared representation. Use a graph to capture both nested parts and relationships across them: data, functions, rules, services, and their dependencies. Give agents a compact overview and expandable task views, rather than requiring every detail in one prompt.

For graph-managed programs, let AI propose small structured edits, check each candidate, and use target compilers to produce runnable software. Different targets would handle how supported programs run on a server, in a browser, or on another system.

For existing projects, the accepted design keeps source files authoritative and builds a rebuildable view of supported facts. Shared configuration and durable project knowledge travel in a committed `.uir/` area; local caches and working views describe each checkout. Optional shared snapshots can reuse compatible extraction. External edits must be reconciled before presenting a view as current. None of these operations is implemented yet.

Readable views would help people and agents understand a project, review a change, and trace behavior back to its rules and evidence. Source state, check results, deployments, and runtime observations would remain distinct.

The accepted delivery direction is [reusable core, CLI first, SDK later](docs/design/0002-cli-first.md). Existing coding agents will use the CLI through terminal tools; custom integrations can use a public SDK later. Both will share the same core behavior.

## Current state

This repository contains documentation, examples, and documentation quality tooling. There is no executable program format, source index, state service, usable CLI, compiler, runtime, or public executable API yet. Broad software support, fast coherent views, and lower token costs are goals to test, not demonstrated results.

The [portable project-coherence specification](docs/specs/project-coherence.md) defines the first proof: inventory across languages, connected views, conversational project knowledge, and freshness. Deep semantic adapters, checked source edits, executable IR, and compilers follow in later increments. Concrete metadata schemas, extraction/CLI interfaces, and implementation language must be specified before building that proof; final executable IR encoding remains open.

## Intended use in your own projects

The intended setup is: install the CLI, connect a supported new or existing project to your coding agent, and start prompting it to do development work. Universal IR would give the agent a coherent program structure and tools to inspect, change, and check it.

- **Coding subscription:** Keep using your existing coding agent and authentication. Its terminal tools invoke the Universal IR CLI while it creates a project, changes a feature, or fixes a supported existing repository.
- **API-backed harness:** Register the CLI as a tool in your existing model loop. Use its structured results and checks to guide work; adopt a public SDK later if a direct integration is useful.

These are planned consumer workflows, not working setup instructions. There is no installer or usable CLI yet. The first design lets the existing agent prefill purpose from evidence and refine it through normal conversation, while keeping interpretations and developer declarations distinguishable. Local inventory requires no model calls by design; AI interpretation and agent work have separate costs to measure.

The [coherence specification](docs/specs/project-coherence.md) covers local and optional shared views, including awareness of published changes before a graph is ready. The broader [adoption proposal](docs/existing-repositories.md) covers future checked source changes, whose application guarantees still need contracts and demonstration.

The [real development examples](examples/using-with-ai.md) explain both journeys. The [accepted product-use decision](docs/design/0003-real-development-workflows.md) records the goal. To help build Universal IR itself, use the [contribution guide](CONTRIBUTING.md).

## Start here

- [Roadmap](ROADMAP.md): milestones and what it takes to complete them.
- [Architecture](docs/architecture.md): proposed parts and how they connect.
- [Coherent project views](docs/coherence.md): nested structure, cross-cutting relationships, and different kinds of state.
- [Portable project-coherence specification](docs/specs/project-coherence.md): repository storage, conversational knowledge, lifecycle, and collaboration contracts.
- [Existing-repository adoption](docs/existing-repositories.md): proposed freshness and checked-change lifecycle.
- [Project task example](examples/project-tasks.md): one application and a change to its rules.
- [Complex-project example](examples/complex-project.md): connected services, offline edits, and source versus runtime state.
- [Real development examples](examples/using-with-ai.md): using a coding subscription or API harness for your own projects.
- [Development readiness](docs/development.md): quality gates, review policy, and GitHub controls.
- [Design decisions](docs/design/README.md): durable records of accepted choices and tradeoffs.
- [Contributing](CONTRIBUTING.md): how to help refine and build the project.

## License

[MIT](LICENSE), copyright 2026 1xmint.
