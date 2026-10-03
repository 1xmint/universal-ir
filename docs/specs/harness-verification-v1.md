# Host-configured receipt tool, version 1

**Status:** Implemented bounded internal adapter under [decision 0012](../design/0012-pinned-harness-verification.md). It wraps the [receipt verifier](host-receipts-v1.md), not human authentication or knowledge acceptance. The Python interface and JSON are provisional; this is not a stable public SDK.

## Boundary and host configuration

The trusted harness constructs `universal_ir.harness.HarnessVerifier` with keyword-only `root`, `project_id`, `policy_path`, `policy_id`, `receipt_paths`, and optional `clock`. Paths are fixed as absolute paths at construction. `receipt_paths` is a copied dictionary from receipt identity to explicitly selected public receipt file. The project identity and policy digest must come from host configuration, not a repository declaration or model request that the host simply treats as trusted. The actual project configuration must match that identity during every verification.

The host registers only the bound `handle` operation with its model tool dispatcher. It does not register the constructor, object configuration, arbitrary Python evaluation, policy administration, a file-path resolver, or a signer. The operation performs no shell interpolation, subprocess command dispatch, provider call, network request, or write. A host may translate the fresh provider-neutral `tool_definition()` into its provider's tool envelope; both schema and handler require exactly the same two arguments.

This is protection against model-supplied requests through that operation. The host must enforce isolation from other model capabilities. An unrestricted same-user shell that can replace policy configuration, write trusted transport files, inspect the host process, or construct another verifier defeats the intended integration. A separate process alone does not establish isolation. Tool-schema validation and private Python attributes are not access controls. The adapter neither authenticates the host's configuration administrator nor isolates signing credentials; no signer exists here.

## Model request

`handle` consumes raw UTF-8 JSON **bytes**, at most 1,024 bytes, with exactly `record_id` and `receipt_id`. Both must be `sha256:` plus 64 lowercase hexadecimal digits. Serialize a provider's raw arguments as UTF-8; do not substitute a model-supplied configuration object. Duplicate keys, unknown fields, invalid UTF-8, non-finite values, malformed JSON, arrays, missing fields, invalid identities, and excess size fail before any project or host-file read.

~~~json
{
  "record_id": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "receipt_id": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
}
~~~

These are placeholder identities, not usable proofs. A model cannot select a root, project, policy/pin, path, key, clock, actor/event, or action. Adding any of those fields is invalid even if the requested IDs are otherwise valid. The host-selected receipt registry supplies the only path lookup. An unregistered receipt fails without filesystem discovery.

## Verification and output

For an eligible request, call the existing project receipt verifier with the fixed project/identity, policy/path/pin, selected registry path, and host clock. Default time is aware UTC from the host process. The host may inject another trusted clock at construction; a failing or invalid clock cannot produce a verified result. Clock rollback protection is not implemented.

Preserve the core's regular-file/link boundaries, external host transport placement, byte limits, signature and grant checks, policy freshness, revocation, included-record restrictions, and matching project/host-input observations. Check configured project identity before host-file reads and again on the matching final inspection. Require the verified receipt identity to equal the requested registry key: a configured filename alone does not establish content identity. No metadata or status is persisted.

Success is `{format: uir.harness-verification.v1, status: ok, result: <receipt verification result>}`. The nested result retains exact project/record/receipt/key/host/actor/event/action, policy identity, times, source observation, evidence/coverage, `acceptance: not_established`, and `replay: not_checked`. Policy observation is distinct from verification time; no live revocation or atomic source snapshot is claimed. It includes the selected project root but not host policy/receipt paths or the receipt lookup registry.

Failure is `{format: uir.harness-verification.v1, status: error, error: {code, message}}` with no `result`. Model-facing messages are deliberately generic and omit host paths and raw decoder/OS details. The host can diagnose the named code against its configuration and public inputs; this adapter creates no diagnostic log containing those inputs. Host clock exceptions are converted to failure. Programming errors outside the specified inventory/receipt failures are not turned into successful results.

| Code | Meaning and recovery |
| --- | --- |
| `invalid_host_configuration` | Constructor rejected malformed project identity, policy/registry identity, path, or clock configuration. Fix trusted setup before registering the tool. |
| `invalid_tool_request` | Request violates the exact bounded schema. Correct the two model-visible identities. |
| `unknown_receipt` | Receipt ID is absent from the host registry. The host must decide whether to register a public proof; the tool cannot enroll it. |
| `host_project_mismatch` | Current project identity differs from the host's selected project. Reconcile trusted configuration; no alternate project is selected. |
| `receipt_lookup_mismatch` | Verified bytes identify another receipt than the registry key. Repair the host lookup; do not relabel the requested proof. |
| `host_clock_unavailable`, `invalid_verification_time` | Host time failed or is not aware UTC. Repair the host clock. |
| Receipt/inventory failures | Keep the [core meanings](host-receipts-v1.md#failure-outcomes), including policy pin mismatch/expiry, revocation, bad signature, missing transport, unavailable crypto, and unstable source/inputs. No successful partial report. |

Changing policy bytes at the same path does not update a pin. A refresh or revocation requires a newly configured verifier with the independently trusted new policy identity. Changes to the original constructor dictionary cannot mutate an existing instance's copied registry. Trusted code with direct object/process access can change configuration; preventing that access is the host's responsibility.

## What remains unproved

A registered receipt is not an authenticated live user action. Verification under configured authority does not establish that a host faithfully captured conversation or obtained exact approval. Repeated reads do not consume an event. Default knowledge inspection remains unverified. No request signs a claim, grants source access, records knowledge, resolves accepted intent, or deploys anything.

The [fictional walkthrough](../../examples/harness-verification.md) demonstrates wiring and hostile requests without a paid model call. It explicitly reports real user integration as not demonstrated. A concrete authenticated human channel and the [serialized acceptance protocol](knowledge-acceptance-draft.md) remain required before a writer ships. No performance or token savings are claimed for this extra boundary or the full source scans it invokes.
