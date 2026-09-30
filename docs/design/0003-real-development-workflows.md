# 0003: Real development workflows for product users

**Status:** Accepted

**Accepted:** September 30, 2026

## Context

The maintainer clarified that the subscription and API examples should describe people using Universal IR for their own development work. Contributor onboarding did not capture that intent.

The intended users want less setup work and a coherent structure that helps an existing coding agent understand and complete tasks in a new or existing project. Developers with an API-backed harness want the same capabilities inside their existing model loop.

## Decision

- Treat work in users' own projects as the main product journey. Keep contributing instructions in the contribution guide.
- Preserve the accepted delivery direction: reusable core, CLI first, SDK later.
- Plan a short setup path that connects a supported project and an existing coding agent to the CLI, followed by ordinary task prompts.
- Include both new-project creation and changes or fixes in a supported existing repository as consumer acceptance scenarios.
- Let an existing API harness invoke the CLI through its tool interface before a public SDK exists. The harness continues to own model access, orchestration, permissions, and budget.
- Require explicit support boundaries, checkable changes, and evidence for any performance improvement.
- Keep the shared program representation and compiler vision. These journeys do not establish a general-purpose agent runtime or promise support for arbitrary source repositories.

## Consequences

The main usage guide describes intended consumer workflows. It must still state that the installer, setup integration, CLI, compiler, and SDK are not implemented.

Existing-repository adoption becomes an explicit design and implementation requirement. The project must decide how source files map to a graph, which representation is authoritative, how external edits are detected, and what happens to unsupported code. Those technical decisions remain open.

A subscription or API key supplies model access through another tool. Users should not need to move their authentication or replace their agent host to adopt Universal IR.

## Validation

Before claiming a usable consumer release, demonstrate a supported new-project workflow, a real change or fix in an existing project, and an external harness calling the CLI. Document setup steps, support boundaries, and check results.

Evaluate task success, total token use, repair work, latency, review effort, and setup effort against a baseline. A structured representation alone does not establish better performance.
