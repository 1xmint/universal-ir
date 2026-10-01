# Read-only local inventory proof

**Status:** Accepted through the pull request adopting this increment.

**Date:** 2026-10-01

## Context

The portable coherence specification needs observable local behavior before model enrichment or shared infrastructure. The first shipment should help an existing agent navigate actual files without changing them or claiming execution semantics.

## Decision

Implement a reusable Python 3.12+ inventory core and a source-run CLI adapter. Python is selected for this bounded prototype, not the eventual executable IR, compiler, or final encoding. Use the standard library and installed Git; no runtime Python dependencies or model calls are needed.

Use Git's ignore evaluator with a temporary, isolated repository outside the selected project. Apply root and nested `.gitignore` files equally to tracked and untracked paths. Do not read machine-global exclusions or the project's private `.git/info/exclude`; report this scope explicitly. Git is a required executable even for projects without version control. No project repository is initialized or modified.

Publish a versioned JSON inventory with SHA-256 content identity, containment, file classification hypotheses, document links, evidence, omissions, and bounded expandable views. Optional explicit configuration is read from `.uir/config/project.json`; metadata initialization and conversational knowledge writes are deferred. Compare an explicitly supplied previous full inventory after checking its format and content identity. Comparison is not shared-artifact trust or behavioral validation.

Each invocation rescans contents. Match two consecutive captures, including metadata observations, and retry boundedly when changes are detected. This is an optimistic filesystem observation, not an atomic snapshot against adversarial or continuously concurrent writers. Consumers needing an atomic source revision must supply an externally frozen tree. This limitation refines the observation boundary for this prototype rather than weakening the eventual coherence requirement.

Keep model enrichment and ranking replaceable. GLiNER-family extraction and Jev decisions are evaluation candidates, not dependencies or selected providers. Rank future views without discarding underlying facts; model interpretations cannot become established source facts or developer declarations.

## Consequences

The first command is useful without accounts, servers, paid calls, installation into a target project, or changes to its source. Full rereading costs remain; there are no cache, speed, token-saving, semantic-analysis, or full consumer-release claims.

Portable ignore behavior is explicit but narrower than a developer's complete Git configuration. Python and Git must be installed. Source-run invocation is provisional; distribution, stable SDK, persistent caches, host provenance, knowledge recording, and remote transport remain separate increments.

## Validation

Exercise mixed-language and non-Git fixtures, nested ignore/negation rules, boundaries, opaque files, equivalent input identities, external edits, configuration changes, bounded views, missing targets, bad baselines, missing tools, unreadable inputs, and detected changes during capture. Verify no application writes and run core tests on Windows and Linux in required CI. The [local inventory contract](../specs/local-inventory-v1.md) defines precise results and limits.
