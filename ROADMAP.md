# Roadmap

## Vision

Give AI one shared way to build and change software. Check that the software follows its rules, then turn it into programs that run on different systems. People should always be able to inspect what it does.

We will start small, prove that changes work, and expand to other kinds of software when the evidence supports it.

## Guiding principles

- **Preserve meaning.** Translating a program must preserve its defined behavior.
- **Make changes checkable.** Reject invalid changes before they replace an accepted program.
- **Keep human inspection available.** Show behavior, rules, and changes in forms people can understand.
- **Reuse existing infrastructure.** Build on existing libraries, compilers, and runtimes where they fit.
- **Measure the whole task.** Count context, generation, checking, and repair when comparing token use. Correctness comes first.

## Milestones

Checkboxes show completed work. Later milestones depend on the earlier ones; these are completion gates, not promised dates.

### 0. Explain the idea

- [x] State the vision and current state in the README.
- [x] Describe the proposed architecture and its boundaries.
- [x] Walk through a task application and an administrator archive change.
- [x] Document contribution guidance and ordered milestones.
- [x] Add subscription and API usage journeys, agent handoffs, and decision records.
- [x] Add reproducible documentation checks and tests with pull-request CI.

**Purpose:** Give contributors a shared starting point.

**Done when:** The documentation lets a new reader explain the purpose, current state, and first implementation step. Those answers are available in the [README](README.md).

### 1. Define a small program format

- [ ] Define a versioned format for typed values, functions, references, and explicit effects.
- [ ] Document valid and invalid examples with clear expected interpretations.
- [ ] Specify operation and error meanings, capability boundaries, and deterministic fixture outcomes.
- [ ] Choose the implementation language and initial encoding; record the reasons and tradeoffs.
- [ ] Define reference identities, edit acceptance, version evolution, and compatibility rules.
- [ ] Choose the first user entry point: CLI or SDK, backed by a reusable core.

**Purpose:** Establish precise meanings before writing the core.

**Done when:** Each example has an unambiguous interpretation, including what makes it valid or invalid. The minimum supported operations and version rules are documented.

### 2. Build the core

- [ ] Build a parser and validator for the defined format.
- [ ] Build a reference interpreter for small supported programs.
- [ ] Add structured edits that check their starting version and validate the result before acceptance.
- [ ] Add core behavior tests to the existing CI, including unsupported effects and execution limits.

**Purpose:** Prove that the format can represent, run, and safely change programs.

**Done when:** Small programs run with expected results. Invalid programs, broken references, and stale edits are rejected. A failed edit leaves the previous accepted program intact.

### 3. Generate a useful application

- [ ] Define the minimum data, permission, and interface extensions needed by the worked example.
- [ ] Build TypeScript and PostgreSQL targets for the project task application.
- [ ] Generate its initial behavior and the administrator archive change.
- [ ] Check behavior and permissions through server requests, including requests that bypass the interface.

**Purpose:** Show that one connected representation can produce a useful application.

**Done when:** The generated application passes behavior and permission checks before and after the archive change. Accepted changes include any required data migration and readable explanation.

### 4. Measure the benefit

- [ ] Publish a reproducible comparison against ordinary AI file editing.
- [ ] Use the same tasks, model configuration, acceptance checks, and attempt limits; document approach-specific tools.
- [ ] Report correctness, total tokens, repair attempts, latency, and review effort.
- [ ] Include failed outcomes and explain how measurements were collected.

**Purpose:** Find out whether the representation makes correct changes easier or cheaper.

**Done when:** Someone else can rerun the comparison and inspect both the results and their limits. A finding of no improvement still completes the experiment.

### 5. Demonstrate portability

- [ ] Add a WebAssembly target for the supported computational core.
- [ ] Document which operations are supported and which require unavailable host capabilities.
- [ ] Run matching behavior tests against the reference interpreter and WebAssembly runtime.

**Purpose:** Prove that a shared program can execute through different targets.

**Done when:** The same supported programs pass matching tests in both runtimes. Unsupported operations are reported explicitly. This milestone does not promise that the full task application runs unchanged in WebAssembly.

### 6. Expand from evidence

- [ ] Add domain extensions only for concrete use cases.
- [ ] Improve the model editing interface using measured failures and costs.
- [ ] Add compatibility tests and document boundaries for each addition.

**Purpose:** Grow coverage without losing precise meanings or reliable changes.

**Done when:** Each accepted addition has a use case, documented boundaries, and passing compatibility tests. Track subsequent expansion as separate increments.

## Current boundaries

The repository contains documentation, conceptual examples, and documentation quality tooling. It establishes no public executable API. The compiler implementation language, final encoding, and first user entry point remain decisions for milestone 1. Compiler source directories and runtime build tooling will arrive with executable core code.

See the [architecture](docs/architecture.md) and [worked example](examples/project-tasks.md) for the proposed design.
