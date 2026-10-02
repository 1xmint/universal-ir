# Inspect a project's recorded knowledge

This is a working source-run reader. The [contract](../docs/specs/knowledge-inspection-v1.md) defines its bounds. It can read conforming existing records; it cannot yet capture your conversation, authenticate approval, or write requirements. The [broader knowledge lifecycle](knowledge-lifecycle.md) still requires a host integration.

## Try the fictional project

From the Universal IR checkout with Python 3.12+ and Git:

~~~sh
python -B -m universal_ir knowledge examples/fixtures/knowledge-project
python -B -m universal_ir knowledge examples/fixtures/knowledge-project --id retention --limit 1
python -B -m universal_ir knowledge examples/fixtures/knowledge-project --id retention --offset 1 --limit 1
python -B -m universal_ir knowledge examples/fixtures/knowledge-project --full
~~~

On Windows use `.venv\Scripts\python` instead of `python` when using the development environment. This [static fixture](fixtures/knowledge-project/README.md) is a separate adopting-project input for executable reader tests, not adoption metadata for Universal IR itself. It has no runnable application. All actor/event names are fictional; no one approved these statements.

Expect four revisions, two logical identities, and one competing group. `tenant-isolation` quotes “Keep tenants apart.” from the identified README bytes. Its matching document support establishes a document statement, not an authenticated developer requirement or verified application behavior. `retention` has an initial claim and two competing successors: 30 days and 90 days. All three developer claims show `unverified_attribution` and `pending_acceptance`; the reader cannot choose one as approved.

With `--id retention --limit 1`, only one revision fits, but the group still reports competing heads, their total, and an omitted-head count. Continue paging or use `--full` to inspect every branch and predecessor. A record order or newer Git commit does not resolve the disagreement.

## Edit while the tool is stopped

Copy the fictional project to a disposable directory outside the tool checkout using your normal file tools. Run `knowledge` on that copy. Then change “Keep tenants apart.” in the copy's README and run it again. The same historical statement remains, with `evidence_status: changed` and the original content ID/quote. It does not adopt the new README wording or claim the old words are current. Removing the document produces unresolved evidence; hiding the record store with `.gitignore` produces incomplete coverage, not an empty complete knowledge set.

The reader always reconciles current inputs before publishing; there is no watcher to run while you work. It cannot determine whether application behavior violates the statement. A real test result or deeper semantic adapter would need its own evidence contract.

## Use from your coding agent or harness

An existing agent with terminal access can invoke `inventory` for structure, then `knowledge` for recorded statements. A harness can call the latter through its existing subprocess/tool adapter, parse stdout on exit 0, and handle stderr errors on exits 2/3. Check `coverage.complete`, omissions, attribution, evidence, and competing-group summaries before treating a view as context. Passing JSON to a model does not establish approval or applicability of instructions.

For a project without knowledge records, a configured project returns an empty inspected set. Without project configuration, `knowledge_unavailable` is explicit; inventory still works. There is no supported automatic authoring/setup command yet. A future existing-agent host will propose and accept records under the authenticated binding and checked writer protocol; manually serialized fixtures are useful to test inspection but cannot bypass those gates.

Five developers who pull compatible source/configuration/record files get equivalent identified findings in separate checkout observations. Dirty workspaces can yield different evidence states. Shared caches, network services, GitHub membership, and model calls are unnecessary for this reader. It does not fetch Sally's merge automatically or know about Alice's uncommitted work in another checkout.
