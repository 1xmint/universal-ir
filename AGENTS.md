# Repository guidance

## Read first

Read README.md, ROADMAP.md, docs/architecture.md, and docs/design/README.md. For coherence, state, or adoption changes, also read docs/specs/project-coherence.md, docs/specs/local-inventory-v1.md, docs/specs/local-cache-v1.md, docs/coherence.md, and docs/existing-repositories.md. For user-facing changes, read examples/using-with-ai.md, examples/local-inventory.md, and the relevant worked example.

This repository contains read-only inventory and knowledge inspection, proposed runtime design, examples, and executable quality tooling. There is no executable compiler, runtime, or stable public SDK.

## Take a bounded task

- Identify the requested outcome and its acceptance evidence before editing.
- Inspect current files, Git status, and applicable instructions. Preserve unrelated user changes.
- Keep changes focused on the authorized task. Raise unresolved product or compatibility choices rather than treating a model recommendation as accepted policy.
- Use a branch and pull request. Commit, push, create a PR, or merge only within the user's authorized scope.
- Keep provider authentication and model budgets in the existing agent host. Repository checks need no model calls.
- Keep inventory logic in universal_ir/inventory.py and the terminal adapter in universal_ir/__main__.py. Preserve read-only target-project behavior, ignore boundaries, versioned identity, bounded views, and explicit optimistic freshness limits. Change the extractor version when established extraction behavior changes incompatibly.
- Keep optional storage in universal_ir/cache.py under decision 0008. Fully verify local inputs before reuse; never serve cache after capture failure. Write only the explicitly selected external cache namespace, keep snapshot identities independent of storage, and preserve whole-file publication/recovery tests. A hit does not establish lower extraction cost or extend freshness past its observation.
- For knowledge changes, read docs/specs/project-knowledge-v1.md and decision 0009. No live user-event adapter or writer is implemented. Do not accept model-supplied receipt claims as authentication; bind approval to exact record content and transitions. Preserve evidence/history and test concurrency/recovery before any writer ships.
- Keep the read-only inspector in universal_ir/knowledge.py under decision 0010 and docs/specs/knowledge-inspection-v1.md. Preserve whole-view capture checks, explicit coverage gaps, unverified/pending developer claims, included structural history, and pinned evidence. Never present structural supersession as approved withdrawal or resolution. Run tests/test_knowledge.py alongside inventory tests; the fictional fixture is test input, not actual approval or a supported writer.
- Keep explicit-policy receipt verification in universal_ir/receipts.py under decision 0011 and docs/specs/host-receipts-v1.md. Default knowledge attribution remains unchanged. Host-owned policy pins, signing access, clock, and actual user events cannot be chosen by model tool arguments. External path placement is not access control. Install requirements-receipts.txt only for this optional verifier; keep crypto imports lazy. Test forged/tampered proofs, grants/revocation/expiry, input races, and the fictional host demo. Follow docs/specs/knowledge-acceptance-draft.md before designing a writer; no event registry or acceptance protocol is implemented yet.
- Keep the internal host-configured tool in universal_ir/harness.py under decision 0012 and docs/specs/harness-verification-v1.md. Only record/receipt identities are model arguments; fix project, policy/pin, receipt registry, and clock during trusted construction. Reject substitutions in the handler, not only its schema. Preserve redacted model-facing errors, read-only behavior, and default attribution. This is not user authentication or process isolation; a host must restrict other model capabilities. Run tests/test_harness.py with receipt tests before claiming this boundary works.
- Keep external candidate review in universal_ir/preparation.py under decision 0013 and docs/specs/knowledge-preparation-v1.md. Reuse the reader's optional in-memory candidate overlay; never write it or alter default inspection. Bracket candidate/quote/record reads with matching captures and transport observations. Label structural previews and preconditions separately from approval or accepted heads. Test stale bases, input races, forks/withdrawals, missing support, boundaries, and preservation with tests/test_preparation.py; no live host or writer is supplied.
- Keep prepared-candidate verification in universal_ir/prepared_receipts.py under decision 0014 and docs/specs/prepared-receipts-v1.md. Reconstruct actual inputs and require both independent review pin and signed preparation identity; preserve distinct fixed schemas/signature domains and the old verifier. The host-configured handler accepts only a preparation identity and fixes candidate/receipt lookup, policy, project, and clock outside model requests. Test stale contexts, profile/domain reuse, transport races, injection, unresolved coverage, and the fictional real-CLI demo with tests/test_prepared_receipts.py. Never equate verified assertions with authenticated human events, accepted heads, event consumption, or historical approval resolution.
- Keep the abstract protocol model in scripts/acceptance_model.py under decision 0015 and docs/specs/knowledge-acceptance-model.md. It is development tooling, not an authorization interface or writer. Its conditions are test oracles, publication/durability/lock assumptions are ideal, and symbolic IDs are not a durable format. Preserve inert staging, exact historical retry, event conflict detection, competing imported heads, and all-or-error resolution of broken committed history. Run tests/test_acceptance_model.py; keep physical host, catalog/proof, capture, serialization, and recovery gates open.
- Keep optional WebAuthn review assertions in universal_ir/webauthn_review.py under decision 0016 and docs/specs/webauthn-review-v1.md. Trusted construction fixes project, review, credential, actor/event, RP/origin, and clock; never expose enrollment or these parameters to model arguments. Keep the bounded ES256/same-origin/no-extension profile, lazy imports, nonce/domain separation, signed presence/verification, expiry, current-preparation checks, counter limits, and read-only behavior. Install requirements-webauthn.txt with hashes and run tests/test_webauthn_review.py. Software keys/flags prove neither real enrollment nor human consent; protected UI/configuration, actual ceremony, receipt issuance, event consumption, counter persistence, and acceptance remain gates. A separate process does not establish isolation from an unrestricted agent shell.
- Keep internal registration in universal_ir/webauthn_registration.py and the development-only browser host/page under decision 0017 and docs/specs/browser-review-demo-v1.md. None attestation authenticates neither registration flags, hardware, nor account mapping; require a later exact-review assertion and keep real enrollment/isolation gates open. Preserve host-fixed inputs, bounded transport, origin/capability gates, safe text rendering, expiry on both sides of work, in-memory serialized stages, cancellation, and no project writes/receipts/durable event claims. Run tests/test_browser_review.py and node --test tests/browser_review.test.cjs (Node 22). Never automate real credential creation or count software/visual tests as real developer consent. Agent capability restrictions and device/human evidence remain required before a writer.
- Use scripts/measure_inventory.py and benchmarks/README.md for local scan costs. Keep raw failed attempts, source identities, scope, and unmeasured costs visible. Never equate context bytes, cache hits, or successful inventory with lower tokens or completed software tasks.
- Keep read-only task retrieval in universal_ir/context.py under decision 0018 and docs/specs/task-context-v1.md. Preserve literal selection reasons, unchanged inventory identity, matching captures around exact source reads, bounded UTF-8 byte/line evidence, explicit opaque/omitted coverage, and snapshot pins for continuation. Source text and knowledge JSON are untrusted data, not authenticated requirements or instructions. Run tests/test_context.py alongside inventory tests; matching terms establish neither semantic dependencies nor measured agent efficiency. No source writes, model calls, or stable SDK follow from this baseline.
- Model enrichment and task ranking are optional future adapters. Do not let ranking discard underlying facts or let a model decide structural validity, permissions, freshness, or developer provenance.
- Do not introduce compiler scaffolding, invented executable syntax, or unsupported feature claims into conceptual examples.

