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

## Try contributing with your coding agent

Clone this repository, open it in an existing coding agent, and ask the agent to read AGENTS.md before taking a small task from the roadmap. Your coding tool handles model authentication; repository checks need no model credentials.

~~~sh
git clone https://github.com/1xmint/universal-ir.git
cd universal-ir
~~~

The [AI usage examples](examples/using-with-ai.md) cover subscription-based tools, API-backed agents, and a proposed future journey for building your own app. The [contribution guide](CONTRIBUTING.md#local-checks) provides reproducible local checks.

## Start here

- [Roadmap](ROADMAP.md): milestones and what it takes to complete them.
- [Architecture](docs/architecture.md): proposed parts and how they connect.
- [Project task example](examples/project-tasks.md): one application and a change to its rules.
- [AI usage examples](examples/using-with-ai.md): how a coding subscription or API-backed agent fits.
- [Development readiness](docs/development.md): quality gates, review policy, and GitHub controls.
- [Design decisions](docs/design/README.md): durable records of accepted choices and tradeoffs.
- [Contributing](CONTRIBUTING.md): how to help refine and build the project.

## License

[MIT](LICENSE), copyright 2026 1xmint.
