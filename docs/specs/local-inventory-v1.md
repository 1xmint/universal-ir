# Local inventory prototype, version 1

**Status:** Implemented bounded prototype under [decision 0007](../design/0007-local-inventory-proof.md). This is a subset of the [portable coherence specification](project-coherence.md), not a complete coherence or executable IR release.

## Supported operation

Run from the Universal IR checkout with Python 3.12+ and Git on PATH:

~~~sh
python -m universal_ir inventory /path/to/project
python -m universal_ir inventory /path/to/project --path services --limit 20 --offset 0
python -m universal_ir inventory /path/to/project --full
python -m universal_ir inventory /path/to/project --baseline /outside/project/before.json
~~~

On Windows the existing development environment can run `.venv\Scripts\python -m universal_ir` instead of `python -m universal_ir`. Quote paths containing spaces. This is a source-run prototype, with no packaged installer or stable public SDK. This contract covers `inventory`; a separate [knowledge operation](knowledge-inspection-v1.md) inspects existing records. Inventory never modifies the selected project, initializes its Git repository, fetches remotes, executes project scripts, or contacts a model.

Every invocation reconstructs from current inputs. Optional `--cache-dir /outside/project/cache` stores/reuses snapshots only after that full verification, as defined in the [local cache contract](local-cache-v1.md). The selected project remains untouched. There is no watcher, initialization command, conversational knowledge writer, shared snapshot import, or upstream awareness. `.uir/knowledge/` files are inventoried as source files, not interpreted as authenticated declarations. Existing agent guidance is identified by filename, not automatically obeyed or proved applicable.

Python may create its ordinary bytecode caches in the Universal IR tool checkout. Use `python -B -m universal_ir` to disable those writes when inspecting the tool checkout itself; inventory does not create caches in another selected project.

## Configuration

Configuration is optional. If present, `.uir/config/project.json` must be a UTF-8 JSON object with these exact fields; unknown fields and duplicate JSON keys fail:

~~~json
{
  "version": 1,
  "project_id": "example-project",
  "exclude": ["vendor", "build"],
  "documents": ["README.md", "docs/architecture.md"]
}
~~~

`project_id` is a nonempty project-owned string. `exclude` and `documents` are lists of unique project-relative paths using `/`, with no absolute path, backslash, colon, empty segment, `.` or `..`, control character, or wildcard. An exclusion matches that path and its descendants, not a glob. Document links may remain unresolved. Configuration does not declare a recovered purpose or grant permissions. No metadata is automatically created; developers can add configuration through their normal review workflow.

Without a file, use `{version: 1, project_id: null, exclude: [], documents: []}` as the default scope. Null means no durable project identity has been established. Equal inventories of unconfigured projects can share content identity; that does not assert they are the same collaborating project.

Always include configuration as a control input even if an exclusion would hide it from the file view. Read every `.gitignore` used in traversed directories as a control input, including when its own filename is ignored. A symlink or junction in the configuration path is rejected. Ignore files that are links are boundaries and are not followed; Git itself does not follow symlinked `.gitignore` files.

## Filesystem and ignore scope

The selected root must exist and be a directory, and must not contain the system temporary directory used for isolated Git evaluation. Relative paths retain spelling and source contents are hashed without newline normalization. This prototype requires portable UTF-8 path names: the same segment/character restrictions as configuration paths apply to included directory entries, including control characters and wildcard characters. Unsupported names fail rather than being silently renamed or dropped. File contents can be arbitrary bytes.

Exclude `.git` entries anywhere and `.uir/cache/` at the selected root. Apply explicit exclusions and root/nested `.gitignore` rules through `git check-ignore --no-index`, with NUL-separated paths, case-sensitive matching, isolated configuration, and a temporary repository outside the project. The temporary repository is removed after the call. Machine-global Git ignore files and private `.git/info/exclude` are intentionally outside scope. The same rules apply whether a file is tracked, dirty, or untracked. Git commit and branch state are not collected.

Do not descend into symlinks, Windows junctions, nested repositories, or special filesystem objects. Record these as boundaries. Nested repositories are directories with their own `.git` entry; the selected root itself may be a repository. Ignored or excluded paths are omissions, not empty known components. An unreadable included file or control input blocks a successful result. Excluded contents are never read for inventory. An ignore evaluator failure cannot silently fall back to scanning everything.

The selected filesystem is trusted local input, not a sandbox against malicious writers swapping links during traversal. Capture detects ordinary in-flight changes but cannot promise atomic multi-file observation on an arbitrary mutable filesystem. Use an externally frozen tree where atomicity is required.

## Identity and evidence

JSON result format is `uir.inventory.v1`; extractor is `inventory.v1`. SHA-256 file identities hash exact bytes. The snapshot manifest contains the effective configuration, control-input content hashes, included entries, boundaries, omissions, and ignore-engine compatibility version. Absolute root, observation time, local metadata tokens, pagination, and comparison are excluded from content identity.

