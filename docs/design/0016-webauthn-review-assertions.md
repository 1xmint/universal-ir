# 0016: Check WebAuthn assertions for exact knowledge reviews

**Status:** Accepted through the pull request adopting this bounded component. A complete local review host remains a candidate integration.

**Date:** 2026-10-04

## Context

Context-bound host receipts and the abstract acceptance model are available. Neither connects approval to a real developer channel. An unrestricted coding agent can manufacture an approval flag or sign with a key it controls. The next host needs protected enrollment, review display, configuration, and authenticated events before knowledge writing is allowed.

A separate local review host is the first integration direction to explore. Its assertion checker can be implemented and tested independently while enrollment, interface, isolation, and durable acceptance remain open.

## Decision

Add an optional internal [WebAuthn review component](../specs/webauthn-review-v1.md) in `universal_ir/webauthn_review.py`. Trusted host construction fixes project, candidate, preparation identity, actor/event, RP (the relying party), exact browser origin, one credential, counter baseline, and clock. The component generates a fresh random nonce and a two-minute review challenge binding the exact preparation and host configuration.

Use the pinned Yubico `fido2` server verifier for the cryptographic assertion checks. Require signed user-presence and user-verification flags. Limit this initial profile to P-256/ES256 credentials, one named credential, same-origin assertions, and no extensions. Keep parsing bounded and strict, check current preparation before and after verification, and reject stale context or expired requests. Do not negotiate authority from assertion fields. These checks cannot distinguish a top-level interface from a same-origin frame; the future host must enforce its display boundary.

Return a read-only verification result. Do not enroll credentials, supply a browser/server, issue Ed25519 host receipts, update counters, consume events, or accept records. The two existing receipt profiles, CLI, default attribution, and reader remain unchanged. This internal browser-host component does not establish a stable SDK or supersede CLI-first product delivery.

## Alternatives and consequences

A CLI yes/no response is easy to script from an agent shell and does not independently authenticate a person. Git-provider review could be another host binding, but would couple this first component to a provider and still need exact-review and actor mapping. Neither is ruled out as a later adapter.

WebAuthn supplies a standard signed challenge mechanism with authenticator flags. Trustworthy enrollment and a protected review interface must establish who controls the credential and what they saw. A software key can produce valid test assertions, so this increment cannot claim a real authenticated human event. A separate process alone does not protect the host from an unrestricted same-user agent.

The optional hashed dependency adds installation and supply-chain costs to this component. Default inventory and inspection remain standard-library operations. Passkey support does not establish universal authenticator compatibility; other algorithms, extensions, embedded contexts, registration, and counter policies need separate bounded work.

## Validation

`tests/test_webauthn_review.py` uses an ephemeral software credential and real signatures. Test signature/key/subject substitution, challenge/nonce separation, RP/origin, signed presence/verification flags, strict encodings, counters/backup flags, expiry, host configuration, stale contexts, input races, lazy dependency loading, and file preservation. Required Windows/Linux CI installs `requirements-webauthn.txt` with artifact hashes after the default suites and runs the new tests and fictional demonstration.

Run documentation checks/checker tests, inspect GitHub rendering, and publish through the checked PR workflow. Complete only the assertion-checker increment. Protected registration, real browser/device/developer ceremony, host isolation, receipt issuance, event use, historical approval, physical acceptance, and writer gates remain open. No latency or token savings are claimed.
