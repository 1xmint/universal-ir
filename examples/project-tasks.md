# Worked example: project tasks

This is a conceptual walkthrough, not executable syntax. It illustrates the proposed architecture; none of the described application behavior is implemented yet.

## The application

People belong to projects and keep a list of tasks for each project. A project member can read and create tasks. A project administrator is a member with an additional role.

| Data | Meaning |
| --- | --- |
| Person | An authenticated person with a stable identity. |
| Project | A named project with a stable identity. |
| Membership | Connects a person to a project and gives them a member or administrator role in that project. |
| Task | Belongs to one project and has a stable identity, title, and open or completed status. |

Roles apply within a project. Being an administrator in one project gives no access to another project.

Initially, members see all tasks in their project and can create tasks there. Archiving does not exist. Other task actions are outside this example.

## Describe the connected parts

The shared representation would connect:

- The task data to its project.
- Read and create operations to project membership rules.
- Those operations to their declared storage effects.
- The task list and create form to the corresponding operations.
- Behavior checks to the rules they are meant to exercise.

The TypeScript target would produce interface and server behavior. The PostgreSQL target would produce storage definitions and constrained queries. A target integration would supply the authenticated identity; a client-supplied role would never establish authority.

Server-side enforcement must protect the data even when someone bypasses the interface and sends a request directly. Hiding a button can explain available actions, but it does not enforce access.

## Request a change

> Allow project administrators to archive tasks.

For this example, make these choices explicit:

- Archiving keeps the task and its open or completed status, and adds a separate archived flag.
- Existing tasks begin unarchived.
- All current project members can still read archived tasks through an archive view.
- The default task list shows unarchived tasks.
- Only current administrators of the task's project may archive it.
- Repeating an authorized archive request leaves the task archived without an additional change.
- Restoring or permanently deleting tasks is outside this change.

These are example requirements, not universal defaults for future applications.

## Trace the edit through the program

| Connected part | Proposed change |
| --- | --- |
| Task data | Add an archived flag without changing task identities or completion status. |
| Archive operation | Identify a task, check its project's current administrator membership, and mark it archived. |
| Permission rule | Require an authenticated person with the administrator role in that task's project. |
| Effects | Declare the membership read, task read, and task update needed by the operation. |
| Interface | Add an archive action for administrators and an archive view for project members. |
| Storage migration | Add the archived flag and initialize existing tasks as unarchived. |
| Checks | Exercise allowed requests, denied requests, repeated requests, and preservation of existing task data. |

The edit refers to the existing task and project parts by stable identity. The system checks the candidate version before accepting it, then generates updated artifacts and the required migration. Applying that migration to a deployed database would be a separate execution step.

A readable change summary would say:

> Project administrators can archive tasks. Archived tasks remain available to project members in the archive view. Existing tasks start unarchived.

## Expected behavior to check

| Scenario | Expected result |
| --- | --- |
| Administrator archives a task in their project | The task is archived; its identity, title, and completion status remain intact. |
| Ordinary member attempts to archive a task | The request is denied and the task is unchanged. |
| Administrator of another project attempts to archive the task | The request is denied and the task is unchanged. |
| Unauthenticated person sends an archive request directly | The request is denied and the task is unchanged. |
| Person whose administrator membership has been removed sends an archive request | Current permissions are checked; the request is denied. |
| Authorized administrator repeats an archive request | The task remains archived without an additional change. |
| Current member opens the default list | Only unarchived tasks in their project appear. |
| Current member opens the archive view | Archived tasks in their project appear. |
| Nonmember requests either task view directly | No project task data is returned. |
| Existing tasks are migrated | They remain readable with their prior data and start unarchived. |
| Proposed edit has a broken reference or starts from a stale version | The edit is rejected and the previous accepted program remains intact. |

These checks are acceptance scenarios for future implementation, not claims of passing tests today.

## What this example demonstrates

One change connects data, authority, interface behavior, storage, and checks. The graph makes those relationships available for inspection and validation. Whether this approach improves correctness or total token cost must be measured.

Return to the [architecture](../docs/architecture.md) or [roadmap](../ROADMAP.md).
