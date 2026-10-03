# Wire a verification tool into your harness

This working integration example fixes receipt-verification authority outside model arguments. It supports an existing API harness's **verification** step; it does not connect a model provider, capture an authenticated developer conversation, or write knowledge. See the [contract](../docs/specs/harness-verification-v1.md).

## Run the fictional integration

From the tool checkout, with Python 3.12+, Git, and the optional dependencies:

~~~sh
python -m pip install --require-hashes --only-binary=:all: -r requirements-receipts.txt
python -B examples/verify_host_receipt.py
~~~

On Windows use `.venv\Scripts\python` for this repository's environment. The [script](verify_host_receipt.py) now exercises both the raw CLI and a host-configured tool against the same fictional project. It creates an ephemeral in-memory key and public transport files outside the project, then removes its scratch directory. The fixture and default knowledge attribution remain unchanged.

The `harness` report contains a valid verification, `authority_substitution: invalid_tool_request`, and `unknown_receipt: unknown_receipt`. A scripted model request attempting to add a policy pin fails before scanning; an unknown receipt cannot trigger file discovery. The report still says `approval_source: scripted_fictional_event` and `real_user_integration: not_demonstrated`. This is not evidence of a real Alice approving anything.

## Host-owned setup

Trusted initialization imports `HarnessVerifier` from `universal_ir.harness` and constructs one instance with:

| Host setting | What to fix outside model arguments |
| --- | --- |
| `root`, `project_id` | One selected checkout and its independently selected project identity. |
| `policy_path`, `policy_id` | External public policy file and independently trusted exact policy digest. |
| `receipt_paths` | A dictionary mapping permitted receipt IDs to external public proof files. It is copied at construction. |
| `clock` | Optional trusted aware-UTC clock; otherwise the host process clock. |

The host registers `tool_definition()` with its model provider after translating the provider-neutral envelope if needed, and maps `uir_verify_receipt` to this instance's `handle`. Pass the tool's raw JSON argument bytes to the handler. The model can request only `record_id` and `receipt_id`; the host checks `status`, then the nested verification result. Existing inventory/knowledge commands remain separate read-only tools.

Treat the result as an assertion verified under the named host policy, with acceptance and replay tracking explicitly absent. A policy refresh requires trusted reconfiguration of the pin. Do not use the receipt registry as an approval-event ledger or turn a successful result into a source write.

## Isolation and next step

Protect host configuration and process capabilities from the model's other tools. This wrapper does not restrict an existing coding agent's shell or filesystem permissions. If an agent can overwrite trusted settings, read a future signing key, or choose another policy and call that authoritative, the integration has no protected approval boundary. Keeping paths outside the repository or running a separate process is insufficient by itself.

The next human-event adapter must identify an actual developer action and bind approval to the complete candidate wording, scope, and transition. Then implement and test event consumption, stale/head checks, serialization, crash recovery, and accepted-state derivation before recording requirements. This integration removes model-controlled verification settings from one tool; those remaining [writer gates](../docs/specs/knowledge-acceptance-draft.md) are still open.
