# Repository guidance

## Read first

Read README.md, ROADMAP.md, docs/architecture.md, and docs/design/README.md. For user-facing changes, read examples/using-with-ai.md and the relevant worked example.

This repository contains a proposed runtime design, examples, and executable documentation quality tooling. There is no executable compiler, runtime, or public runtime API.

## Take a bounded task

- Identify the requested outcome and its acceptance evidence before editing.
- Inspect current files, Git status, and applicable instructions. Preserve unrelated user changes.
- Keep changes focused on the authorized task. Raise unresolved product or compatibility choices rather than treating a model recommendation as accepted policy.
- Use a branch and pull request. Commit, push, create a PR, or merge only within the user's authorized scope.
- Keep provider authentication and model budgets in the existing agent host. Repository checks need no model calls.
- Do not introduce compiler scaffolding, invented executable syntax, or unsupported feature claims into conceptual examples.

## Preserve the design

- Explain ideas in simple words and define technical terms.
- Keep the README, architecture, examples, roadmap, and decision records consistent.
- Distinguish proposals, accepted decisions, implemented features, and measured results.
- Keep the program representation as the intended source of truth for generated artifacts.
- Keep checking a graph, building artifacts, and deploying software as distinct operations.
- Treat token efficiency as a hypothesis to measure across complete, correctly finished tasks.
- Record material design choices and compatibility effects in numbered design decisions.
- Update roadmap checkboxes only when their completion conditions are met.

## Validate

Use the environment-specific commands in CONTRIBUTING.md. Run the documentation checker and checker tests for repository changes. Inspect rendering when presentation changes.

For future core changes, add meaningful behavior and failure checks. Include invalid references and types, stale or rejected edits, unsupported effects, execution limits, and preservation of the previous accepted version.

Permission checks must cover trusted execution boundaries and requests that bypass the interface. A model explanation is not evidence that behavior is correct.

Add source directories and runtime tooling with executable core code. Python quality tooling does not select the compiler language. Reusable core, CLI first, SDK later is accepted in docs/design/0002-cli-first.md. Keep domain behavior in the core and the CLI as an adapter. The compiler language, final encoding, and exact CLI interfaces remain milestone 1 decisions.

## Hand off clearly

End with the outcome, changed behavior, validation commands and results, remaining limitations or decisions, and the next useful step. Name the relevant branch, commit, or PR when available.

A fresh agent should be able to continue from repository documents and recorded evidence without needing this conversation. Do not label the project production-ready or assign a perfect score without a defined scope and supporting evidence.
