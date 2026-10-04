# Prepared-candidate receipts, version 1

**Status:** Implemented bounded read-only verification under [decision 0014](../design/0014-prepared-receipt-verification.md). Builds on [candidate preparation](knowledge-preparation-v1.md) and the existing [pinned trust-policy contract](host-receipts-v1.md). Provisional core/CLI/internal harness interfaces; no stable SDK, signer, authenticated human channel, acceptance, or writing.

## What is bound

An exact record identity binds wording, scope, origin, evidence, supersession, and state. A preparation identity additionally binds the current full inventory snapshot, scoped source projection, and included structural heads. Those heads describe included history, not accepted intent. The verifier reconstructs actual inputs rather than accepting a model-submitted preparation report.

The caller independently fixes both expected policy and preparation identities. A digest supplied by the model is not authority. The raw CLI is a diagnostic entry point; an agent host must protect trusted settings and transport files outside the model's capabilities.

Only `developer_statement` records qualify, and payload project/record/host/actor/event identities must match the entire validated candidate. An AI interpretation cannot be promoted by signing its current record. Any explicitly reviewed developer claim is a different record and preparation; this verifier never rewrites origins.

## Exact binding and bytes

The envelope has exactly `format`, `algorithm`, `key_id`, `payload`, `signature`, and `receipt_id`. Its format is `uir.signed-preparation-receipt.v1`, algorithm `ed25519`. Key, signature, and receipt identities use the same encoding rules as the earlier receipt binding.

The payload has exactly:

| Field | Meaning |
| --- | --- |
| `format` | `uir.preparation-receipt.v1` |
| `project_id`, `record_id` | Configured project and exact candidate revision |
| `preparation_id` | Canonical SHA-256 identity of the exact reconstructed review preconditions |
| `host_id`, `actor_id`, `event_id` | Exact claimed origin identifiers; the event is not independently authenticated here |
| `action` | Only `approved`, meaning the host asserts approval of this exact preparation |
| `recorded_at` | UTC `YYYY-MM-DDTHH:MM:SSZ`, subject to the existing policy/grant/time rules |

Sign `b"Universal IR preparation receipt v1\x00"` followed by canonical JSON bytes of the envelope's `format`, `algorithm`, `key_id`, and `payload`. Canonical JSON is the existing sorted-key, ASCII-escaped, compact, finite-value encoding, with no trailing newline. Neither signature nor receipt ID is signed. The receipt ID hashes the entire envelope except `receipt_id`, including its signature. There is no encoding negotiation.

This domain and schema are distinct from `uir.signed-knowledge-receipt.v1`. Neither entry point accepts the other's profile; rehashing an envelope cannot make an old-domain signature valid. The existing `uir.host-trust.v1` policy remains unchanged: an `approved` grant authorizes verification of this host assertion in either fixed binding, subject to exact actor/key/project matching. It does not authenticate events or grant write access. Hosts requiring separate signing scopes must use separately protected keys/policies; this increment adds no profile-specific grant field.

## Source-run CLI

~~~sh
python -B -m universal_ir verify-preparation /path/to/project /outside/project/candidate.json \
  --receipt /outside/project/receipt.json --policy /outside/project/policy.json \
  --policy-id sha256:<policy-digest> --preparation-id sha256:<review-digest>
~~~

Replace placeholders with actual independently selected 64-digit lowercase digests. Quote paths with spaces. Python 3.12+, Git, and the optional pinned `requirements-receipts.txt` are required for signature verification. Preparation/default inspection still need no crypto. Candidate transport follows preparation's UTF-8/LF/final-newline rules. Receipt/policy transport uses strict UTF-8 JSON and the existing at-most-1-MiB, regular-file, external-path, no-link/junction rules. No input or project file is written.

For up to three attempts:

1. Prepare the external candidate against current project inputs. If a host fixes a project identity, check it before reading host files.
2. Read receipt and policy from the selected external paths.
3. Prepare again; require matching preparation identities and raw candidate content identities. Reread host files and require matching bytes, digests, and metadata observations.
4. Require the reconstructed preparation to equal the independent expected identity. Validate the fixed receipt profile and pinned policy; require the signed preparation identity to match too.
5. Check complete record subject, host/actor/key/action grant, issuance time, current policy window, revocation, and Ed25519 signature using the trusted clock. Return one report without changing attribution or state.

Detected changes retry; stable invalid inputs fail. This uses matching observations on a trusted filesystem, not an atomic source snapshot or hostile-filesystem isolation. A restored input between observations can escape detection; no watcher remains active after return. The operation performs multiple full scans and has no measured token or latency benefit.

## Result and failure meanings

