# 0017: Exercise registration and review through a temporary browser host

**Status:** Accepted through the pull request adopting this development increment. Protected production enrollment and host authority remain open.

**Date:** 2026-10-04

## Context

The [WebAuthn assertion checker](0016-webauthn-review-assertions.md) binds a configured credential to an exact prepared review. There is no browser transport, registration checker, or protected developer channel yet. A software signature alone cannot demonstrate real user consent.

## Decision

Add a reusable internal registration checker and an ephemeral loopback browser demonstration under the [ceremony contract](../specs/browser-review-demo-v1.md). Require a host-fixed actor/origin, fresh challenge, reported presence/verification flags, and a valid ES256 credential. Request `none` attestation; do not claim device attestation, authenticated account enrollment, or proof of private-key possession from registration alone. The subsequent signed assertion checks possession under the configured credential.

The development host fixes project, candidate, independent preparation pin, actor/event, and clock before browser requests. Keep credentials and stages only in memory. Bind to IPv4 loopback on an allocated port; require exact Host/Origin and an unpredictable session capability for project API access. Reject embedded display, malformed/oversized requests, authority substitution, stale inputs, invalid stages, and completed-session reuse. Show exact statement, scope, evidence/history summary, full expandable preparation, expiry, and explicit no-write outcome. Render repository text as text.

Do not persist enrollment, sign receipts, consume durable approval events, resolve accepted intent, or write project knowledge. The existing CLI and receipt profiles remain compatible. The demo is development tooling, not a stable SDK, released approval host, or substitute for operating-system isolation.

## Alternatives and consequences

Another software-only assertion demo would not exercise browser transport and review presentation. Implementing production enrollment now would assume unresolved account authentication, protected storage, capability restrictions, credential recovery/revocation, and real developer/device evidence. A temporary host lets those transport and interface details be tested without granting write authority.

A bearer capability limits unrelated browser access but is not proof of the intended actor. An unrestricted same-user agent can read process state, alter host assets, open its own credential ceremony, or control the browser. Loopback and a separate process do not remove those capabilities. A real protected host remains a separate increment with an explicit threat model and device/developer demonstration.

CI adds a pinned Node setup action with Node 22 for frontend behavior tests; the page and host need no Node runtime in consumer operation. The optional Python requirements remain unchanged. No paid model, remote service, build framework, installer, or compiler is introduced.

## Validation

Run registration/loopback tests in `tests/test_browser_review.py`, frontend transport/state/text-rendering checks with `node --test tests/browser_review.test.cjs`, existing WebAuthn assertions, documentation checks/checker tests, and required Windows/Linux CI. Inspect the browser view and GitHub Markdown rendering. Software credentials, a mocked frontend transport, and visual browser inspection do not establish a real authenticator ceremony or host isolation. Complete only the registration/temporary browser increment; keep the authenticated host and writer gates unchecked.
