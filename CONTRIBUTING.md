# Contributing

Start with the [README](README.md), [architecture](docs/architecture.md), [roadmap](ROADMAP.md), and [development guide](docs/development.md). The current runtime design is proposed; documentation quality tooling is executable.

## Propose a change

Use an issue for a concrete problem or substantial design proposal. Small documentation fixes can go directly to a pull request. A direct maintainer task can also establish scope.

For changes to the program format or architecture, record a [design proposal](docs/design/README.md) before a large implementation. Include the use case, desired behavior, meaningful alternatives, and validation plan.

Keep each pull request focused on one coherent change. Explain the problem and resulting behavior, how it was checked, and remaining limitations. Update related documentation and examples together.

## Local checks

Install Python 3.12 or newer and Git. These are documentation tooling requirements, not a choice of compiler implementation language.

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

The documentation workflow runs the checker and its failure-oriented tests. Dependency versions and artifact hashes are pinned. Dependabot proposes dependency updates; validate the updated lock hashes and both commands before merging.

## Review and publication

Work on a branch and open a pull request. Default-branch rules require the Documentation checks status, an up-to-date branch, resolved review conversations, and linear history. Squash merge reviewed changes.

There is currently one maintainer, @1xmint. A second-person approval is not required yet, and ownership must not be presented as independent review. Require independent approval when another maintainer joins.

For agent contributions, include scope, changed behavior, commands and outcomes, unresolved decisions, and the next useful step. An agent can create or merge a pull request only within the user's authorized task. Never mark work complete solely because the agent says it succeeded.

## Record design decisions

Keep important accepted choices in numbered [decision records](docs/design/README.md), including their reasons, tradeoffs, and compatibility effects. Record acceptance through the pull request that adopts the decision. Preserve superseded records.

Reusable core, CLI first, SDK later is accepted in [decision 0002](docs/design/0002-cli-first.md). The compiler implementation language, final encoding, and exact CLI interfaces remain decisions for milestone 1. Add compiler source directories and runtime build tooling when implementing the core.

## Provide evidence

For behavior changes, check intended behavior and relevant failure cases. Permission changes must be tested through trusted execution boundaries, including requests that bypass the interface.

For efficiency claims, report the complete task: model and tool configuration, acceptance criteria, context and generation tokens, checking and repair costs, latency, and review effort. Include failed attempts and enough detail to reproduce the comparison.

Mark a roadmap milestone complete only when its completion conditions are met. Distinguish proposals, accepted decisions, implemented features, and measured results.

## Security and license

Use the [security policy](SECURITY.md) for private reports. Never include provider credentials or private data in commits or reports.

Contributions are provided under the repository's [MIT license](LICENSE).
