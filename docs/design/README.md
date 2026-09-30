# Design decisions

Keep important choices here so a new contributor or agent can find the reasons without reconstructing an old conversation.

## Decision index

| Record | Status | Subject |
| --- | --- | --- |
| [0001](0001-foundation.md) | Accepted | Project boundaries and development foundation |
| [0002](0002-cli-first.md) | Accepted | Reusable core, CLI first, SDK later |

## Adding a decision

Use the next available four-digit number and a short filename. Include:

- **Status:** Proposed, Accepted, or Superseded.
- **Context:** The problem and constraints.
- **Decision:** The chosen behavior, or the proposal awaiting acceptance.
- **Consequences:** Benefits, tradeoffs, and compatibility effects.
- **Validation:** The evidence required and how it was checked.

Record an accepted decision through the pull request that adopts it. Link to any decision it supersedes and preserve earlier records. A model's recommendation is not automatically an accepted project decision.

The entry-point priority is accepted: reusable core, CLI first, SDK later. The initial program format, compiler implementation language, encoding, and exact CLI interfaces are still open. Follow [milestone 1](../../ROADMAP.md#1-define-a-small-program-format).
