# Fix verification authority outside model requests

**Status:** Accepted through the pull request adopting this increment.

**Date:** 2026-10-03

## Context

The raw receipt CLI lets its caller inspect a policy of its choosing. A harness that forwards arbitrary model arguments could let the model replace both policy and pin, then mistake verification under an invented authority for developer approval. The host needs a narrower callable boundary before real conversation integration.

## Decision

Add an internal provider-independent verification adapter. A trusted host constructs it with one project root/identity, one policy path/pin, a copied receipt-ID-to-path registry, and a trusted clock. Its model-visible operation accepts only record and receipt IDs, validates raw bounded JSON itself, and invokes the existing receipt core. Require the observed project and verified receipt identities to match those fixed selections. Never discover trust or receipt transport paths from the project or model arguments.

Return the core's verification result inside a versioned harness envelope. Preserve explicit absence of acceptance/replay tracking and default reader attribution. Error codes remain inspectable, while host file paths and raw decoder/OS error details are withheld from model-facing failures. The raw CLI and its policy-relative meaning remain unchanged.

Do not introduce a signer, user-event adapter, public SDK, server, model provider, or knowledge writer. The fictional host demo now exercises the narrow operation and rejects authority substitution. It still uses scripted events, not authenticated human approval.

## Consequences

Existing API harnesses have executable wiring for a verification tool without exposing trust parameters in its request schema. Policy/receipt registry changes require trusted host reconfiguration. The registry is an allowlist for read transport, not a durable approval-event or acceptance registry.

Python object privacy and tool schemas are not an operating-system sandbox. This adapter protects against requests through its registered operation; a host must separately prevent model tools from rewriting host configuration/files, executing code in the trusted process, or invoking an unrestricted alternative verifier and treating it as authoritative. Protect signing access before adding a signer. Subscription agents with unrestricted same-user shells do not gain that isolation from this adapter.

## Validation

Exercise legitimate verification and hostile model requests through the real handler, not just schema inspection: policy/root/clock/action injection, unknown receipts, malformed/duplicate/oversized JSON, changed project identity, wrong receipt lookup, tampering, missing transport, policy updates/revocation/expiry, failed clocks, current-source observation, repeat reads, and preservation. Run the fictional integration example, Windows/Linux CI, documentation checks, and rendering review. Complete only the fixed-configuration verification-tool increment; real event authentication and serialized acceptance remain gates.
