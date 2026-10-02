# Verify host receipts under explicit trust

**Status:** Accepted through the pull request adopting this increment.

**Date:** 2026-10-02

## Context

The knowledge reader can distinguish claims and changed evidence, but cannot authenticate a developer statement. A provider-independent signature binding is useful to a future API harness without coupling the core to one coding subscription. Authentication of actual user events and safe acceptance are separate problems.

## Decision

Specify and implement an Ed25519 receipt binding using the maintained `cryptography` library, with pinned optional dependencies. Sign a fixed domain plus canonical binding fields. Bind the exact knowledge record ID, project, host, actor, event, action, time, and key identity. Verify against a project-specific policy whose content identity the trusted caller pins independently of model-controlled input. The policy supplies public keys, authorized actor/actions, issuance windows, revocations, and an explicit observation/expiry interval.

Expose a separate read-only `verify-receipt` CLI operation. Require explicit policy/receipt files outside the inspected project, report the policy fingerprint, and reconcile project/host inputs before publishing. No implicit repository trust, public-key discovery, signer, key-generation command, network request, or writer ships. Signature verification does not establish the user's real-world identity or that the host issued its assertion honestly. It authenticates an authorized host's assertion under the supplied policy.

Keep default knowledge inspection unchanged: developer claims remain unverified and pending. A verification report says `verified_under_pinned_policy`, `acceptance: not_established`, and `replay: not_checked`. A raw CLI caller chooses its policy; an agent harness must bind that policy and pin in trusted tool configuration rather than expose them as model-selectable arguments. Moving a file outside the project is not access control.

## Consequences

Receipt bytes can be exchanged without sharing signing secrets. Keys remain host-owned, and an old explicitly retained key can verify historical issuance. Offline verification knows revocations only through the pinned policy's observation; expired/not-yet-current policy fails closed. A signature, receipt hash, or repeated successful verification does not prove edit acceptance, current source support, or unique event consumption.

The fictional offline host demonstration exercises signatures and CLI transport with an ephemeral key. Its actor/actions are scripted, not authenticated human events. The live-host and serialized acceptance gate remains incomplete. The [acceptance protocol draft](../specs/knowledge-acceptance-draft.md) records the remaining writer requirements without shipping them.

## Validation

Test exact subject binding, forged keys, payload/domain/signature tampering, policy pin mismatch, actor/action grants, revocation, expiry, issuance/rotation, strict schemas, absent crypto, read races, ignored records, external input boundaries, source preservation, and separate default attribution. Run the fictional CLI demo, required Windows/Linux CI and documentation checks, inspect rendering, and publish through a checked PR. Complete only this receipt-verification increment.