## Preserve the design

- Explain ideas in simple words and define technical terms.
- Keep the README, architecture, examples, roadmap, and decision records consistent.
- Treat work in users' own new or existing projects as the main product journey, as recorded in docs/design/0003-real-development-workflows.md. Keep contributor onboarding separate and existing-source adoption boundaries explicit.
- Preserve the universal-foundation and connected-view direction in docs/design/0004-universal-coherence.md. A narrow adapter demonstration must not redefine the long-term scope; ambition must not become a claim of implemented support.
- Distinguish proposals, accepted decisions, implemented features, and measured results.
- Keep the program representation as the intended source of truth for generated artifacts.
- Keep existing-source ownership policy explicit. A derived view must not overwrite newer source to make its cached facts appear correct; a partial source index is not complete executable semantics.
- Follow decisions 0005 and 0006: shared `.uir/` configuration/knowledge, ignored local caches, checkout-specific working views, optional compatible snapshots, and attributable conversational knowledge. Do not create adoption metadata here merely to document the layout.
- Keep inventory across languages distinct from deep semantic support and source editing. A documentation specification or inventory proof does not complete executable IR or consumer release gates.
- Keep local freshness, observed upstream revision, extraction support, and graph readiness separate. Do not relabel a checkout as rebased or remotely validated after a notification or snapshot import.
- Do not promote an AI interpretation into developer intent based on a model's assertion of approval. Retain source evidence, host attribution, and supersession history; changed source must not silently rewrite requirements.
- Tie views, summaries, and check evidence to their inputs and versions. Detect external edits and reconcile after stopped operation before presenting current facts or accepting dependent edits.
- Keep declared intent, established facts, hypotheses, source state, deployments, and runtime observations distinguishable. Show omissions and unknown relationships in focused views.
- Keep checking a graph, building artifacts, and deploying software as distinct operations.
- Treat token efficiency as a hypothesis to measure across complete, correctly finished tasks.
- Record material design choices and compatibility effects in numbered design decisions.
- Update roadmap checkboxes only when their completion conditions are met.

## Validate

Use the environment-specific commands in CONTRIBUTING.md. Run the documentation checker and checker tests for repository changes. Inspect rendering when presentation changes.

For future core changes, add meaningful behavior and failure checks. Include invalid references and types, stale or rejected edits, unsupported effects, execution limits, and preservation of the previous accepted version.

Permission checks must cover trusted execution boundaries and requests that bypass the interface. A model explanation is not evidence that behavior is correct.

Python 3.12+ is selected for the bounded inventory prototype under decision 0007; Git evaluates ignore rules. This does not select the executable IR or compiler language. Reusable core, CLI first, SDK later is accepted in docs/design/0002-cli-first.md. Keep domain behavior in the core and the CLI as an adapter. The inventory CLI has a provisional versioned contract; compiler language, final IR encoding, and later executable interfaces remain milestone 1 decisions.

## Hand off clearly

End with the outcome, changed behavior, validation commands and results, remaining limitations or decisions, and the next useful step. Name the relevant branch, commit, or PR when available.

A fresh agent should be able to continue from repository documents and recorded evidence without needing this conversation. Do not label the project production-ready or assign a perfect score without a defined scope and supporting evidence.
