# Explicit host receipt verification, version 1

**Status:** Implemented bounded verification under [decision 0011](../design/0011-explicit-host-receipts.md). This binds signatures to [knowledge records](project-knowledge-v1.md); it supplies neither a live user-event adapter nor a knowledge writer. It is a provisional CLI/format, not a stable SDK.

## Authority and host duties

The first candidate integration is a provider-independent host/harness. A trusted caller owns the project trust policy, its expected digest, trusted clock, and signer access. The host must authenticate the actual developer channel and event; `stated` means the exact recorded text was stated, and `approved` means explicit approval of the exact proposed wording and record transition. Scope and supersession are part of the record identity. General permission to work on a project does not approve generated requirements. If scope/transition cannot be established from the event, obtain explicit approval rather than infer it.

Only the host can issue signing requests from authenticated user actions. Signing credentials and policy updates must be inaccessible to model tool execution. This repository does not create that isolation, authenticate a conversation, or supply a signing endpoint. A harness with unrestricted tools that can read signing keys, replace trust configuration, or choose another policy/pin has no protected approval boundary. External file placement alone is not protection.

A raw CLI caller may choose a policy for inspection. Its result is valid only under the displayed policy identity. A real harness must supply and check that identity from trusted configuration and prevent the model from substituting CLI policy arguments. Model-supplied keys, `approved: true`, a receipt payload without a signature, and repository-provided trust do not establish authority. A compromised or dishonest authorized host can issue false assertions; cryptography does not recover the actual conversation.

## Optional dependency

Inventory and default knowledge inspection still need only Python 3.12+ and Git. Install the optional verifier from the tool checkout:

~~~sh
python -m pip install --require-hashes --only-binary=:all: -r requirements-receipts.txt
~~~

On Windows use `.venv\Scripts\python` if using the development environment. The lock pins cryptography 50.0.2, cffi 2.1.1, and pycparser 3.0 with release artifact hashes. Hashes cover platform artifacts; CI requires binary wheels on Windows/Linux Python 3.12. Unsupported environments fail installation rather than build an unreviewed dependency implicitly. This choice does not select executable IR language/encoding. Verification follows the library's [Ed25519 interface](https://cryptography.io/en/stable/hazmat/primitives/asymmetric/ed25519/); no custom signature primitive is implemented.

## Signed envelope

The envelope has exactly `format`, `algorithm`, `key_id`, `payload`, `signature`, and `receipt_id`.

| Field | Meaning |
| --- | --- |
| `format` | `uir.signed-knowledge-receipt.v1`. |
| `algorithm` | Exactly `ed25519`; no algorithm negotiation from model input. |
| `key_id` | `sha256:` plus the SHA-256 of the raw 32-byte public key. |
| `payload` | Exact conceptual receipt fields from the knowledge contract: `format: uir.knowledge-receipt.v1`, `project_id`, `record_id`, `host_id`, `event_id`, `actor_id`, `action`, `recorded_at`. |
| `signature` | 64 signature bytes encoded as 128 lowercase hexadecimal characters. |
| `receipt_id` | Canonical SHA-256 identity of the entire envelope excluding `receipt_id`, including the signature. |

Sign the literal UTF-8 bytes `Universal IR host receipt v1` followed by one zero byte, then canonical UTF-8 JSON of exactly `{format, algorithm, key_id, payload}`. Use inventory canonical encoding: sorted keys, compact separators, unescaped Unicode, no non-finite values. The signature and receipt ID are excluded from signing bytes, avoiding a hash/signature cycle. Envelope key identity and algorithm are signed too. There is no embedded trusted public key.

Identifiers are nonempty UTF-8 strings. Digests use `sha256:` plus 64 lowercase hexadecimal digits. Timestamps use exactly `YYYY-MM-DDTHH:MM:SSZ`, valid UTC calendar times with whole-second precision. Unknown fields/versions, duplicate JSON keys, invalid UTF-8, non-finite values, and invalid encoding fail. Optional CLI inputs are limited to 1 MiB each. The record itself must pass the existing full record validator; a supplied digest string alone is insufficient.

This binding verifies `developer_statement` records only. Payload project/record IDs must match the record and policy; host/actor/event IDs must match the claimed origin exactly. A trusted host approving an interpretation must produce a separately attributed developer revision with a new record ID. A receipt does not silently change origin or body.

## Caller-owned trust policy

The policy has exactly `format: uir.host-trust.v1`, `project_id`, `observed_at`, `valid_until`, `grants`, and `revoked_receipts`. Its identity is canonical SHA-256 of the complete policy. The trusted caller pins this independently; the receipt cannot provide its own authority.

Each grant has exactly `host_id`, `actor_id`, `key_id`, `public_key`, `actions`, `not_before`, and `not_after`. `public_key` is 32 raw bytes in lowercase hexadecimal and must match `key_id`. Actions are a nonempty unique list containing `stated` and/or `approved`. One grant per host/actor/key tuple is allowed. Issue intervals must be nonempty. Grants authorize assertions for this specific project, not source writes or arbitrary user roles.

