# 0004: Universal foundation and coherent project views

**Status:** Accepted

**Accepted:** September 30, 2026

## Context

The maintainer reaffirmed the original ambition: one shared language for agents to understand, build, and change any kind of software. The foundation must accommodate complex systems with nested structure and relationships across that structure, rather than becoming a tool for one application stack.

The maintainer also requested a living project view that detects manual or agent changes, including changes made while Universal IR is stopped. A cached map must not silently become an authority over newer source.

## Decision

- Aim for a universal, extensible foundation across languages, frameworks, runtimes, and software domains. Actual support grows through bounded adapters, extensions, and evidence.
- Connect declared purpose, implementation structure, supported behavior, and validation evidence in a shared representation. Keep their origins and authority distinguishable.
- Represent containment and cross-cutting relationships as a graph. Offer tree views, system overviews, and task-focused detail over that graph.
- Define agent coherence as fast orientation, access to relevant detail, explicit unknowns, and traceability to current evidence. Do not promise that every detail fits in one model context or that arbitrary runtime behavior is completely understood.
- Require visible freshness, detection of external edits, and reconciliation after stopped operation before presenting a view as current or accepting a dependent edit.
- Preserve reusable core, CLI first, SDK later, and the eventual graph-managed compilation path. The existing host continues to own model access and orchestration.
- Prove the foundation with a narrow, deeply supported workflow before claiming broader compatibility or better performance.

## Consequences

This extends [0003](0003-real-development-workflows.md) without replacing its consumer journeys. A universal foundation and a narrow first demonstration serve different purposes and can coexist.

The accepted direction is a product requirement. [Coherent project views](../coherence.md), [existing-source adoption](../existing-repositories.md), and the [complex-project walkthrough](../../examples/complex-project.md) propose mechanisms and acceptance scenarios; they are not implemented contracts.

Existing source, generated artifacts, declared intent, and observed runtime state need explicit ownership rules. Calling a project view authoritative for agent navigation does not make its cached facts newer than the inputs they describe. A partial source index is not a complete executable program.

The proposed initial existing-source policy keeps source authoritative and derives a rebuildable graph. That technical policy, adapter selection, refresh algorithms, edit application protocol, encoding, and exact CLI interfaces still require milestone 1 specifications. This decision does not choose TypeScript as the first adoption adapter or accept a model recommendation as an implementation contract.

## Validation

Documentation must explain nested and cross-cutting structure, different kinds of state, pause/resume reconciliation, unknowns, and the distinction between accepted goals and proposed mechanisms.

Future implementation must demonstrate external-edit detection, stale-edit rejection, preservation of unrelated code, traceable views, and bounded support on a real existing project. Measure initial discovery, restart, refresh, context size, task success, and whole-task costs. Do not mark those demonstrations complete from documentation alone.

## Subsequent decisions

[0005](0005-portable-project-state.md) resolves the existing-source authority and storage questions that were open when this direction was accepted. It establishes inventory across languages as the first coherence proof, with deeper semantic support following later. [0006](0006-conversational-knowledge.md) establishes AI prefill and attributable conversation-derived knowledge. Detailed executable interfaces and source application guarantees remain later contracts.
