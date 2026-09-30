# Real development with a coding agent or API harness

These examples describe people using Universal IR in their own projects. They are planned consumer journeys, not instructions for contributing to Universal IR.

There is no installer, project setup integration, usable CLI, source index, state service, compiler, or SDK yet. The [project-coherence specification](../docs/specs/project-coherence.md) defines the first inventory and knowledge proof. Deep semantic adapters, source editing, and executable interfaces remain later work.

## Example 1: a user with a coding subscription

The user already has a coding agent that can work with local files and terminal commands. They want a short setup path, then ordinary task prompts.

The intended setup is:

1. Install the released Universal IR CLI once.
2. Select a new project location or an existing repository.
3. Initialize the supported project representation and connect it to the coding agent.
4. Keep the agent's existing subscription authentication.
5. Start prompting the agent to create, change, or fix the project.

Setup should establish project intent, supported structure, known checks, and how the agent invokes the CLI. It should provide an overview linked to expandable detail and surface unsupported code or capabilities before claiming that the project is ready. Exact setup commands and supported agent integrations do not exist yet.

### First coherence increment

The user asks:

> Map this project, explain its likely purpose and structure, show what you do not understand, and retain the project goals we establish in this conversation.

The planned first proof inventories files across languages and connects explicitly declared relationships. The existing agent can propose purpose from that evidence, with interpretations labeled and linked to their inputs. The developer can correct it through normal conversation. Host-attested statements and approved declarations remain distinct from the agent's paraphrases and hypotheses.

Shared configuration and durable knowledge travel in a committed `.uir/` area, with references to existing documents where useful. Local caches, drafts, and uncommitted work stay local by default. Discovery preserves application files and needs no paid model calls; explanation and conversation use the existing host's model and budget. There are no working setup commands yet.

The new-project generation and existing-project fixes below describe later consumer capabilities. A first inventory proof does not establish permission correctness or deliver checked source edits.

### New project

The user asks:

> Create a new repository for a project task app. Members can read and create tasks; project administrators can archive them. Set up the project and its checks, then show me how to run it.

The existing agent host handles authorized repository creation and ordinary environment operations. Universal IR would provide the supported program representation, bounded edits, checks, and target compilation.

The agent would settle requirements, build the graph, check behavior, and generate the supported application artifacts. It would report what passed, what remains unresolved, and how to run the application. The user would not need to maintain separate copies of the same program rules in repeated prompts.

See the [task application example](project-tasks.md) for the intended behavior. Repository creation, compilation, and deployment are distinct operations; the agent must stay within the user's authorized task.

### Existing project

The user opens an existing repository and asks:

> Fix the archive action for project administrators. Keep the existing framework and unrelated code. Reproduce the problem, make the smallest relevant change, and run the project's checks.

A supported adoption workflow would inspect the current project, identify relevant source and rules, and give the agent a coherent view of the task. The agent would propose a bounded change, receive check results, and repair failures before reporting completion.

The accepted [coherence contract](../docs/specs/project-coherence.md) keeps existing source authoritative and derived facts tied to current inputs. The broader [adoption proposal](../docs/existing-repositories.md) adds a future deep source adapter and checked changes. The tool must detect stale information after external edits, preserve unrelated code, and report unsupported parts.

Ownership is decided, but source application and recovery guarantees still need contracts. A partial index cannot be described as a complete executable representation. The supported source-editing subset must be demonstrated on a real change before this fix journey is advertised as working.

### Return after manual or other agent edits

The user stops using Universal IR, changes files with another editor or agent, and later reconnects it. The proposed tool would treat the persisted view as historical, inspect current included inputs, detect added, changed, and deleted files, and refresh affected relationships and summaries before returning a current view.

It would preserve the intervening edits and reject affected proposals based on the old snapshot. Missing or incompatible cached information would be rebuilt. If inputs keep changing or behavior is unsupported, it would report that boundary rather than silently show the old tree as current.

For a large project, an overview would lead to nested components and cross-cutting connections instead of loading every detail into one prompt. See the [complex-project walkthrough](complex-project.md). Discovery, restart, and refresh speed are measurements to collect, not working performance claims.

### Work with teammates and published changes

Five developers can share committed configuration and project knowledge while their working views remain specific to each checkout. A compatible published snapshot may be reused from local storage, CI artifacts, or an optional service after verification; downloading it does not replace local edits.

If Sally merges while Alice is working, Alice's agent can learn that the published revision advanced even when its graph is pending. It can compare known relationships and show unresolved impact without pretending Alice has rebased or passed tests against the new revision. Git fetching or optional provider notifications can supply awareness; GitHub is not required. Offline operation retains local views and explicitly last-known remote state.

See the [solo and team walkthroughs](../docs/specs/project-coherence.md#walkthroughs). Live sharing of uncommitted edits is outside the first proof.

### What the CLI provides

The CLI is the first entry point into the reusable core. It would expose supported inspection, editing, validation, and compilation operations with automation-friendly results and clear failure behavior.

The user can continue prompting the existing coding agent. Its tool integration must make the CLI available and guide its use; installing a command alone does not make every agent use it automatically.

## Example 2: a developer with an API key or existing harness

The developer already owns a model loop, tool execution, authentication, permissions, and a budget. They want to add Universal IR without replacing that harness.

The initial integration would expose the CLI as a tool:

1. The harness selects a supported project and establishes its current version.
2. It requests the relevant program or source-backed view for the task.
3. The model proposes a supported edit against that version.
4. The CLI delegates the edit and validation to the core.
5. The harness receives structured results, including failures and unsupported behavior.
6. The host runs authorized project checks and supplies the observations to the model.
7. The model repairs failures; the host accepts or publishes a change only within its authorized scope.

The exact request/result format is not defined yet. This workflow must preserve the distinction between a checked representation, generated artifacts, and live deployment.

For the first coherence proof, the harness would request inventory and views, submit attributed knowledge, refresh inputs, and optionally exchange published snapshots or observe upstream. The source-editing loop above follows later. It must not promote model interpretations to developer declarations without the specified evidence origin.

The API key stays in the existing harness. Universal IR does not need to own the model conversation, route providers, or charge for model access. A key without a tool-executing host is insufficient to run these operations.

A public SDK comes later for direct, typed integration. It would use the same core behavior as the CLI, so an API harness does not have to wait for an SDK to participate in the first consumer release.

## What counts as success

A usable consumer release must demonstrate:

- A short, documented setup-to-prompt path for a supported coding agent.
- A new-project task completed with observable checks.
- A real change or fix in a supported existing repository, preserving unrelated code and the project's build/test workflow.
- Reconciliation after offline edits, stale-proposal rejection, and reconstruction without a usable cache.
- An overview connected to task detail, evidence, and visible unknowns across component boundaries.
- An external harness invoking the CLI and consuming its results.
- Explicit support boundaries and rejection of stale or unsupported changes.
- Measured task success, total token use, repair work, latency, review effort, and setup effort against a baseline.

Less busywork and better performance are goals to evaluate. Structure alone does not establish improvements.

Consumer intent and universal coherence remain in decisions 0003 and 0004. Portable state and conversational knowledge are now accepted in decisions [0005](../docs/design/0005-portable-project-state.md) and [0006](../docs/design/0006-conversational-knowledge.md). Follow the [roadmap](../ROADMAP.md) and [architecture](../docs/architecture.md) for remaining implementation gates. To contribute to Universal IR itself, use [CONTRIBUTING.md](../CONTRIBUTING.md).