`revoked_receipts` is a unique list of receipt IDs. To revoke all assertions from a key, remove its grant in the new policy. Rotate to a new public key by issuing a new grant; retain old grants only when historical assertions should remain trusted. Key windows constrain issuance: `not_before <= recorded_at < not_after`. They need not include today's verification time, so explicitly retained historical keys can verify old receipts. Future-dated receipts are rejected.

Policy freshness requires `observed_at <= now < valid_until` under the trusted UTC clock. A policy is not a live revocation feed. Offline verification cannot discover revocations after `observed_at`; the caller chooses a refresh/expiry policy appropriate to its host. A new policy has a new pin and must be distributed through the trusted host, not accepted from project contents or model output. Clock compromise or rollback is outside this verifier's protection.

## CLI and observation

~~~sh
python -B -m universal_ir verify-receipt /path/to/project sha256:<record-digest> --receipt /outside/project/receipt.json --policy /outside/project/trust.json --policy-id sha256:<trusted-policy-digest>
~~~

Angle-bracket placeholders are explanatory; replace them with actual lowercase digests. Quote paths containing spaces. Both host inputs must be existing regular files outside the resolved selected project, without links/junctions in their path components. No trust is discovered in `.uir/`, no private key is read, and no file is written. These external inputs are explicitly selected transport inputs, not a widening of source inventory's ignore rules.

Up to three attempts bracket host input reads with full knowledge inspections. Require matching project snapshot IDs and matching host bytes/digests/metadata before verification. Internal inspections retain their own capture checks. A detected edit retries; sustained changes return `unstable_inputs`. Stable malformed JSON fails without a successful partial report. This is an optimistic observation on a trusted filesystem, not an atomic snapshot or sandbox against hostile path replacement. It still fully scans source and does not establish faster startup.

Success is one JSON object on stdout, format `uir.receipt-verification.v1`, status `ok`, exit 0. It names receipt/record/project/key/host/actor/event/action, recording and verification times, `trust_policy_id`, and `verification: verified_under_pinned_policy`. It also states `acceptance: not_established` and `replay: not_checked`. `observation` identifies source snapshot/root, record evidence status, coverage completeness, optimistic freshness, and `atomic: false`. A valid host assertion can coexist with changed source support; it does not prove implementation compliance or accept a stale edit.

`trust_observation` separately exposes policy `observed_at`, `valid_until`, and `live_revocation: false`. Verification time does not imply that later remote revocations were observed.

Default `knowledge` views remain unchanged and unverified. Verification does not save a status, resolve a conflict, withdraw a requirement, consume an event, or turn a structural head into accepted intent. Repeating an identical verification is a read, not another approval action. Contradictory signed reuse of an event cannot be detected from one receipt: the future host/writer must maintain a durable event registry and reject reuse for a different record/action. That gate is explicit in the [acceptance draft](knowledge-acceptance-draft.md).

## Failure outcomes

Errors use the receipt format on stderr after command dispatch, with `status: error`, `error.code`, and `error.message`; no successful stdout. Parser errors before dispatch retain the existing inventory envelope. Exit 2 covers invalid/unavailable inputs and failed verification; exit 3 is `unstable_inputs`.

| Code | Meaning |
| --- | --- |
| `invalid_receipt`, `invalid_trust_policy` | Unsupported shape/encoding/version, duplicate keys, malformed times, identity/key mismatch, or invalid intervals. |
| `trust_policy_mismatch` | Supplied policy differs from the independently pinned digest. |
| `trust_policy_not_current` | Policy expired or not yet current; refresh through trusted host configuration. |
| `receipt_subject_mismatch` | Receipt does not cover the exact developer record/project/origin. |
| `receipt_not_authorized` | Host/actor/key/action lacks a current policy grant. |
| `receipt_revoked` | Pinned policy explicitly revokes this receipt. |
| `receipt_time_not_authorized` | Receipt is future-dated or outside key issuance bounds. |
| `invalid_receipt_signature` | Signature fails under the authorized public key. |
| `receipt_verifier_unavailable` | Optional library/backend absent or Ed25519 unavailable; no verified result. |
| `invalid_host_input`, `invalid_arguments` | Unsafe, oversized, missing/nonregular host path or invalid CLI identifiers. |
| Existing knowledge/inventory errors | Keep their meanings; ignored/missing records cannot gain verified attribution through this operation. |

No error replaces source, stored intent, or the chosen trust policy. The [fictional walkthrough](../../examples/host-receipts.md) and `tests/test_receipts.py` demonstrate this bounded contract. Real user-event authentication, replay consumption, and serialized stale/concurrent/interrupted acceptance remain unimplemented gates.
