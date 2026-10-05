# Temporary browser registration and review

**Status:** Implemented development components under [decision 0017](../design/0017-temporary-browser-review.md). Protected enrollment, authenticated actor mapping, real developer/device evidence, receipt issuance, and durable acceptance remain open. No stable executable API is established.

## Registration component

`universal_ir/webauthn_registration.py` provides internal `WebAuthnRegistration`. Trusted construction fixes host/actor, RP ID, exact origin, and aware UTC clock. Reuse the assertion checker's origin/byte restrictions and optional hashed dependencies. Generate independent random user-handle and nonce bytes; hash a distinct registration domain plus a canonical request containing the fixed host/actor, RP/origin, handle, timestamps, and nonce. The host does not take the challenge or actor from a response. Options request only ES256, required verification, `none` attestation, and a two-minute timeout.

Completion accepts at most 16 KiB of strict UTF-8 JSON. Mandatory top-level fields are `id`, `rawId`, `type`, and `response`; only optional attachment and empty extension results are supported. IDs are equal canonical base64url credential bytes; type is `public-key`. Response contains exactly `clientDataJSON` and `attestationObject`. Client data is bounded to 4 KiB, parsed with duplicate/non-finite rejection, and requires the exact `webauthn.create` challenge/origin and absent or false `crossOrigin`, with no other fields.

The at-most-8-KiB attestation object is CBOR interpreted by the pinned fido2 decoder. Validate its resulting map as exactly `fmt`, `authData`, and `attStmt`; this does not define canonical CBOR transport bytes. Only `fmt: none` and an empty attestation statement are supported. Require attested credential data, no extensions/reserved flags, coherent backup flags, matching embedded credential ID, and an exact ES256/P-256 key map with valid 32-byte coordinates. The library checks challenge, origin, RP hash, and required reported presence/verification. It does **not** cryptographically authenticate those registration flags with `none` attestation. This narrow profile can reject authenticators that require other formats/extensions.

Registration is a public-key capture and context check, not hardware attestation or authenticated account enrollment. A software producer can supply a public key and flags. The later assertion proves the signing key under the selected credential; the operator must independently establish the actor and trustworthy authenticator. These limits follow the [WebAuthn registration/attestation model](https://www.w3.org/TR/webauthn-3/) and [Yubico server API](https://developers.yubico.com/python-fido2/API_Documentation/autoapi/fido2/server/index.html).

Check expiry before and after completion; lock completion in memory so only one caller succeeds. Return credential fields directly compatible with `WebAuthnReview`, request identity, `actor_authentication: not_established`, `device_attestation: not_requested`, and `persistence: none`. Malformed/context/algorithm failures raise `invalid_webauthn_registration`; a completed instance raises `registration_used`. Shared configuration, clock, backend, and expiry failures retain the assertion component's codes. A new registration request invalidates no durable credential because none is stored.

## Development host and session

`scripts/browser_review_demo.py` is a developer-operated source-run adapter. CLI flags independently select root, external candidate, preparation/project identity, host, actor, and event. Do not derive approver identity or a trusted review pin from a model's assertion of authorization. Validate actual preparation and the complete developer origin before serving. No network model or provider integration exists.

Bind `127.0.0.1` on an allocated port and use exact `http://localhost:<port>` origin/RP `localhost`. Create a 32-byte unpredictable bearer capability and print the operator's local URL with the capability in its fragment. The page immediately removes the fragment from displayed history and keeps it only in page memory, sending it in the Authorization header. It is not a persistent password; it permits this temporary session's project API operations. Treat the URL as private. Reopening/reloading requires the original capability URL; it is never saved in local storage or a cookie. Restart discards all session state.

Serve only three fixed public assets. They contain no selected-project data. API operations require IPv4 loopback, one exact Host and Origin header, and one matching bearer capability. Do not enable CORS. Reject transfer encoding, duplicate/invalid/oversized content length, non-JSON content type, and bodies over 16 KiB. Header/body sockets have three-second timeouts. Invalid framing can cause transport closure; no success follows. Errors expose a code only; request logging is disabled. This standard-library development server is not a production HTTP server or sandbox.

Use no-store responses, a restrictive content security policy with self-only script/style/connect and no framing/base/form targets, frame denial, no MIME sniffing, no referrer, and same-origin credential permissions. The frontend also refuses framed/insecure contexts. These controls reduce ordinary browser-origin attacks; they do not authenticate the operator or protect against a compromised local host/browser. No raw repository text becomes HTML or executable script.

The session lasts ten minutes under monotonic process time. Registration and assertion requests retain their separate two-minute UTC deadlines. The listener remains open until Ctrl+C, even after session expiry/completion. The synchronous HTTP server and in-memory session lock serialize calls; neither is a project filesystem lock or durable event ledger.

## Operations and presentation

| Operation | Stage and result |
| --- | --- |
| `session` | Any active stage: reconstruct the pinned actual preparation and return the complete view. No caller-selected root/actor. |
| `register/options` | New/enrolling: begin or replace the temporary registration request. Older challenges stop matching. |
| `register/complete` | Enrolling: validate registration, recheck current project, retain public credential in memory, move to enrolled. No authenticated actor claim. |
| `review/options` | Enrolled/reviewing: reconstruct and create or replace an exact `WebAuthnReview`; return complete review/options and clear UI acknowledgement. |
| `review/complete` | Reviewing: check the assertion and current preparation, return the existing read-only verification result, close the session and discard credential/ceremony objects. |
| `cancel` | Any active stage: close and discard objects even if source is stale. Nothing is accepted. |

Operations are POST paths on this development host, not public model tools. Non-completion operations accept exactly `{}`; completion bodies are the bounded credential response profiles. Unknown operations, authority fields, wrong stages, or closed sessions fail. Refreshing source never silently selects a new preparation. Restart with an independently selected new pin after an external edit.

Show project, actor/event, preparation identity, exact wording and scope, evidence/attribution status, structural transition, supersession and competing-head warning, plus a complete expandable review with evidence, affected heads, coverage gaps, and freshness. Approval is enabled only after a separate exact-review step and explicit acknowledgement. Cancelled credential prompts can be retried by restarting that step. A UI acknowledgement is not authentication or evidence that the person read everything; server checks remain decisive and cannot depend on the checkbox.

Successful completion closes this one process session; repeats fail `ceremony_finished`. This is not durable replay protection and does not change the core result's `replay: not_checked` or `human_event_authentication: not_established`. Registration baseline/counters are never persisted. A restart creates a different request and discards the old history; no accepted event is created. No Ed25519 receipt, accepted heads, effective requirement, or knowledge files are produced.

## Required evidence and remaining work

Python tests use real software signatures and loopback HTTP; Node tests execute frontend code with a small DOM and scripted credential transport. A browser visual check exercises loading/rendering and literal hostile markup. None establishes a real authenticator or human approval. Default CLI/inspection remains unchanged, and only optional verification loads cryptographic dependencies.

The [operator walkthrough](../../examples/browser-review.md) supplies reproducible commands. Before a knowledge writer, demonstrate authenticated enrollment/configuration protected from every permitted agent capability, a real browser/device/developer ceremony, signer/event policy and withdrawal, historical proof/catalog resolution, and stale/concurrent/crash-safe acceptance on Windows/Linux. Production HTTP, sessions, recovery/revocation, retention, isolation, supported devices, and cost evidence need explicit contracts. No token, latency, or agent-success savings are claimed.