Canonical identity encoding is UTF-8 JSON with keys sorted, no insignificant whitespace, non-ASCII characters preserved, and no NaN. Entry and omission lists use deterministic path order; configuration lists retain declared order. The snapshot ID is `sha256:` followed by the digest of that manifest. JSON output ordering and indentation need not be identical to identity encoding. Changes to relevant configuration, control inputs, directory membership, file bytes, or extractor compatibility change identity. Empty directory membership is represented. Different local paths and timestamps do not change content identity.

Every entry has a relative path, kind, and parent. File entries also have byte count and content ID; extension-based language and name-based role labels are explicitly hypotheses. The overview includes project identity when configured and aggregate language hypotheses. Unrecognized files have unknown classification; no code parser, symbol resolver, import graph, call graph, permission check, or runtime analysis is present. A directory hierarchy supports containment, not complete software architecture.

Containment edges and configured document links carry their origin and evidence within the returned snapshot. A document target is resolved only when it is an included file; absent, excluded, directory, and boundary targets remain unresolved. Guidance candidates are README, AGENTS, CONTRIBUTING, and SECURITY Markdown files identified by name; their contents and instruction applicability are not interpreted.

Local checkout attribution is the resolved root in the observation envelope. It is not a durable workspace ID or developer authentication. No remote published revision is assigned to a dirty workspace.

## Freshness and failures

Capture configuration, control inputs, directory membership, boundaries, and file hashes twice. Compare manifests and local metadata tokens for both passes. If they disagree, try again up to three pairs. Successful freshness means `verified_consecutive_captures`, with start/end timestamps and the atomicity limitation visible. It does not mean a cache hit, a frozen filesystem, or a guarantee about edits after observation. No partial or mixed detected result is labeled verified. A disappeared input triggers retry; unreadable input returns a diagnostic.

Each invocation after stopped operation rebuilds from source, so additions, removals, edits, and configuration changes cannot be hidden by a missing watcher or stale cache. There is no background monitoring while the process is stopped.

| Exit | Result |
| --- | --- |
| 0 | Versioned JSON success on stdout, with snapshot, coverage, freshness, views, and optional comparison. Unknown semantics, unresolved document links, and boundaries are visible successful inventory outcomes. |
| 2 | Versioned JSON error on stderr for invalid arguments/configuration, unsupported paths, missing Git, unreadable inputs, invalid selection, incompatible baseline, or failed ignore evaluation. No success view is returned. |
| 3 | Versioned JSON `unstable_inputs` error on stderr after three mismatching capture pairs. Retry when inputs settle or use an externally frozen tree. |

Errors contain `format`, `status`, `error.code`, and `error.message`. Invalid JSON, unsupported versions, and scope widening are never silently repaired. No failure overwrites source or a prior saved inventory.

## Views and comparison

Default view contains at most 20 entries, selected by lexicographic path order; `--limit` accepts 1 through 200. `--path` selects an included file or directory subtree; `.` selects the root. `--offset` pages entries. A bounded immediate-child outline helps locate components without loading their contents. The view includes parent edges, snapshot-qualified evidence, bounded guidance and document-link lists, total and omitted counts, and a next offset where available. A view is not a relevance ranking. No result within a selection is not a statement about excluded files or unsupported semantics. Full detail is available through `--full`, which includes the complete manifest and all entries/relationships and ignores pagination only after valid arguments. Full output also expands truncated outline, guidance, document-link, exclusion, and comparison lists.

A baseline must be a full version-1 success export, with a valid manifest shape, unique ordered paths, and matching SHA-256 identity. Extractor and ignore-engine versions must match. Configuration may differ and is reported explicitly. This validates bytes and compatibility, not producer trust or the truth of unverified external findings. Baselines are comparison-only and never replace current extraction.

Comparison reports added, removed, and changed **inventory inputs**, with counts and a list bounded by `--limit` unless full output is requested. Removed input means no longer inventoried, possibly because scope changed; it does not prove physical deletion. It reports configuration change and preserves both snapshot IDs. It does not calculate semantic change impact, rename continuity, tests, or permission correctness. Save exports outside the project or inside excluded `.uir/cache/` to avoid making an export its own input. Without the cache flag, the CLI writes only stdout/stderr; the host controls redirection and file permissions. With it, the only additional writes are to the explicitly selected external cache namespace.

## Acceptance and next increments

Behavior tests cover byte preservation, identical facts across locations, mixed-language hypotheses, nested ignores and negation, no-Git projects, opaque bytes, missing document references, boundaries, configuration changes, additions/removals/edits, bounded expansion, invalid arguments/configuration/baselines, unreadable inputs, and detected concurrent edits. Windows and Linux run the same core suite in required CI.

Verified local snapshot storage is implemented in the [separate cache increment](local-cache-v1.md). Remaining gates include incremental extraction/invalidation, durable workspace identities, authenticated conversational knowledge acceptance and host provenance, source-linked excerpts, model enrichment evaluation, shared snapshot trust, and remote revision awareness. The full program-format and consumer-release milestones remain incomplete. No performance threshold or token saving is claimed.

Git's [ignore rules](https://git-scm.com/docs/gitignore) and [check-ignore interface](https://git-scm.com/docs/git-check-ignore) support the ignore design. Python's [hashlib](https://docs.python.org/3/library/hashlib.html) provides SHA-256. These are implementation references, not evidence of measured performance.