Success is one stdout JSON object, `format: uir.preparation-receipt-verification.v1`, `status: ok`, exit 0. It retains the earlier verifier's `verified_under_pinned_policy` assertion, exact subject/receipt/key/policy IDs, issuance/verification times, and policy observation/expiry. It adds the preparation identity and full reconstructed `preparation` report, plus `human_event_authentication: not_established`.

`observation` reports current snapshot/root, raw candidate content ID, evidence status, coverage completeness, `freshness: matching_preparations_and_host_input_reads`, and `atomic: false`. The embedded preparation still labels its candidate unverified/pending and its authority as not established: the default reader is unchanged. The separate signature result does not override those reader meanings.

`acceptance: not_established` and `replay: not_checked` remain explicit. Verification may succeed with changed/unresolved evidence, future scope, competing history, or coverage gaps. Those conditions are inspectable and cannot establish readiness to accept, resolve a fork, withdraw a requirement, or write.

Dispatched failures emit only a stderr error envelope in this format, with exit 2 for stable failures and exit 3 for `unstable_inputs`. Parser failures before dispatch retain the existing inventory envelope.

| Code | Meaning and recovery |
| --- | --- |
| `stale_preparation` | Current normalized candidate or review context differs from the independently pinned preparation. Refresh actual inputs and obtain another exact review; never relabel the old assertion. |
| `receipt_subject_mismatch` | Signed preparation, project/record/origin, or eligible developer kind differs. Fix the actual host assertion and binding, not the requested digest alone. |
| `invalid_receipt` | Wrong profile/action, missing/extra fields, malformed encoding/identity, or strict JSON failure. Old-profile receipts require their original operation. |
| `host_project_mismatch` | Valid prepared project differs from trusted host selection; candidate validation may fail earlier if its project is wrong. |
| `invalid_arguments` | Malformed independently supplied identity. |
| `unstable_inputs` | Repeated source/candidate/host-file changes prevent matching observations; retry when stable. |
| Existing failures | Preserve [preparation](knowledge-preparation-v1.md#failures-and-next-gate) and [receipt](host-receipts-v1.md#failure-outcomes) meanings: invalid/unreadable transport or knowledge, wrong policy pin, invalid time, expired policy, unauthorized/revoked assertion, bad signature, or unavailable crypto. No partial success. |

Pretty-printing an otherwise identical normalized candidate does not change its review identity, but transport must be stable during one verification. Adding/deleting source, changing included configuration or history, or storing the candidate itself changes the full snapshot and invalidates the old live-review pin. That does not establish revocation of a previously accepted historical decision. Historical approval resolution needs an acceptance ledger and its own contract; neither exists here.

## Host-fixed model tool

Trusted code constructs `universal_ir.harness.PreparedReceiptVerifier` with keyword-only `root`, `project_id`, `policy_path`, `policy_id`, `reviews`, and optional `clock`. It copies a dictionary from preparation identity to an exact object containing `record_id`, `candidate_path`, `receipt_id`, and `receipt_path`. Paths become absolute; identities are validated. This registry is trusted setup, not a model enrollment operation or authenticated event registry.

Register only `handle` and translate `prepared_tool_definition()` for the chosen provider. It consumes at most 1,024 raw UTF-8 JSON bytes, with exactly one field:

~~~json
{"preparation_id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
~~~

The placeholder is not a real review. Reject duplicate/extra/missing fields, malformed JSON/UTF-8/digests, non-finite values, non-object requests, and size violations before reading files. Unknown review IDs fail with `unknown_preparation` without discovery. The model cannot choose paths, record/receipt IDs, policy/pin, project, actor/event/action, or clock.

Invoke the core using only the copied host configuration, then require returned record and receipt IDs to match the registry. A mismatch is `receipt_lookup_mismatch`. Return the existing `uir.harness-verification.v1` envelope around the new result. Model-facing errors retain named codes and generic messages; clock exceptions become `host_clock_unavailable`. Host configuration errors retain `invalid_host_configuration`, bad requests `invalid_tool_request`. No enrollment, signing, provider/network call, or write occurs; local Git ignore evaluation still invokes Git through preparation.

Preserve the [existing harness isolation limits](harness-verification-v1.md#boundary-and-host-configuration). Schemas and Python attributes are not access controls; unrestricted same-user shells can defeat trusted configuration. Protect host configuration/transport/clock/signing separately and refresh policy pins through trusted setup. Repeated requests do not consume an event.

The [fictional real-CLI and handler walkthrough](../../examples/prepared-receipts.md) proves this boundary only. A concrete authenticated user-event adapter, accepted-state preconditions, unique event consumption, serialized publication, and interrupted recovery remain gates in the [acceptance draft](knowledge-acceptance-draft.md).
