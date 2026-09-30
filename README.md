# Universal IR

A shared program format for AI to build, check, and change software across platforms.

## Vision

Give AI one shared way to build and change software. Check that the software follows its rules, then turn it into programs that run on different systems. People should always be able to inspect what it does.

Here, **IR** means **a shared program format**. In compiler terminology, it stands for *intermediate representation*: a form of a program that tools can work with and translate into other forms.

## The idea

Store a program as connected, structured parts: data, functions, rules, and the relationships between them. Let AI propose small edits to those parts. Check each change before accepting it, then use target compilers to turn the program into runnable software.

The shared format would describe what the program does. Different targets would handle how it runs on a server, in a browser, or on another supported system.

Readable views would help people understand the program, review a change, and trace behavior back to its rules.

## Current state

This repository contains documentation and one worked example. There is no executable program format, compiler, runtime, or public executable API yet. Support across platforms and lower token costs are goals to test, not demonstrated results.

The first implementation step is to define a small, versioned program format with typed values, functions, references, and explicit effects. The implementation language and final encoding will be chosen during that milestone.

## Start here

- [Roadmap](ROADMAP.md): milestones and what it takes to complete them.
- [Architecture](docs/architecture.md): proposed parts and how they connect.
- [Project task example](examples/project-tasks.md): one application and a change to its rules.
- [Contributing](CONTRIBUTING.md): how to help refine and build the project.

## License

[MIT](LICENSE), copyright 2026 1xmint.
