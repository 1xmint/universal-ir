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
| [0010](0010-read-only-knowledge-inspection.md) | Accepted | Read-only evidence/history inspection before authenticated knowledge recording |
| [0011](0011-explicit-host-receipts.md) | Accepted | Explicit-policy signed receipt verification before live host integration and acceptance |
| [0012](0012-pinned-harness-verification.md) | Accepted | Host-configured verification tool with authority outside model requests |
| [0013](0013-read-only-knowledge-preparation.md) | Accepted | Read-only external knowledge proposals and evidence/history previews before storage |
| [0014](0014-prepared-receipt-verification.md) | Accepted | Context-bound external candidate assertions and host-fixed review verification |

## Adding a decision

Use the next available four-digit number and a short filename. Include:

- **Status:** Proposed, Accepted, or Superseded.
- **Context:** The problem and constraints.
- **Decision:** The chosen behavior, or the proposal awaiting acceptance.
- **Consequences:** Benefits, tradeoffs, and compatibility effects.
- **Validation:** The evidence required and how it was checked.

Record an accepted decision through the pull request that adopts it. Link to any decision it supersedes and preserve earlier records. A model's recommendation is not automatically an accepted project decision.

Reusable core, CLI first, SDK later, real-development consumer journeys, and universal coherence remain accepted. Decisions 0005 and 0006 now establish existing-source authority, repository knowledge with local caches, optional shared snapshots, published-revision awareness, inventory-first scope, and conversational knowledge provenance.

The [project-coherence specification](../specs/project-coherence.md) is a completed documentation increment. Decisions 0007, 0008, and 0010 implement bounded inventory, local snapshots, and knowledge inspection; decision 0009 specifies records. These do not complete the program-format or coherence milestone. Executable IR semantics, compiler language, final encoding, deeper adapters, live authenticated user-event integration, knowledge acceptance, source application/recovery, and remote bindings still need contracts and evidence. Follow [milestone 1](../../ROADMAP.md#1-define-a-small-program-format).
