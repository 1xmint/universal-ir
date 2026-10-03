# Contributing

Start with the [README](README.md), [architecture](docs/architecture.md), [roadmap](ROADMAP.md), and [development guide](docs/development.md). The compiler/runtime design remains proposed; local inventory and quality tooling are executable.

## Propose a change

Use an issue for a concrete problem or substantial design proposal. Small documentation fixes can go directly to a pull request. A direct maintainer task can also establish scope.

For changes to the program format or architecture, record a [design proposal](docs/design/README.md) before a large implementation. Include the use case, desired behavior, meaningful alternatives, and validation plan.

Keep each pull request focused on one coherent change. Explain the problem and resulting behavior, how it was checked, and remaining limitations. Update related documentation and examples together.

## Local checks

Install Python 3.12 or newer and Git. They run quality tooling and the local inventory prototype, not an executable IR compiler. Inventory itself uses the standard library and Git; the pinned Markdown dependency is for documentation checks only.

Create an isolated environment:

~~~sh
python -m venv .venv
~~~

On Windows, run from the repository root:

~~~powershell
.venv\Scripts\python -m pip install --require-hashes -r requirements-dev.txt
.venv\Scripts\python scripts/check_docs.py
.venv\Scripts\python -m unittest discover -s tests -v
~~~

On macOS or Linux:

~~~sh
.venv/bin/python -m pip install --require-hashes -r requirements-dev.txt
.venv/bin/python scripts/check_docs.py
.venv/bin/python -m unittest discover -s tests -v
~~~

The checker uses a Markdown parser to check local links and heading anchors, document headings, closed code fences, UTF-8/LF formatting, and accidentally tracked environment files. Code examples are not treated as links. It checks tracked and non-ignored new files. External links are not fetched during CI; review them when changing source references.

The checker supports CommonMark links, headings, tables, and strikethrough. Use Markdown links rather than raw HTML links. Inspect GitHub rendering when changing tables, diagrams, or other presentation-sensitive content. Checks do not establish semantic agreement between documents; the reviewer must inspect that.

The workflow runs documentation checks and checker tests, plus inventory/cache/cost and knowledge inspection behavior/failure tests on Windows and Linux with Python 3.12. The required Documentation checks job explicitly fails unless both inventory jobs pass, including when a prerequisite fails. Dependency versions and artifact hashes are pinned. Dependabot proposes dependency updates; validate the updated lock hashes and both local commands before merging.

Receipt tests additionally require `python -m pip install --require-hashes --only-binary=:all: -r requirements-receipts.txt` (use the environment's Python path above). The runtime dependency is optional for inventory/default knowledge inspection; CI tests those before installing the receipt verifier, then exercises receipt behavior and the fictional host demo on both platforms. The same required job covers all suites. No model credentials or paid calls are required.

The same optional dependencies support `tests/test_harness.py`, covering host-fixed settings and adversarial model requests through the real handler. Required Windows/Linux CI runs that suite after receipt tests. The adapter is internal, with no stable SDK or authenticated human-event claim.

## Review and publication

Work on a branch and open a pull request. Default-branch rules require the Documentation checks status, an up-to-date branch, resolved review conversations, and linear history. Squash merge reviewed changes.

There is currently one maintainer, @1xmint. A second-person approval is not required yet, and ownership must not be presented as independent review. Require independent approval when another maintainer joins.

For agent contributions, include scope, changed behavior, commands and outcomes, unresolved decisions, and the next useful step. An agent can create or merge a pull request only within the user's authorized task. Never mark work complete solely because the agent says it succeeded.

## Record design decisions

Keep important accepted choices in numbered [decision records](docs/design/README.md), including their reasons, tradeoffs, and compatibility effects. Record acceptance through the pull request that adopts the decision. Preserve superseded records.

Reusable core, CLI first, SDK later is accepted in [decision 0002](docs/design/0002-cli-first.md). [Decision 0007](docs/design/0007-local-inventory-proof.md) chooses Python for the inventory prototype and specifies its provisional CLI. Keep extraction in `universal_ir/inventory.py`, optional snapshot storage in `universal_ir/cache.py` under [decision 0008](docs/design/0008-verified-local-snapshots.md), and terminal handling in `universal_ir/__main__.py`. Compiler language, final IR encoding, and later executable interfaces remain milestone 1 decisions.

## Provide evidence

For behavior changes, check intended behavior and relevant failure cases. Permission changes must be tested through trusted execution boundaries, including requests that bypass the interface.

For efficiency claims, report the complete task: model and tool configuration, acceptance criteria, context and generation tokens, checking and repair costs, latency, and review effort. Include failed attempts and enough detail to reproduce the comparison.

Use the [local cost tool](benchmarks/README.md) for the narrower inventory/storage baseline. Its synthetic timings, context bytes, and digest comparisons do not establish complete agent-task efficiency. Knowledge implementation must follow the [record specification](docs/specs/project-knowledge-v1.md) and demonstrate a trusted host binding plus stale/concurrent/interrupted acceptance before introducing a writer. Keep the existing reader in `universal_ir/knowledge.py` under the [inspection contract](docs/specs/knowledge-inspection-v1.md); validate its fictional fixture, evidence, history, capture races, and coverage independently of future approval work.

Mark a roadmap milestone complete only when its completion conditions are met. Distinguish proposals, accepted decisions, implemented features, and measured results.

## Security and license

Use the [security policy](SECURITY.md) for private reports. Never include provider credentials or private data in commits or reports.

Contributions are provided under the repository's [MIT license](LICENSE).
