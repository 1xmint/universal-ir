# Proposed architecture

Everything in this document describes proposed behavior. The current repository contains documentation only.

## The flow

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

## The program graph

A graph is a set of connected parts. Here, those parts describe a program and the connections show how they depend on one another.

The small core would represent typed values, functions, references, and effects. Later extensions would describe application data, permissions, interfaces, and other domain-specific behavior.

- **Stable identities:** Each editable part has an identity that survives renaming and rearrangement. References use those identities, so changing a display name does not silently disconnect the program.
- **Types:** Values and operations declare the kinds of data they accept and produce. Checks reject incompatible connections.
- **Effects:** Reading stored data, changing it, contacting a service, or accessing a device is explicit. Declaring an effect does not itself grant permission to perform it.
- **Permissions:** Rules describe who may perform protected actions. Target integrations must enforce those rules at trusted execution boundaries.

The accepted graph is the source of truth for generated artifacts. Existing libraries can be connected through adapters with documented interfaces and effects. The project does not need to rewrite every dependency into its own format.

## Editing and checking

An AI editor would receive the relevant parts of the graph and propose a bounded change against an identified version. The system would apply the edit to a candidate, check it, and accept it as a new version only if the required checks pass.

Checks would cover references, types, supported operations, and declared effects. Application extensions would add permission and behavior checks. Tests and simulation would check selected outcomes; proofs could establish specific properties where practical.

Checks cannot automatically establish that an unclear request matches the user's intention. Assumptions and unresolved choices must remain visible. Edit conflicts and missing information must be reported rather than silently guessed away.

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

The implementation language and final encoding are undecided. Milestone 1 will record those choices; this document defines no executable syntax or public executable API.

## Existing ideas to learn from

- [MLIR](https://mlir.llvm.org/docs/LangRef/) describes typed operations, extensible dialects, and multiple forms of the same program representation.
- [WebAssembly Component Model](https://component-model.bytecodealliance.org/composing-and-distributing/composing.html) provides interfaces and composition between components originating in different languages.

These are design references, not current project dependencies. Follow the [roadmap](../ROADMAP.md) for the order of implementation.
