# Verified local snapshots before incremental optimization

**Status:** Accepted through the pull request adopting this increment.

**Date:** 2026-10-01

## Context

The inventory prototype reconstructs structure from current files. The next bounded increment needs persistent snapshots, recoverable storage, and honest freshness before attempting to skip extraction work. Source remains authoritative, and cache failures must not hide offline edits or block otherwise valid local operation.

## Decision

Add optional `--cache-dir` to the source-run inventory CLI, implemented in a separate reusable storage adapter, `universal_ir/cache.py`. Keep inventory/extraction in `inventory.py` and terminal handling in `__main__.py`. No model, server, runtime dependency, public SDK, or implementation-language change is introduced.

For this increment, require an explicitly selected external local cache. Store only content-addressed manifests in its reserved version-1 namespace. Committed project configuration and future durable knowledge retain the `.uir/` ownership in decisions 0005 and 0006. Repository-local cache placement is deferred: version-1 inventory includes directory membership and omissions, so creating `.uir/cache/` and its parents could change its own inputs. External storage preserves the existing extractor and identity contract, as well as target-project read-only behavior.

Always perform full local capture first. Verify cached contents against those freshly established facts, not just a cached digest, timestamp, or producer assertion. Store immutable accepted snapshots; never keep a mutable latest pointer. Local checkout attribution and observation times remain outside the artifact. Reuse of identical established facts across checkouts does not copy attribution or imply remote validation.

Publish via a unique temporary file and whole-file replacement in the same namespace. Ignore unfinished temporary files. Reconstruct missing, incompatible, or corrupt regular artifacts. Reject unsafe path types; report unavailable storage while returning a successfully verified local view. Local capture failures cannot use stale cache as fallback. Define exact outcomes in the [cache contract](../specs/local-cache-v1.md).

## Consequences

This ships disposable persistent state, restart verification, and publication recovery without changing inventory format or extractor version. The new CLI flag and optional output field are additive; existing invocations and baselines retain their meanings. This refines physical cache placement for the implemented subset of the broader coherence layout; it does not move durable project knowledge out of the repository.

Warm runs still rescan everything and may cost more than uncached runs. No speed or token savings are claimed. Source-managed artifact imports, producer trust, repository-local storage, incremental invalidation, retention, remote awareness, and live collaboration remain separate gates. Collect cold/warm costs before optimizing; preserve full local reconstruction as a correctness baseline.

## Validation

Run cache and inventory behavior/failure tests on Windows and Linux through required CI. Demonstrate separate-process cold/warm reuse, offline byte/configuration/membership changes, corrupt and incompatible artifact repair, interrupted publication, preserved prior artifacts, unavailable storage, and concurrent publication without rollback. Check documentation and GitHub rendering; publish through a checked PR. Complete only this cache increment, leaving incremental extraction and full milestones open.
