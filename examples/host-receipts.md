# Verify a fictional host receipt

This walkthrough exercises the implemented [receipt binding](../docs/specs/host-receipts-v1.md). It does not connect a coding subscription, authenticate a real conversation, or write approved knowledge.

## Run the offline demonstration

From the tool checkout with Python 3.12+ and Git:

~~~sh
python -m pip install --require-hashes --only-binary=:all: -r requirements-receipts.txt
python -B examples/verify_host_receipt.py
~~~

On Windows, use `.venv\Scripts\python` for the existing development environment. The [demonstration script](verify_host_receipt.py) reads the existing fictional project, creates an ephemeral signing key in memory, and acts as a scripted fictional host. It creates public receipt/policy transport files only in an external temporary directory and deletes its own scratch directory afterwards. It never persists the private key or changes the fixture.

Expect a report labeled `scripted_fictional_event` and `real_user_integration: not_demonstrated`. The script invokes the real CLI twice: a correctly signed receipt verifies under its pinned demo policy, while a tampered signature returns `invalid_receipt_signature`. Default `knowledge` inspection still reports the developer claims as `unverified_attribution`; the demonstration has not installed any trusted host integration or selected an approved retention rule.

## How this would fit your harness

Your existing host would authenticate a developer event and review the exact proposed statement, scope, and transition. Its protected signer would issue a receipt for that exact record ID. Public verification can use the receipt and trusted public-key policy without exposing signing secrets to the coding model.

The harness would wrap `verify-receipt`, fix the policy path/pin from trusted configuration, and expose only permitted model inputs. It must compare the returned policy identity with its own pin. Allowing a model to choose both policy and pin lets it invent a different authority; the raw CLI does not prevent that. Keeping a key outside the repository is insufficient if the model's shell can still read it.

The verifier can establish an authorized host's assertion under that policy. The actual user event, unique event consumption, source/head preconditions, and safe publication still need a concrete adapter and the [acceptance protocol](../docs/specs/knowledge-acceptance-draft.md). A valid signature alone must not trigger recording or source changes. This increment supplies a tested building block while keeping that release gate open.
