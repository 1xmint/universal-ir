# 0001: Project boundaries and development foundation

**Status:** Accepted

## Context

Universal IR starts as a design repository. Contributors need a coherent direction, reproducible checks, and a review process before building a compiler. A coding subscription or API key provides model access through another tool; this repository does not provide an agent runtime.

## Decision

- The long-term product is a shared, machine-editable program representation with checks, readable views, and target compilers.
- The first executable core will support a deliberately small subset with precise meanings and a reference interpreter.
- Existing coding agents can eventually interact with this core through an adapter. At adoption, CLI-versus-SDK priority was open; [0002](0002-cli-first.md) subsequently establishes reusable core, CLI first, SDK later.
- Model authentication, billing, and agent orchestration remain outside the core.
- Proposed behavior must be labeled. Token savings and cross-platform behavior require measurements.
- Python 3.12 or newer is used for documentation quality tooling only. This does not choose the compiler's implementation language.
- Documentation quality checks and tests run now. Compiler source trees and runtime build tooling arrive when their milestone is implemented.
- Changes to the default branch go through pull requests and passing documentation checks. The initial single-maintainer policy requires no second-person approval.
- API credentials and paid model calls are unnecessary for repository checks.

## Consequences

The repository is usable today for design and contributions. It cannot yet compile or run an application.

Small tooling dependencies and pinned GitHub Actions make checks repeatable. The maintainer still reviews semantic consistency; automated documentation checks do not prove architecture correctness.

The single-maintainer review policy avoids requiring approval from a nonexistent second maintainer. Once an independent maintainer joins, require at least one independent approval and revisit code-owner enforcement.

## Validation

The [development guide](../development.md) states the local commands and GitHub controls. Quality checks, checker tests, CI results, and the configured repository rules provide evidence for development readiness at this stage.

## Subsequent decisions

[0007](0007-local-inventory-proof.md) expands Python's use from quality tooling to a bounded read-only inventory prototype. The executable IR and compiler language remain open, and the original program-core gates still apply. Required documentation status now also gates Windows/Linux inventory tests.
