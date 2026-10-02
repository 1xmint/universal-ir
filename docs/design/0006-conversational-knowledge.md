# 0006: Evidence-linked conversational project knowledge

**Status:** Accepted

**Accepted:** September 30, 2026

## Context

The maintainer clarified that project purpose should be prefilled through scanning and AI interpretation, then refined through normal developer conversations. Onboarding should not require people to manually reconstruct every goal or repeat requirements in every session.

Observed implementation can support an interpretation of purpose, but it does not necessarily establish intended direction. Storing an inference must not make it indistinguishable from a developer's requirement or a reproduced observation.

## Decision

- Let the existing agent host interpret source-backed evidence to propose project purpose, patterns, goals, and relationships. Keep model authentication, reasoning, permissions, and budget in that host.
- Store selected project-relevant statements and decisions with scope, provenance, supporting inputs, and version or supersession links. Link existing documents and capture attributable conversation evidence without requiring a complete chat archive.
- Distinguish deterministic facts, document declarations, AI interpretations, host-attested developer statements, and observations. Origin and freshness are separate properties.
- Let normal conversation correct and refine project knowledge. A developer statement needs host-attested provenance or an explicitly approved declaration; a model's claim of approval is insufficient.
- Keep an AI paraphrase identifiable as an interpretation unless its content is established as the declaration. Hosts lacking developer provenance can still provide useful labeled hypotheses.
- Invalidate dependent interpretations and summaries when their supporting inputs change. Do not automatically call a model for unaffected records or silently rewrite declared goals to match changed code.
- Surface conflicting statements and known implementation discrepancies. Preserve history and require an explicit resolution rather than letting recency choose a requirement.
- Share durable records through ordinary project review; keep transient task drafts and unpublished work local by default.

## Consequences

An agent can begin with useful prefilled knowledge and improve it through development. The reusable core validates record structure, references, and declared origin requirements; it cannot independently prove that an interpretation captures all human intent.

Deterministic inventory can operate without paid model calls. Prefill explanations and agent use have separate token costs, including refresh and repair. Cache deletion must not lose durable declarations, while stale cached interpretations must not be presented as current.

This complements [0005](0005-portable-project-state.md). The [project-coherence specification](../specs/project-coherence.md#conversational-project-knowledge) defines required behavior and failure scenarios. Exact host provenance bindings, metadata schemas, and CLI interfaces remain later implementation contracts; no conversation adapter is implemented yet.

Subsequent [decision 0009](0009-knowledge-and-cost-gates.md) specifies record/evidence schemas, source dependencies, and attribution/history states in the [knowledge contract](../specs/project-knowledge-v1.md). Authenticated host proof, acceptance serialization/recovery, and knowledge CLI delivery remain implementation gates; the earlier open-schema statement describes this decision's original scope.

Subsequent [decision 0010](0010-read-only-knowledge-inspection.md) delivers a read-only knowledge CLI with evidence/history views. Authenticated host proof and checked recording remain gates; the inspector does not establish accepted conversational intent.

## Alternatives considered

Manual-only declarations increase setup work and miss the value of existing source and conversation. Treating inferred purpose as confirmed intent removes useful uncertainty and can silently change requirements. The chosen approach combines automatic prefill with explicit origins and ordinary conversational refinement.

## Validation

Document a billing-purpose inference refined into a developer-stated tenant-isolation requirement. Future checks must show attributable correction, retained history, stale-input handling, rejected self-promotion of inferred approval, and preservation of requirements when implementation differs.

Documentation and roadmap completion do not establish a working host integration or measured token savings.
