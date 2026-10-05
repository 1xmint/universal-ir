# Decision 0018: deterministic task context

**Status:** Accepted through the pull request adopting this increment.

## Context

The inventory offers a project outline and file identities. An agent fixing a task still needs source locations and bounded evidence across components. Optional model extraction and ranking need a deterministic retrieval baseline before their value can be measured. Real host enrollment and knowledge acceptance have separate gates; they need not block read-only source navigation.

## Decision

Add a source-run `context` command and an internal core in `universal_ir/context.py`, with the [versioned contract](../specs/task-context-v1.md). Match literal whitespace-separated terms in paths and eligible UTF-8 source. Order by the number of distinct matched terms, then path. Describe every selection with its reasons, snapshot, and limits.

Return exact source excerpts, byte ranges, line locations, ancestor containment, the outline, guidance candidates, configuration document links, and explicit gaps. Bracket retrieval with matching full inventory captures. An optional expected snapshot rejects changed inputs during pagination or expansion. Never serve an older result after capture failure.

Keep the existing inventory extractor and identity unchanged: retrieval is a versioned view of its inputs, not a new semantic fact. It has no model calls, source writes, dependency installation, project script execution, remote service, or persistent cache. Existing knowledge files are ordinary untrusted source for this operation; their text cannot establish approved intent.

## Alternatives

- Ordinary file search remains useful and is a future comparison baseline. This increment adds inventory-qualified identity, freshness, containment, and coverage around literal retrieval; it does not claim superior relevance or cost.
- Embeddings or decision models could rank context, but need evidence of benefit and distinct provenance. They must retain the underlying facts and omissions.
- Deep language adapters could establish symbols and references. Literal matches cannot substitute for that work; syntax and runtime relationships remain unknown.

## Consequences

Agents can locate source and navigate across directories with one read-only command. Substring matching can miss aliases, synonyms, indirect references, and dynamic behavior. Common terms can rank unrelated text highly. Only the first matching-line window is excerpted; long lines and output budgets can hide a matching term.

All inventory inputs are still fully hashed twice. Eligible selected text is additionally read and checked, so narrower output does not imply less extraction work. Source excerpts are neither sanitized nor instructions to obey; the existing host controls project scope, external-model disclosure, and authorized edits. Matching captures remain an optimistic observation on a trusted local filesystem, not an atomic view or sandbox.

No public SDK, stable installer, writer, complete change-impact analysis, or efficiency claim follows. The full program-format, consumer, and model-comparison milestones stay open.

## Validation

Required Windows/Linux CI covers the real CLI, equivalent checkouts, exact UTF-8/CRLF ranges, literal matching and tie order, bounded excerpts and diagnostics, pagination pins, ignored and opaque inputs, nested-repository boundaries, scope/configuration changes, read races, unreadable inputs, and byte preservation. Documentation checks and rendering review cover the contract and working walkthrough. Future complete-agent-task comparisons must include unsuccessful retrieval and repair.
