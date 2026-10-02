# Inspect knowledge before recording approval

**Status:** Accepted through the pull request adopting this increment.

**Date:** 2026-10-02

## Context

Decision 0009 defines knowledge revisions and attribution gates. A reader can make evidence and conflicting history useful before an authenticated host binding exists. Waiting for a writer would delay this independently testable work; treating file contents as approval would undermine the design.

## Decision

Add a read-only knowledge inspector in `universal_ir/knowledge.py`, exposed through the provisional source-run CLI. Validate immutable records against the existing knowledge schema, compute scoped input identities, trace evidence and supersession, and display competing included heads. Read only included files under existing inventory boundaries. Bracket record and quoted-document reads with matching inventory captures before publishing a view.

Keep origin, attribution, evidence, structural history, and disposition separate. No receipt verifier, writer, effective accepted-intent resolver, or conversation capture ships. Developer claims always remain unverified and pending; every claimed successor/withdrawal remains pending too. Supersession describes file-record structure and cannot establish an authorized transition. Keep all included predecessors visible through pagination/full inspection.

Report coverage gaps rather than interpreting hidden knowledge as an empty complete set. Reject malformed included records without a partial successful knowledge result. Limit each record to 1 MiB in this prototype; bound default output by record count and explicitly report omitted revisions, groups, heads, and gaps. This does not promise a fixed token budget.

## Consequences

Agents can inspect portable records, see stale support after restart, and find conflicting branches of knowledge. This adds a useful layer above file inventory without changing inventory extraction identities or selecting executable IR semantics. A static fictional fixture demonstrates the reader; it is not a supported authoring flow or actual approval evidence.

Every inspection still performs full captures. Freshness is optimistic, not atomic or a security boundary against hostile concurrent filesystem changes. History covers included records only; incomplete coverage or missing references cannot establish absence of other conflicts. Matching evidence does not prove a statement true. Historical cost results continue to describe their recorded tool hashes and do not measure the new inspector.

## Validation

Test exact identity and schema failures, UTF-8 byte quotes, hidden/missing evidence, scoped/global staleness, dependency propagation, forks with pagination, unverified withdrawal, read races, malformed-record reconciliation, equivalent checkouts, real CLI output, and target preservation. Exercise Windows links/junctions and Linux links in CI. Review the [inspection contract](../specs/knowledge-inspection-v1.md) and [working walkthrough](../../examples/knowledge-inspection.md), run all required checks and rendering review, and publish through checked PR CI. Complete only this reader increment.
