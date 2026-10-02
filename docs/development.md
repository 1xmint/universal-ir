# Development readiness

This checklist describes readiness for collaborative development at the current design stage. It is not a score for an implemented compiler. Runtime correctness, portability, security, and token efficiency remain future acceptance gates.

## Foundation checklist

| Area | Evidence |
| --- | --- |
| Clear purpose and honest status | [README](../README.md) and [roadmap](../ROADMAP.md) |
| Defined architectural boundaries | [Architecture](architecture.md) and [accepted foundation decision](design/0001-foundation.md) |
| Concrete user journeys | [Using the project with AI](../examples/using-with-ai.md) |
| Reproducible local checks | [Contribution commands](../CONTRIBUTING.md#local-checks), pinned and hashed tooling dependencies |
| Automated change checks | Required Documentation checks cover links, structure, formatting, checker behavior, and Windows/Linux inventory behavior on pull requests and main |
| Human ownership and review | CODEOWNERS names @1xmint; the PR template asks for purpose, validation, and remaining risks |
| Durable project decisions | [Decision records](design/README.md) |
| Agent task boundaries and handoffs | [AGENTS.md](../AGENTS.md) |
| Private security reporting | [Security policy](../SECURITY.md) |
| Default-branch controls | Required pull requests, documentation checks, linear history, and blocked force pushes and deletion |

## GitHub policy

The repository uses squash merging and deletes merged branches. The active default-branch ruleset requires the **Documentation checks** status, an up-to-date branch, and resolved review conversations. That job now explicitly requires successful Windows and Linux inventory tests; it fails if either prerequisite does not succeed. There are no configured bypass actors.

There is one maintainer, so the required independent approval count is zero. CODEOWNERS identifies ownership; it is not evidence that an independent review happened. Raise that count and require owner review when another independent maintainer is available.

The Actions token has read permissions and cannot approve pull requests. The documentation workflow uses commit-pinned actions, no persisted checkout credentials, and no provider keys. Fork pull requests use the ordinary pull-request event, not a privileged target workflow. Dependabot checks the tooling and actions weekly.

Secret scanning and push protection are enabled. Private vulnerability reporting is enabled. Wiki and project-board features are disabled because the repository documents its plan and decisions in versioned files.

## Verify the controls

These read-only commands require GitHub CLI access to the repository:

~~~sh
gh api repos/1xmint/universal-ir/rulesets
gh api repos/1xmint/universal-ir/rules/branches/main
gh api repos/1xmint/universal-ir/actions/permissions/workflow
gh api repos/1xmint/universal-ir/private-vulnerability-reporting
gh run list --repo 1xmint/universal-ir --workflow docs.yml --limit 5
~~~

Check live settings after changing a workflow, status name, permission, or branch rule. Documentation about settings can become stale.

The policy follows GitHub's [ruleset model](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets) and [workflow security guidance](https://docs.github.com/en/actions/reference/security/secure-use).

## Next implementation gate

Before building the executable program core, milestone 1 must define the supported subset, operation meanings, errors, reference identities, effect and capability boundaries, edit acceptance, version evolution, and valid/invalid fixtures. Source-editing work also needs semantic mappings, invalidation, and application/recovery guarantees. Those decisions need a recorded rationale. The [CLI-first decision](design/0002-cli-first.md) fixes delivery priority, and [decision 0004](design/0004-universal-coherence.md) establishes universal coherence and freshness goals.

The [portable project-coherence specification](specs/project-coherence.md) defines inventory, knowledge, lifecycle, and optional collaboration requirements. Decisions 0005 and 0006 settle source authority, portable storage, and conversational provenance. [Decision 0007](design/0007-local-inventory-proof.md) and the [local inventory contract](specs/local-inventory-v1.md) define and implement the bounded configuration, identity, filesystem, views, and CLI subset in Python. [Decision 0008](design/0008-verified-local-snapshots.md) adds optional external snapshots and publication recovery after full source verification, covered by the same Windows/Linux CI gate. Knowledge/host provenance, cost baselines, and incremental extraction remain next gates. Remote release needs transport/access/trust, scheduling, and retention contracts. Deeper source editing and executable IR retain their separate gates.

Keep an interpreter as a reference for target behavior. Passing type checks alone must not be presented as proof that a program matches human intent or is safe to deploy.

Before a runtime release, add the applicable test matrix, installation instructions, version and compatibility policy, release automation, and supported-version security policy. Add evidence for each claim as the product grows.
