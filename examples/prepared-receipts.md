# Verify an exact external review

**Working fictional demonstration:** Verify a host-signed assertion about an external candidate and its exact project context, then reject reuse after the wording changes. This uses the implemented [prepared receipt contract](../docs/specs/prepared-receipts-v1.md). No real developer consent, accepted resolution, or writer is demonstrated.

## Run it

From the repository root, use Python 3.12+ and Git. Install optional pinned crypto into an isolated environment, following [contribution setup](../CONTRIBUTING.md#local-checks):

~~~powershell
.venv\Scripts\python -m pip install --require-hashes --only-binary=:all: -r requirements-receipts.txt
.venv\Scripts\python -B examples/prepared_receipts.py
~~~

On macOS/Linux use `.venv/bin/python` for the same commands. No provider credential, network model call, private signing key on disk, or project write is needed. The script creates an ephemeral test key in memory and temporary public transport outside the project; it removes that temporary transport on exit. This test signer is not a supported production signer.

## What the example does

The fixture contains two competing retention revisions. A scripted fictional developer claim says to retain archived tasks for 60 days and explicitly supersedes both. This claim has its own record identity and remains external. It is not an automatic promotion of the earlier AI proposal.

Preparation records the exact candidate, current full source/configuration snapshot, source projection, and included structural heads. A fictional host signs that preparation identity with matching project/record/actor/event fields. The script runs the real `verify-preparation` CLI with independently fixed policy/review pins, then invokes a host-configured handler whose sole model argument is that registered preparation identity.

Both report `verified_under_pinned_policy`. That establishes a valid assertion by the permitted test key. It does not prove the scripted event happened in a real human conversation. Embedded reader attribution stays unverified/pending; acceptance and replay remain unestablished/unchecked. Evidence and structural preview stay separate from authority.

The script changes only the external candidate to 90 days and recalculates its record identity. The old receipt and preparation pin now fail with `stale_preparation` in both CLI and handler. The fixture's snapshot, records, and competing heads remain unchanged throughout.

| Scenario | Expected outcome |
| --- | --- |
| Exact external record and context, current pinned policy, authorized signature | Verified host assertion, with no activation or write |
| Changed wording/scope/supersession or changed included source/configuration/history | Old live-review pin is stale; refresh and review again |
| New preparation pin with the old receipt | Signed subject mismatch; no approval reuse |
| Extra model fields for policy, candidate path, actor, or clock | Invalid tool request before scanning |
| Unknown preparation identity | Unknown review without filesystem discovery |
| Valid signature with unresolved evidence or coverage gaps | Conditions stay visible; acceptance remains unestablished |
| Candidate later stored in the project | Full review snapshot changes; historical acceptance needs a separate future ledger |

## Real development boundary

An existing agent can prepare evidence-linked proposals now. A host may use this provisional internal handler to verify externally supplied public assertions against trusted configuration. The raw CLI lets its caller choose settings, so a host must not copy model-selected policy or review pins into trusted setup.

A real user-facing integration must authenticate the developer channel, display exact wording/scope/transition and gaps, protect signing and policy authority from model tools, and bind the authenticated event to the reviewed preparation. A future writer must also recheck accepted heads and source under serialization, consume events once, and recover interrupted publication. Those are still [open gates](../docs/specs/knowledge-acceptance-draft.md), not features this example supplies.
