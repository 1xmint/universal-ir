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

A local CLI will be the first entry point, so existing coding agents can call the tools through terminal commands. A public SDK will follow later for custom hosts. This priority is accepted in [decision 0002](design/0002-cli-first.md); neither interface is implemented yet. See the [usage journeys](../examples/using-with-ai.md).

The core owns program representation, validation, editing, interpretation, and compilation behavior. The CLI is an adapter over that core, and the future SDK will use the same behavior. Exact commands, automation outputs, diagnostics, and exit behavior must be specified before CLI release.

The intended user installs the tool into their development environment, connects a supported project and coding agent, and prompts the agent to do work. An API harness can invoke the CLI as a tool before an SDK is available. The host owns repository creation, general command execution, and deployment authorization; Universal IR provides the supported representation and checkable operations. These consumer journeys are accepted in [decision 0003](design/0003-real-development-workflows.md).

## Adopting existing repositories

The current compiler flow describes a program managed through its graph. It does not yet define how to adopt an existing source repository.

An adoption design must specify supported languages and constructs, mappings to existing files, the authority of source versus graph, freshness after external edits, and treatment of unsupported parts. It must preserve unrelated code and the project's existing build and test workflow.

For graph-managed generated artifacts, the accepted graph remains the source of truth. For existing source files, the adoption policy is still open. Do not treat independently edited source files and a graph as two simultaneous authorities, or claim a partial project index captures complete execution semantics.

The first consumer release needs a documented, bounded existing-project workflow. It does not need to import every language or replace every framework. These boundaries must be explicit before the project can claim that an agent can use it to fix an existing repository.

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
