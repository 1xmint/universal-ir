# Using Universal IR with a coding agent

A coding subscription or API key gives your chosen tool access to a model. Universal IR would provide a checked program representation and compiler tools. The coding agent would connect the two.

Today this repository contains a design, examples, and documentation quality tooling. It cannot yet build an application. The journeys below distinguish actions you can take now from proposed future use.

## Today: use an existing coding subscription

Use a coding agent that can work with local files and commands. Authenticate through that agent using an access method supported by its provider. Universal IR does not collect your subscription credentials.

Clone the project and open the folder in your agent:

~~~sh
git clone https://github.com/1xmint/universal-ir.git
cd universal-ir
git switch -c docs/my-first-contribution
~~~

Ask the agent to read README.md, ROADMAP.md, AGENTS.md, and the relevant example before changing anything. Give it a bounded task:

> Review the project task example against the architecture. Find inconsistencies in permission rules or archive behavior. Fix only those documentation issues, run the repository checks, and report the changes, evidence, and remaining questions. Do not invent a working compiler or mark unbuilt milestones complete.

Review the diff yourself. Use the [local checks](../CONTRIBUTING.md#local-checks) and submit a pull request. No API key is needed for those checks.

For milestone 1, a useful design task is:

> Propose the smallest program format needed to represent and interpret a pure function. Explain values, types, references, errors, and unsupported operations. Include valid and invalid examples. Record the proposal as a design decision and identify choices needing maintainer acceptance. Keep compiler implementation out of this change.

This helps build Universal IR. It does not yet use Universal IR to build your own app.

## Today: use an API-backed agent

An API key alone cannot read a repository or run its commands. Use an existing agent host or your own integration that can call the model, expose scoped file and command tools, and track tool results.

Authenticate in that host's local settings or environment. Do not paste keys into prompts, examples, Git commits, or pull requests. Access methods and billing depend on the provider; a subscription does not establish API access for every tool.

Point the host at your clone and use the same bounded tasks and checks as above. Set your own model budget and review its tool actions. The repository does not supply this agent host or pay for its model calls.

## Proposed future: build your own app

Once the core and application targets exist, a user journey could be:

1. Install a released Universal IR tool and open a separate application workspace.
2. Use your existing coding agent and its existing model authentication.
3. Ask for a project task app and settle the permissions and behavior requirements.
4. Have the agent create a program graph through the supported editing interface.
5. Validate the candidate graph and run behavior checks.
6. Accept a checked version and compile it through the TypeScript and PostgreSQL targets.
7. Review the readable changes and generated artifacts before running or deploying the app.
8. Ask for the administrator archive change, then repeat the checks and review the data migration.

The model could run remotely while validation and compilation run locally. The library, installer, CLI commands, and integration protocol do not exist yet; their exact interfaces will be decided and documented before release.

Universal IR would complement the coding agent. It would not automatically provide model access, deployment hosting, or support for every existing framework.

## Proposed future: embed it in a custom agent

A developer could use an SDK to inspect a graph, submit an edit against a known version, obtain validation results, and compile supported targets. The developer's agent host would own the model loop and resource access.

| Entry point | Main advantage | Main tradeoff |
| --- | --- | --- |
| Local CLI | Existing agents can call it through terminal tools across providers and languages | Process overhead and command-result handling |
| Embedded SDK | Typed, direct integration with a custom host and repeated operations | Language bindings and closer version coupling |

A reusable core can support both. CLI first is the current recommendation for ease of adoption; it is a proposal, not an accepted interface decision.

Return to the [roadmap](../ROADMAP.md), [architecture](../docs/architecture.md), or [development guide](../docs/development.md).
