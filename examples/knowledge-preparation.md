# Review a proposal without storing it

The [preparation command](../docs/specs/knowledge-preparation-v1.md) reviews an external knowledge candidate against current source and stored history. It does not approve the proposal, withdraw an existing requirement, or write to your project.

## Run the fictional example

From the tool checkout, with Python 3.12+ and Git:

~~~sh
python -B examples/prepare_knowledge.py
~~~

On Windows use `.venv\Scripts\python` for this repository's environment. No crypto library, model provider, or API key is needed. The [script](prepare_knowledge.py) reads the existing fictional retention-rule fork, proposes a 60-day rule superseding both included heads, and places the complete candidate only in its own external temporary directory. It calls the real CLI with the observed project snapshot and deletes that scratch directory afterwards.

The report shows the exact proposed text, assumptions, references, and candidate identity; included heads before and after the virtual proposal; support/projection checks; and explicit absence of approval and acceptance. The preview has one structural head, while ordinary project knowledge still contains the original competing heads. The proposal remains an AI interpretation. A matching README fingerprint does not prove that 60 days is the developer's intended rule.

## Use it in your own project

An agent can prepare a complete record using the [record schema](../docs/specs/project-knowledge-v1.md) and save its draft in an authorized external location. Then run:

~~~sh
python -B -m universal_ir prepare-knowledge /path/to/project /outside/project/candidate.json
~~~

Require a known inventory base with `--expected-snapshot` when a host needs to prevent review against a changed project. A mismatched base fails with `stale_snapshot`; refresh the current source/history and review again. Changing wording, scope, assumptions, or supersession changes the record/preparation identities. External draft creation is the agent/host's separately authorized action; this command reads it and never enrolls it into the store.

Inspect coverage, support, proposed transition, and exact origin independently. Unavailable evidence is unresolved; a future scope can be explicit without fabricated supporting files. A pending withdrawal or fork resolution cannot remove earlier intent through this preview. An identical already-stored record is labeled rather than written again.

## Future approval handoff

A host can use this preview to present an exact candidate before approval. Its authenticated developer channel must bind the eventual action to the full record and transition, and acceptance must recheck freshness and actual accepted heads. The current receipt CLI still selects included records; it does not verify an external candidate or consume an approval event. The [host-configured verifier](harness-verification.md) does not add a signer or human authentication.

This is the preparation step in the [acceptance draft](../docs/specs/knowledge-acceptance-draft.md), not an implemented transaction or writer. It makes a proposal reviewable while preserving the project's present state.
