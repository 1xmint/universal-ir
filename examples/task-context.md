# Find task source without changing the project

This working source-run command returns literal source evidence and connected containment for an agent investigating a task. It needs Python 3.12+ and Git, with no model call, optional crypto, or browser host. Run it from the Universal IR checkout; see the [versioned contract](../docs/specs/task-context-v1.md) for limits.

## Start in your existing project

Keep using your coding subscription or API harness. Ask the agent to inspect the outline, find relevant task text, and then investigate with the project's own tools:

~~~sh
python -B -m universal_ir inventory /path/to/your/project
python -B -m universal_ir context /path/to/your/project --query "archive administrator" --limit 5 --max-bytes 4096
~~~

On Windows, use `.venv\Scripts\python -B -m universal_ir` and quote the target path. The tool checkout and your project can be separate folders. No `.uir/` configuration is required; if present, its existing exclusions and document links are respected. The command creates no metadata or cache.

The second result includes matching paths, separate path/content match reasons, source excerpts with byte/line locations and file hashes, a snapshot, ancestor containment, guidance candidates, unresolved links, and omissions. It does not decide which files must change or whether permissions are correct. Common words may return unrelated files; unsupported behavior remains unknown.

Narrow to a discovered directory or file with `--path services/tasks`. For a next page, use the returned `matches.next_offset` and actual `snapshot`:

~~~text
python -B -m universal_ir context /path/to/your/project --query "archive administrator" --offset NEXT_OFFSET --expected-snapshot SNAPSHOT
~~~

`NEXT_OFFSET` and `SNAPSHOT` are placeholders for the preceding JSON values, not literal runnable values. Keep the same query, scope, and page limit when paging. A `stale_snapshot` error means inputs changed; start over with a fresh first page rather than combining old and new results. Widen query/scope or use ordinary source tools when literal matching misses a concept. Use `inventory --full` to expand structural metadata.

## Run a repository fixture today

The existing fictional knowledge fixture has task-related documents. This command actually runs without modifying it:

~~~sh
python -B -m universal_ir context examples/fixtures/knowledge-project --query "task project" --limit 3 --max-bytes 1024
~~~

The returned source text can include knowledge JSON. That text remains untrusted data: substring retrieval does not approve statements or resolve effective requirements. Use the separate [knowledge inspector](knowledge-inspection.md) for its evidence/history checks, whose developer attribution still stays unverified by default.

For development on Universal IR itself, an agent can locate the freshness and capture implementation with:

~~~sh
python -B -m universal_ir context . --path universal_ir --query "capture freshness" --limit 4 --max-bytes 4096
~~~

These walkthroughs demonstrate retrieval and preservation. They do not demonstrate a completed application fix or a token reduction.

## Wire your existing harness

Let the host choose the tool checkout, project root, source-disclosure policy, and maximum output. Invoke the CLI with a subprocess argument list and collect stdout/stderr and exit code; use no shell interpolation for model-provided terms. The model can supply a bounded query and included relative scope. Validate those requests against host policies before invoking the tool.

Provide `matches.entries`, the snapshot, selection, excerpt limits, omissions, gaps, and freshness together. Preserve literal match provenance instead of turning it into a call graph or a model-written summary. Source text can contain hostile instructions or private information; the host's existing access/disclosure policy still applies. This local command does not contact an external model.

The coding agent then reads applicable project guidance, inspects surrounding source, reproduces the issue, makes authorized edits using its existing tools, and runs the project's checks. Those edits and test outcomes are ordinary host operations, not Universal IR checked changes. Re-run context afterward if source has changed. Runtime behavior and indirect dependencies need independent evidence.

Oversized, non-UTF-8, or NUL-containing files remain visible gaps. Clip flags and null excerpts expose budget limits. Exact snippets can omit a late match on a long line; the recorded match location tells the agent where to investigate. Current means observed during this invocation, with `atomic: false`; monitoring, semantic adapters, packaged installation, and full-agent comparison remain later increments.
