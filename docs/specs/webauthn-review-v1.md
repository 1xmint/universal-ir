# WebAuthn assertions for prepared knowledge reviews

**Status:** Implemented bounded internal verification component under [decision 0016](../design/0016-webauthn-review-assertions.md). Enrollment, browser ceremony, protected review host, receipt issuance, and acceptance remain unimplemented. The Python interface and JSON transports are provisional, not a public SDK or executable CLI contract.

## Purpose and trust boundary

Check an authenticator assertion against one exact external candidate review. WebAuthn binds a challenge, browser origin, relying-party identity, and authenticator data to a credential signature; its verification procedure includes user presence and, when required, user verification. See the [W3C specification](https://www.w3.org/TR/webauthn-3/) and [Yubico server documentation](https://developers.yubico.com/python-fido2/API_Documentation/autoapi/fido2/server/index.html).

This component verifies under a **host-configured credential**, not an independently authenticated enrollment. Tests use a software key that can set flags without any person. A valid signature does not prove that a trusted device verified a real developer, that the review interface displayed the correct proposal, or that the person read it. The host must establish those conditions separately.

An existing agent may propose knowledge. It must not choose the credential, actor, event, preparation pin, RP/origin, clock, or configuration administration. Trusted host construction supplies them before any assertion is accepted. No model tool exposes construction or enrollment. Python object privacy and a different process are not isolation from unrestricted agent filesystem/process access. External host storage and operating-system capability restrictions remain requirements for the future local reviewer.

## Trusted construction

`WebAuthnReview` accepts a project root, external candidate path, exact preparation identity, project/host/actor/event identifiers, RP ID, browser origin, credential object, and optional trusted UTC clock. It reconstructs the actual [preparation](knowledge-preparation-v1.md); its project and preparation must match the host's independent selection. The candidate must be a developer statement whose entire origin matches the configured host, actor, and event.

Host paths become absolute at construction, so changing the process working directory cannot redirect a later request. Existing preparation rules still reject project/candidate links, invalid files, and candidate placement inside the project; fixing a path does not confer operating-system access control.

The credential has exactly `id`, `public_key_x`, `public_key_y`, `user_handle`, and `sign_count`. Byte fields use canonical unpadded base64url. Credential IDs contain 1–1,023 bytes; user handles contain 1–64 bytes. Coordinates contain exactly 32 bytes each and must describe a valid P-256 point. The counter is a genuine integer from 0 through 2³²−1. The host copies this configuration; later mutation of the caller's dictionary cannot change it. No private key is needed by the verifier.

The initial profile fixes ES256 (ECDSA on P-256 with SHA-256). The RP ID is a lowercase DNS host name; IP addresses are unsupported. The origin must be an exact HTTPS origin or `http://localhost` with an optional non-default port. The RP must equal the origin's host; parent-domain RPs, paths, user information, explicit default ports, cross-origin assertions, and origin wildcards are unsupported. This is a narrow verifier profile, not a statement that other WebAuthn configurations are invalid. Assertion fields cannot distinguish a top-level interface from a same-origin frame; the future host must enforce its display boundary separately.

Install the optional [hashed requirements](../../requirements-webauthn.txt) in the trusted host environment. Importing this module or running default inventory does not load `fido2` or cryptography. Constructing a review requires them. This does not select the executable IR implementation language or require a Git provider or model API.

## Request and browser transport

Construction generates a new 32-byte random nonce. The `uir.webauthn-review-request.v1` request binds project, preparation, record, host/actor/event, fixed `approved` action, configuration identity, issued/expiry timestamps, and nonce. Configuration identity covers RP, origin, and the complete public credential/counter baseline. Request identity uses the existing canonical JSON SHA-256 identity. The challenge is SHA-256 of `Universal IR WebAuthn review v1` followed by a NUL byte and canonical request bytes. It cannot be selected in an assertion.

Each request lasts two minutes under the trusted host's aware UTC clock. Browser `timeout: 120000` is only a hint; verification enforces issuance ≤ current time < expiry, including after source/signature checks. A failed or invalid clock fails closed. There is no persisted rollback-resistant time source; rollback protection is a future host responsibility.

`options()` checks expiry and current preparation, then returns independent copies of `request_id`, `request`, the full prepared `review`, and WebAuthn `options`. The options require user verification and allow only the configured credential. Binary transport fields are base64url strings; a future browser adapter must convert them to byte arrays for `navigator.credentials.get` and serialize the returned assertion correctly.

The future protected interface must show the exact statement, scope, evidence status, transition, omissions, and project/review identity before initiating authentication. Credential discovery, registration and authenticated actor mapping, session authorization, cancellation, browser transport, origin security, and visual review are not supplied here. Options do not themselves establish that any interface displayed the review.

## Untrusted assertion and checks

`verify` consumes raw UTF-8 JSON bytes, at most 16 KiB. Duplicate keys, non-finite JSON values, invalid encoding, and unsupported fields fail. The top-level object requires exactly the mandatory `id`, `rawId`, `type`, and `response`, with optional `clientExtensionResults` and `authenticatorAttachment`. ID fields must both equal the configured canonical credential ID. Type is `public-key`; extension results are absent or empty; attachment is absent/null, `platform`, or `cross-platform` and is not an authority signal.

The response has exactly `clientDataJSON`, `authenticatorData`, `signature`, and nullable `userHandle`. Encoded client data is limited to 4,096 bytes and must itself be strict JSON containing `type`, `challenge`, and `origin`, with only optional `crossOrigin`. Type must be `webauthn.get`; challenge and origin must match. `crossOrigin` is absent or literally false; `topOrigin` and other fields are unsupported. A non-null handle must match the host's enrolled handle. A null handle is permitted for this named-credential flow; it never selects an actor.

Authenticator data contains exactly 37 bytes: RP hash, flags, and counter. Extensions, attested credential data, reserved flags, or trailing bytes are unsupported. Backup state requires backup eligibility. Signatures are bounded to 8–80 bytes before the library validates their encoding and signature. Yubico's fixed server state checks the expected challenge, exact origin, RP hash, configured credential and public key, signed presence, signed verification, and signature. The wrapper does not let a response lower the verification requirement.

If either the signed counter or trusted baseline is nonzero, the counter must increase. A conflict requires host investigation; it is not proof of cloning by itself. Both-zero counters are supported. Report the signed new value and baseline without updating storage. This check alone does not consume a review: even an increasing counter can be verified repeatedly against the same unchanged baseline. Event consumption and atomic counter/event persistence belong to the future host/acceptance protocol.

Reconstruct the pinned preparation before and after signature verification and compare raw candidate transport identities as well. Changed source, proposal, or included history fails; unstable captures retry up to three times. These are matching observations, not an atomic filesystem lock. A change-and-revert between observations can be invisible. Verification does not reserve the project; a writer must recheck its original accepted base under serialization.

## Result and failures

Success returns `uir.webauthn-review-verification.v1`, `status: ok`, and `verification: verified_under_host_configured_credential`, with exact request/identity, raw assertion-byte digest, current preparation, verification time, signed authenticator flags and counters, and observation limits. The assertion digest identifies transport bytes, not a canonical approval or accepted event. The request binds the canonical review; transport variation cannot change what was approved.

Authority remains explicit: `human_event_authentication: not_established`, `enrollment: host_responsibility`, `review_display: not_verified`, `acceptance: not_established`, `replay: not_checked`, and `writes: false`. No receipt is fabricated or issued. Repeated successful verification is permitted and grants no write. There are no network/model calls, target-project changes, persistent counter updates, credential revocations, or event registry operations. Host credential withdrawal requires ending the host-owned request; trusted storage/live revocation is not implemented.

| Failure code | Meaning and outcome |
| --- | --- |
| `invalid_review_configuration` | Trusted identity, origin, credential, or clock configuration is malformed. Repair host setup; do not substitute assertion-provided authority. |
| `webauthn_unavailable` | Optional verification dependencies are missing. Install the hashed requirements; no verification occurs. |
| `host_project_mismatch`, `review_subject_mismatch` | Project or developer origin differs from the host's selection. No alternate identity is chosen. |
| `stale_preparation` | Actual candidate/source/history differs from the pinned review. Prepare and review again. |
| `review_expired` | Request expired or clock precedes issuance. Obtain a new host request and assertion. |
| `host_clock_unavailable`, `invalid_verification_time` | Host time cannot be used. Fix the trusted clock. |
| `invalid_webauthn_assertion` | Schema, encoding, credential, handle, origin, challenge, flags, RP, or signature fails. No partial success. |
| `credential_counter_conflict` | Nonzero counter did not advance beyond the host baseline. Investigate before establishing a new baseline. |
| `unstable_inputs` or preparation failures | Current inputs cannot be coherently reconstructed. Preserve files and retry/reconcile; never serve old approval as current. |

## Demonstration and remaining gates

The [working software-credential demonstration](../../examples/webauthn-review.md) exercises real signatures and stale-source rejection. It demonstrates neither a browser nor a person. Required Windows/Linux tests cover hostile assertions, trusted configuration, expiry during verification, source/transport races, counters, optional imports, and preservation.

The next host increment must protect registration/configuration from the coding agent, display an exact review in a real browser, and demonstrate a real developer/authenticator assertion. Then specify how authenticated events become context-bound receipts, are withdrawn/revoked, and are consumed under the [acceptance contract](knowledge-acceptance-model.md). Historical proof/catalog resolution, serialized filesystem publication, crash recovery, and effective-intent reading remain gates before a knowledge writer. No performance, whole-task correctness, or token-saving result is claimed.
