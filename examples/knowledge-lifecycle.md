# From inferred purpose to an attributable requirement

This is a specified future workflow, not a command you can run today. The [knowledge contract](../docs/specs/project-knowledge-v1.md) defines exact record meanings. Current inventory can identify and hash the files; it cannot record or authenticate these statements yet.

## First explanation

Alice's existing agent inventories a billing repository. It sees a configured product document and files for invoices, tenants, and an API. It proposes: “This project helps customers manage billing.” It cites exact file versions, scope `.`, and assumptions about externally hosted services. The origin is `ai_interpretation`, even if the wording sounds certain.

The proposed body uses logical identity `project-purpose`, category `purpose`, state `active`, scope `["."]`, explicit file/document evidence, and no predecessors. Its `input_id` hashes the specified source projection. Its record ID hashes the full statement, scope, origin, and evidence together with project identity. No guessed developer identity is present.

Persisting that revision in `.uir/knowledge/` changes the ordinary inventory snapshot. It does not change the source projection, which excludes metadata entries and explicitly tracks configuration/controls. The interpretation does not immediately become stale merely because it was saved.

## Correction in conversation

Alice says: “Our main goal is tenant isolation. Billing is the first use case; one tenant must never read another tenant's invoices.”

The agent proposes a successor to `project-purpose`, retaining the earlier revision. It also proposes a separate `tenant-isolation` requirement. A supported host must establish Alice's actual user event and exact wording or her explicit approval of any shortened wording, scope, and supersession. Each record receives approval bound to its exact ID. Approval of the purpose does not automatically approve the separate requirement.

The host-owned receipt points to the finished record ID, so there is no circular receipt/record hash. A receipt copied into a repository remains unverified until a configured binding verifies it. Today, no such binding is implemented: this example's attribution is a required future outcome. A host without it may retain a clearly labeled interpretation of Alice's statement, but cannot claim a verified developer declaration.

## Source changes and a second developer

Bob adds an endpoint while Universal IR is stopped. On restart, inventory detects the addition; the purpose projection changes and the prior interpretation becomes stale. The tenant-isolation requirement remains stated intent. An agent might suspect the endpoint exposes invoices across tenants; that suspicion needs source evidence and remains an interpretation until a supported check establishes the behavior.

Alice and Bob independently refine the same purpose revision on separate checkouts. Their immutable successors can coexist after a merge. Neither timestamp wins. The working view shows both heads, their origins, evidence, and attribution. An explicit approved resolution must supersede both; an incomplete resolution remains pending. An unverified model-generated head cannot silently remove an accepted requirement.

## What the agent should receive

The overview should say which statements are interpretations, document declarations, or verified developer statements; which evidence matches current inputs; which requirements remain active; and which revisions conflict or await acceptance. Detail links should expose source, exact quoted document locations, receipt verification status, and preserved history. Unknown semantics stay visible.

Deleting a disposable graph cache must not delete these committed records. Operating offline may make a receipt unverifiable; show that attribution boundary rather than inventing approval. The future acceptance implementation must reject stale bases and preserve the previous accepted set when publication is interrupted.

This walkthrough does not demonstrate complete tenant-isolation checking, an installed host integration, or lower model-token cost. The [roadmap](../ROADMAP.md) keeps those gates separate from the completed specification increment.
