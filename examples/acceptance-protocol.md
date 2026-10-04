# Walk through acceptance, conflicts, and restart

**Executable abstract model:** This walkthrough runs transaction rules in memory under [decision 0015](../docs/design/0015-acceptance-protocol-model.md). It does not approve real project knowledge, authenticate a person, acquire an OS lock, or write a project. Production behavior remains proposed in the [logical contract](../docs/specs/knowledge-acceptance-model.md).

## Run the demonstration

From this checkout with Python 3.12+:

~~~sh
python -B scripts/acceptance_model.py
python -m unittest discover -s tests -p test_acceptance_model.py -v
~~~

On Windows use `.venv\Scripts\python`; on macOS/Linux use `.venv/bin/python` after [environment setup](../CONTRIBUTING.md#local-checks). The model itself uses only the standard library. It has no project-path argument or file input, and no paid call, key, source scan, or writer.

The demonstration stages a symbolic record, restarts before publication, retries, stages both artifacts, and publishes an ideal decision. It restarts again, changes the source token, and acknowledges the already-committed operation without authorizing another write. The report explicitly labels human authentication, filesystem atomicity, and durability as `assumed_not_demonstrated`.

## Alice and Sally refine a requirement

Suppose the initial declaration is represented by `r1`. These names are symbolic model tokens; actual record digests would bind full wording, scope, origin, evidence, supersession, and state.

| Step | Simulated result |
| --- | --- |
| Alice starts `r2` from head `r1` in one checkout | Holds the model's ideal transaction boundary |
| Sally attempts another transaction in that same boundary | Busy; after Alice publishes, Sally's old expected head is stale |
| Alice stages a record or receipt but stops before publication | `r1` remains the simulated accepted head; the event is unused |
| Alice publishes the complete decision but loses the response | Restart and exact retry return the same historical result; no duplicate decision |
| Alice and Sally instead publish `r2` and `r3` in separate checkouts | Each has a locally valid modeled successor of `r1` |
| Those published histories are merged | Both `r2` and `r3` remain heads, regardless of import order |
| A resolution names only one competing head | Rejected; a complete authorized transition must cover both |
| A resolution explicitly covers both | One modeled head, with `r1`, `r2`, and `r3` retained as history |

Five developers follow the same rule: shared published history and separate local transaction boundaries. A busy result is local serialization; it is not a distributed team lock. Merging source and importing accepted history require independent checks.

## Event reuse, withdrawal, and missing data

An event key is project, host, and event. Repeating an exact complete operation acknowledges its history. Reusing that event for changed wording, another proof/review, or a different transition is a conflict, even after restart. If two branches independently use the same event for different decisions, the merged model reports conflict and retains the decisions for diagnosis; it cannot choose the later timestamp.

A staged withdrawal has no effect. A modeled published withdrawal must supersede the actual current heads and preserve their records. Changed source does not itself withdraw a declaration.

If a published decision names an absent record or receipt, resolution fails as incomplete committed history. It must not drop that decision and revive an older requirement. Recovery needs the exact missing artifact or a separately authorized correction, not a guessed replacement.

## How this will relate to real development

An agent would propose exact knowledge with the existing [preparation command](knowledge-preparation.md). A protected human channel would capture approval, and a future host would verify the [context-bound assertion](prepared-receipts.md), reconcile accepted heads, and publish through a demonstrated physical transaction.

The model's true conditions stand in for those checks solely in tests. They cannot become model tool arguments or prove a person approved anything. The next implementation gates remain a concrete authenticated host, historical proof resolution, real staging/capture and lock/commit/recovery contracts, and a writer with cross-process/platform evidence.
