# Universal IR

A shared program format for AI to build, check, and change software across platforms.

## Vision

Give AI one shared way to build and change software. Check that the software follows its rules, then turn it into programs that run on different systems. People should always be able to inspect what it does.

Here, **IR** means **a shared program format**. In compiler terminology, it stands for *intermediate representation*: a form of a program that tools can work with and translate into other forms.

## The idea

Store a program as connected, structured parts: data, functions, rules, and the relationships between them. Let AI propose small edits to those parts. Check each change before accepting it, then use target compilers to turn the program into runnable software.

The shared format would describe what the program does. Different targets would handle how it runs on a server, in a browser, or on another supported system.

Readable views would help people understand the program, review a change, and trace behavior back to its rules.

The accepted delivery direction is [reusable core, CLI first, SDK later](docs/design/0002-cli-first.md). Existing coding agents will use the CLI through terminal tools; custom integrations can use a public SDK later. Both will share the same core behavior.

## Current state

This repository contains documentation, examples, and documentation quality tooling. There is no executable program format, compiler, runtime, or public executable API yet. Support across platforms and lower token costs are goals to test, not demonstrated results.

The first implementation step is to define a small, versioned program format with typed values, functions, references, and explicit effects. The implementation language and final encoding will be chosen during that milestone.

## Intended use in your own projects

The intended setup is: install the CLI, connect a supported new or existing project to your coding agent, and start prompting it to do development work. Universal IR would give the agent a coherent program structure and tools to inspect, change, and check it.

- **Coding subscription:** Keep using your existing coding agent and authentication. Its terminal tools invoke the Universal IR CLI while it creates a project, changes a feature, or fixes a supported existing repository.
- **API-backed harness:** Register the CLI as a tool in your existing model loop. Use its structured results and checks to guide work; adopt a public SDK later if a direct integration is useful.

These are planned consumer workflows, not working setup instructions. There is no installer or usable CLI yet. Existing-repository adoption still needs defined source adapters, source/graph consistency rules, and supported-language boundaries.

The [real development examples](examples/using-with-ai.md) explain both journeys. The [accepted product-use decision](docs/design/0003-real-development-workflows.md) records the goal. To help build Universal IR itself, use the [contribution guide](CONTRIBUTING.md).

## Start here

- [Roadmap](ROADMAP.md): milestones and what it takes to complete them.
- [Architecture](docs/architecture.md): proposed parts and how they connect.
- [Project task example](examples/project-tasks.md): one application and a change to its rules.
- [Real development examples](examples/using-with-ai.md): using a coding subscription or API harness for your own projects.
- [Development readiness](docs/development.md): quality gates, review policy, and GitHub controls.
- [Design decisions](docs/design/README.md): durable records of accepted choices and tradeoffs.
- [Contributing](CONTRIBUTING.md): how to help refine and build the project.

## License

[MIT](LICENSE), copyright 2026 1xmint.
