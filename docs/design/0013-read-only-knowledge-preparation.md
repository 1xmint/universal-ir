# Review knowledge before it enters the project

**Status:** Accepted through the pull request adopting this increment.

**Date:** 2026-10-03

## Context

The knowledge reader inspects stored records, and receipt verification currently selects included records. A future host must review and approve an exact proposed record before a writer stores it. Requiring a proposal to enter the active store before review would confuse pending candidates with existing project knowledge.

## Decision

Add read-only external candidate preparation using the existing versioned knowledge record schema. Validate the proposal and evaluate its evidence/history in an in-memory overlay against current included inputs. Do not change the stored reader's default behavior or write the overlay. Bracket record, quotation, and candidate reads with matching filesystem captures and transport observations; retain the existing optimistic freshness limit.

Return the exact candidate, its evidence/attribution evaluation, current included structural heads, the proposed structural result, explicit unknowns, and content-bound preparation preconditions. An optional expected inventory snapshot rejects stale review bases. A preparation identity binds the normalized candidate and observed source/history context, not human consent. Do not call structural heads accepted heads or mistake a proposed fork resolution for an approved requirement.

Expose `prepare-knowledge` through the source-run CLI and keep behavior in `universal_ir/preparation.py`. No optional crypto dependency is needed. External candidate transport must be an explicitly selected regular file outside the project without path links/junctions. Stable invalid inputs fail the whole operation; changed/unresolved evidence and incomplete coverage remain inspectable findings rather than approval.

## Consequences

Hosts can present a concrete proposal for future human review without installing it into project state. The fictional example proposes a retention-rule resolution and shows that the stored conflicting heads remain intact. Existing-source ownership, ignore rules, default attribution, and accepted-intent uncertainty are preserved.

This does not authenticate the developer, issue a receipt, implement candidate receipt verification, consume events, serialize acceptance, or write knowledge. The writer must still establish actual accepted heads and fresh preconditions under its lock. A prepared record can become stale after the observation. Matching support cannot prove the statement's meaning or developer intent. Full scans and previews have unmeasured cost; no efficiency claim is added.

## Validation

Test exact external previews, byte/schema/project validation, evidence and quotation checks, AI projections, future scope, missing references, fork/withdrawal previews, already-included proposals, ignored coverage, expected-base rejection, transport boundaries, candidate/source races, stable errors versus transient input changes, CLI failure envelopes, and project preservation. Run the fictional example, documentation checks/rendering, and required Windows/Linux CI. Mark only the preparation subset complete.
