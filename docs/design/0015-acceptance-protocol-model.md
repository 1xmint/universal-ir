# 0015: Test acceptance rules before choosing a writer

**Status:** Accepted through the pull request adopting this increment.

**Date:** 2026-10-04

## Context

External [candidate preparation](0013-read-only-knowledge-preparation.md) and [context-bound receipt verification](0014-prepared-receipt-verification.md) are available. The acceptance draft still leaves publication identity, replay, recovery, and imported-history behavior underspecified. A live user-event adapter and real storage/lock primitives are not implemented.

We can test logical transaction rules independently of those choices. A simulation must not become a shortcut around the real authentication, freshness, and durability gates.

## Decision

Add an [acceptance protocol model contract](../specs/knowledge-acceptance-model.md) and a small standard-library model in `scripts/acceptance_model.py`. It runs on symbolic identities and explicit test conditions in memory. Its default conditions reject new work. It performs no project scan, cryptographic verification, host authentication, lock acquisition, or filesystem publication.

Distinguish staged artifacts, published decisions, and historical acknowledgements. Derive simulated heads and event use from complete published decisions, preserve competing imported heads, and reject incomplete commits or conflicting event use without choosing a partial winner. Recheck modeled prerequisites at publication. Retrying an exact published operation acknowledges history without granting new approval.

Specify the information a future durable decision must bind and the obligations its reader/writer must demonstrate. Keep real host selection, protected signing, durable encoding, storage layout, atomicity, lock/recovery implementation, and historical proof verification open. The existing knowledge reader, preparation, receipt profiles, and harness tools remain unchanged.

## Alternatives and consequences

Implementing a writer directly from the prose draft would combine unresolved authority, transaction, and platform decisions in one change. A model exposes logical mistakes while those boundaries are still reviewable.

Only prose would leave interruption and merged-history rules harder to compare consistently. Executable scenarios provide repeatable evidence under named assumptions; they do not prove those assumptions or exhaust every interleaving.

The model is development tooling, outside the runtime package. Its boolean conditions are test oracles, never trusted model arguments. Its IDs and serialization are not a durable acceptance format or public API. Shipping production recording still requires a real authenticated host and Windows/Linux stale/concurrent/interrupted filesystem evidence.

## Validation

`tests/test_acceptance_model.py` covers inert staging, both staging orders and every prepublication prefix, response-loss retry, changed source/prerequisites, serialized contenders, event conflicts after restart/import, pending and committed withdrawal, fork resolution, malformed/incomplete history, immutable artifacts, and the real demonstration script. Required Windows/Linux CI runs the model suite before optional crypto installation.

Run documentation checks/checker tests, inspect GitHub Markdown rendering, and publish through the checked PR workflow. Complete only this logical-contract/model increment. The live-host, physical acceptance, full coherence, and program-format gates stay open.
