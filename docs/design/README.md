# Design decisions

Keep important choices here so a new contributor or agent can find the reasons without reconstructing an old conversation.

## Decision index

| Record | Status | Subject |
| --- | --- | --- |
| [0001](0001-foundation.md) | Accepted | Project boundaries and development foundation |
| [0002](0002-cli-first.md) | Accepted | Reusable core, CLI first, SDK later |
| [0003](0003-real-development-workflows.md) | Accepted | Real development workflows for product users |
| [0004](0004-universal-coherence.md) | Accepted | Universal foundation, connected views, and freshness goals |
| [0005](0005-portable-project-state.md) | Accepted | Local project state, reusable snapshots, and published collaboration |
| [0006](0006-conversational-knowledge.md) | Accepted | AI-prefilled, attributable conversational project knowledge |
| [0007](0007-local-inventory-proof.md) | Accepted | Read-only Python inventory, provisional CLI, and explicit observation boundaries |
| [0008](0008-verified-local-snapshots.md) | Accepted | Optional external local snapshots, fresh verification, and recoverable publication |
| [0009](0009-knowledge-and-cost-gates.md) | Accepted | Knowledge record/evidence contracts, host verification gates, and measured local costs |

## Adding a decision

Use the next available four-digit number and a short filename. Include:

- **Status:** Proposed, Accepted, or Superseded.
- **Context:** The problem and constraints.
- **Decision:** The chosen behavior, or the proposal awaiting acceptance.
- **Consequences:** Benefits, tradeoffs, and compatibility effects.
- **Validation:** The evidence required and how it was checked.

Record an accepted decision through the pull request that adopts it. Link to any decision it supersedes and preserve earlier records. A model's recommendation is not automatically an accepted project decision.

Reusable core, CLI first, SDK later, real-development consumer journeys, and universal coherence remain accepted. Decisions 0005 and 0006 now establish existing-source authority, repository knowledge with local caches, optional shared snapshots, published-revision awareness, inventory-first scope, and conversational knowledge provenance.

The [project-coherence specification](../specs/project-coherence.md) is a completed documentation increment. Decision 0007 and its [version-1 contract](../specs/local-inventory-v1.md) implement a bounded local inventory subset, not the full program-format or coherence milestone. Executable IR semantics, compiler language, final encoding, deeper adapters, knowledge/host schemas, source application/recovery, and remote bindings still need contracts. Follow [milestone 1](../../ROADMAP.md#1-define-a-small-program-format).
