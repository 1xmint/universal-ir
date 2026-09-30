# Universal IR

A shared program format for AI to build, check, and change software across platforms.

## Vision

Give AI one shared way to build and change software. Check that the software follows its rules, then turn it into programs that run on different systems. People should always be able to inspect what it does.

The long-term ambition is one universal foundation for any kind of software, across languages, frameworks, and runtimes. It should make complex projects coherent for agents: show the big picture, connect it to relevant detail, and keep those views tied to current evidence. Support will grow through adapters and extensions whose boundaries are demonstrated.

Here, **IR** means **a shared program format**. In compiler terminology, it stands for *intermediate representation*: a form of a program that tools can work with and translate into other forms.

## The idea

Connect purpose, structure, behavior, and evidence in one shared representation. Use a graph to capture both nested parts and relationships across them: data, functions, rules, services, and their dependencies. Give agents a compact overview and expandable task views, rather than requiring every detail in one prompt.

For graph-managed programs, let AI propose small structured edits, check each candidate, and use target compilers to produce runnable software. Different targets would handle how supported programs run on a server, in a browser, or on another system.

For existing projects, the proposed adoption path keeps source files authoritative and builds a rebuildable view of supported facts. External changes, including changes made while the tool is stopped, must be reconciled before presenting that view as current. Unknown behavior stays visible. The exact source-adoption contract still needs specification.

Readable views would help people and agents understand a project, review a change, and trace behavior back to its rules and evidence. Source state, check results, deployments, and runtime observations would remain distinct.

The accepted delivery direction is [reusable core, CLI first, SDK later](docs/design/0002-cli-first.md). Existing coding agents will use the CLI through terminal tools; custom integrations can use a public SDK later. Both will share the same core behavior.

## Current state

This repository contains documentation, examples, and documentation quality tooling. There is no executable program format, source index, state service, usable CLI, compiler, runtime, or public executable API yet. Broad software support, fast coherent views, and lower token costs are goals to test, not demonstrated results.

The first implementation step is to specify the small versioned core and its source-backed adoption contract: typed values, functions, references, effects, evidence, snapshots, and checked edits. The implementation language, final encoding, first adapter, and exact interfaces remain milestone 1 decisions.

## Intended use in your own projects

The intended setup is: install the CLI, connect a supported new or existing project to your coding agent, and start prompting it to do development work. Universal IR would give the agent a coherent program structure and tools to inspect, change, and check it.

- **Coding subscription:** Keep using your existing coding agent and authentication. Its terminal tools invoke the Universal IR CLI while it creates a project, changes a feature, or fixes a supported existing repository.
- **API-backed harness:** Register the CLI as a tool in your existing model loop. Use its structured results and checks to guide work; adopt a public SDK later if a direct integration is useful.

These are planned consumer workflows, not working setup instructions. There is no installer or usable CLI yet. The [adoption proposal](docs/existing-repositories.md) describes ownership, pause/resume reconciliation, checked source changes, and unsupported parts; it still needs precise contracts and a working demonstration.

The [real development examples](examples/using-with-ai.md) explain both journeys. The [accepted product-use decision](docs/design/0003-real-development-workflows.md) records the goal. To help build Universal IR itself, use the [contribution guide](CONTRIBUTING.md).

## Start here

- [Roadmap](ROADMAP.md): milestones and what it takes to complete them.
- [Architecture](docs/architecture.md): proposed parts and how they connect.
- [Coherent project views](docs/coherence.md): nested structure, cross-cutting relationships, and different kinds of state.
- [Existing-repository adoption](docs/existing-repositories.md): proposed freshness and checked-change lifecycle.
- [Project task example](examples/project-tasks.md): one application and a change to its rules.
- [Complex-project example](examples/complex-project.md): connected services, offline edits, and source versus runtime state.
- [Real development examples](examples/using-with-ai.md): using a coding subscription or API harness for your own projects.
- [Development readiness](docs/development.md): quality gates, review policy, and GitHub controls.
- [Design decisions](docs/design/README.md): durable records of accepted choices and tradeoffs.
- [Contributing](CONTRIBUTING.md): how to help refine and build the project.

## License

[MIT](LICENSE), copyright 2026 1xmint.
