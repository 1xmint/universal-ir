# 0002: Reusable core, CLI first, SDK later

**Status:** Accepted

**Accepted:** September 30, 2026

## Context

The first users are people working with existing coding agents. Those agents commonly have terminal tools, while developers embedding Universal IR inside a custom host need a direct library interface. The maintainer approved a reusable core with CLI first and SDK later.

This resolves the interface-priority question left open in [0001](0001-foundation.md). The rest of that foundation decision remains in effect.

## Decision

- Put program representation, validation, editing, interpretation, and compilation behavior in a reusable core.
- Deliver a local CLI as the first user entry point. Existing coding agents can invoke it through terminal tools using their existing model authentication.
- Keep the CLI as an adapter over the core. Domain rules must not depend on terminal interaction or live only in CLI command handlers.
- Specify automation-friendly results, diagnostics, and exit behavior before releasing the CLI. Exact commands and output formats remain to be designed.
- Add a public SDK later, when a concrete embedding use case justifies its supported interface and compatibility commitments.
- Have the CLI and future SDK use the same core behavior and acceptance checks.
- Keep model authentication, billing, and agent orchestration in the existing agent host.

## Consequences

The first integration works across coding agents and host programming languages without requiring a custom SDK integration. CLI process overhead and command-result handling are accepted tradeoffs for this adoption path.

Keeping behavior in the core supports a later SDK without maintaining a second implementation. It does not commit the project to any particular compiler language, package layout, command syntax, or SDK binding language.

The initial CLI should expose only operations the core actually supports. It must report unsupported behavior clearly. Neither the CLI nor the SDK exists yet.

## Validation

The roadmap, architecture, usage examples, and agent guidance must agree on this priority while keeping unimplemented features labeled.

When implementing the CLI, test that its supported operations match the core's behavior, including failures, and provide a repeatable terminal workflow. A future SDK must pass equivalent core behavior checks before release.
