# Worked example: a complex project and its changing state

This is a conceptual walkthrough of the proposed [coherent views](../docs/coherence.md) and [adoption lifecycle](../docs/existing-repositories.md). It is not an implemented demonstration, executable syntax, or evidence of support for a particular stack.

## The system at several scales

Imagine a collaboration platform with a web interface, API service, identity integration, task database, background workers, event delivery, shared libraries, deployment configuration, and an external notification provider.

A containment view might show services, then packages, modules, and functions inside each service. Other views would expose connections across them. The archive requirement can connect the web interface to a server permission check, a database update, an emitted event, a worker, and a notification contract.

| Level or relationship | What the agent should find |
| --- | --- |
| Product purpose | Help project members coordinate work; keep project access separate. |
| Domain | Projects, memberships, roles, tasks, and archives. |
| Service boundary | API owns the archive request; the worker owns notification delivery. |
| Cross-service flow | A successful archive update can produce an event consumed by the worker. |
| Implementation detail | Supported declarations, resolved references, and exact source locations. |
| Data and migrations | Task records, project membership lookup, and schema versions. |
| Operational evidence | Which artifacts are deployed and which observations describe them, if available. |
| Verification | Permission, event delivery, and preservation checks with their actual coverage. |

The event link needs evidence: a declared interface, recognized framework configuration, resolved implementation, or an observation. A similar event name in two files is a hypothesis, not a confirmed connection.

## Get a useful overview, then follow a task

The user asks:

> Fix archiving so an administrator can only archive tasks in their own project. Preserve notification behavior and unrelated work.

The system overview should identify the relevant services and current support boundaries. The task view should expand the archive operation, task-to-project relationship, current membership lookup, associated interface, event contract, and checks. It should link to applicable project guidance and the explicit requirement.

If the notification provider implementation is unavailable, show its interface and unknown behavior. If an event consumer is discovered through a heuristic, label it accordingly and let the agent inspect it. The task view must not claim complete impact coverage when unknown edges remain.

A small checked source edit might change the membership lookup to use the task's project. Tests would need to cover an administrator in that project, an administrator in another project, an ordinary member, and a direct request bypassing the interface. Existing task data and established event behavior also need appropriate checks. These cases define intended evidence, not a proof of every distributed-system outcome.

## Pause the tool and change the project

Suppose the tool records source snapshot S1, then stops. Another agent renames an event, changes its producer and consumer, deletes an old module, and adds a new file. A human also changes the task interface without committing it.

On restart, S1 is historical. The tool should inspect the current included files and configuration, detect the offline changes, invalidate affected facts and summaries, and rebuild what cannot be safely reused. Ambiguous renames must not silently preserve an incorrect identity.

Once verified, snapshot S2 should show the changed event relationship, removed module, new file, and current uncommitted interface. Any pending edit based on affected S1 inputs must be rejected or explicitly replanned. The tool must not overwrite these changes to restore S1.

If files change again during reconciliation, it must retry or report an unstable snapshot. If the updated event relationship is no longer understood, S2 can be current within its source scope while explicitly showing that relationship as unresolved.

## Source, deployment, and runtime differ

The workspace may be at S2 while production still runs an artifact built from S1. The development database and production database may have different migration states. A worker observation may describe only one environment and a limited time window.

The graph should keep those identities and relationships separate. It should not infer that refreshing the source view deployed the fix, applied a migration, or updated every running worker. Without deployment or observation inputs, those states remain unknown.

## Evidence required from a future implementation

- Navigate from the system overview to task-specific source and cross-service relationships with their provenance.
- Show omitted and unresolved edges instead of presenting an incomplete task view as exhaustive.
- Reconcile offline additions, deletions, uncommitted edits, and changed configuration before claiming freshness.
- Reject stale proposals and preserve unrelated dirty files.
- Attach check results to the exact candidate; keep deployment and runtime observations separately identified.
- Report cold-start, restart, retrieval, refresh, context size, and whole-task costs, including failures.

Use this walkthrough as an acceptance scenario. A real repository demonstration and measured results must follow before advertising these capabilities.
