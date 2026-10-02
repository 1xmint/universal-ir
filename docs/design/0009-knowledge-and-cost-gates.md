# Knowledge contracts and measurements before further automation

**Status:** Accepted through the pull request adopting this increment.

**Date:** 2026-10-01

## Context

Verified local inventory and disposable snapshots now work. The next step must make durable knowledge useful without allowing a model to invent approval or letting source edits rewrite requirements. Before scan optimization, collect measured costs rather than treating cache hits as performance evidence.

## Decision

Specify versioned, project-owned immutable knowledge revisions, exact source/document evidence, scoped input identities, explicit supersession/conflict handling, and independent attribution/evidence/history states. Use explicit record references for knowledge dependencies and exclude `.uir/` entries from source projections while retaining configuration/control dependencies. This prevents circular/self-invalidating knowledge identity without changing inventory extraction.

Developer approval must bind exact content and transitions through a trusted host outside model-controlled records. A durable origin or receipt payload is a claim until a supported host verifies it. Specify receipt payload requirements now, but leave authenticated transport/signature bindings and acceptance concurrency/recovery as explicit implementation gates. Do not ship a knowledge writer or mark host provenance complete in this increment.

Add a standard-library local measurement script over the existing core in fresh worker processes, comparing uncached, cold tool-cache, and warm tool-cache requests. Record all attempts, actual snapshot/cache outcomes, source versions, wall/worker CPU measurements, stored/context bytes, and missing measurements. Cold means an empty tool cache, not a flushed OS filesystem cache. Publish a small synthetic Windows baseline with raw results, without generalizing to agent performance.

## Consequences

The next agent can implement against clear record and failure meanings, but cannot mistake self-asserted identity for authenticated developer intent. Durable storage, host binding, checked acceptance, conversational capture, and knowledge views remain unimplemented. The [knowledge contract](../specs/project-knowledge-v1.md) fixes prototype design meanings, not a released API or compiler encoding.

Subsequent [decision 0010](0010-read-only-knowledge-inspection.md) implements read-only record/evidence/history inspection. The preceding status describes this decision's original increment; recording, trusted host binding, checked acceptance, and conversational capture remain unimplemented.

The [measurement tool](../../scripts/measure_inventory.py) adds developer tooling, not another product CLI operation. Inventory with freshness and cache read/validation/write are each timed as aggregates; finer separation and Git child CPU remain unmeasured. Timing and context bytes cannot establish token savings or successful software changes. Collect broader corpora and fair task-level comparisons before optimizing or claiming benefit.

## Validation

Review exact identities, evidence, correction, self-invalidation, forked history, stale candidate, and missing/invalid proof outcomes in the contract and walkthrough. Test measurement states, byte counts, source preservation, changed-input comparability, failed samples/workers, and real worker runs on Windows/Linux. Run documentation checks and rendering review, publish raw three-trial local measurements, and merge through required checked PR CI. Complete only this specification and bounded cost-baseline increment.
