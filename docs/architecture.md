# Proposed architecture

The runtime behavior in this document is proposed. The current repository contains documentation, examples, and documentation quality tooling.

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

## Where the coding agent fits

An existing agent host owns the model conversation, authentication, tool permissions, and budget. Universal IR would provide the program representation, edit interface, checks, and compilers. The model might run remotely while those tools run locally.

A local CLI would let existing coding agents call the tools through terminal commands. An SDK would let custom hosts call the same core directly. CLI first is a proposed adoption path; the entry-point priority remains a milestone 1 decision. See the [usage journeys](../examples/using-with-ai.md).

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

The compiler implementation language and final encoding are undecided. Python is used only for repository quality tooling. Milestone 1 will record core choices; this document defines no executable syntax or public executable API. Keep the reasons for accepted choices in [design decisions](design/README.md).

## Existing ideas to learn from

- [MLIR](https://mlir.llvm.org/docs/LangRef/) describes typed operations, extensible dialects, and multiple forms of the same program representation.
- [WebAssembly Component Model](https://component-model.bytecodealliance.org/composing-and-distributing/composing.html) provides interfaces and composition between components originating in different languages.

These are design references, not current project dependencies. Follow the [roadmap](../ROADMAP.md) for the order of implementation.
