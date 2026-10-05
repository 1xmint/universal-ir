# Task context, version 1

**Status:** Implemented bounded read-only prototype under [decision 0018](../design/0018-deterministic-task-context.md). This is literal retrieval over inventory inputs, with source evidence. It establishes no execution semantics, approved intent, or complete change-impact coverage.

## Source-run operation

Run from the tool checkout with Python 3.12+ and Git:

~~~sh
python -B -m universal_ir context /path/to/project --query "archive administrator"
python -B -m universal_ir context /path/to/project --query "archive" --path services --limit 5 --max-bytes 4096
~~~

Windows can use `.venv\Scripts\python` in place of `python`. This command needs only the standard library and Git. No crypto, Node, model, account, or running review host is needed. There is no packaged installer or stable SDK.

`root` selects the project. `--path` defaults to `.` and selects an included file or directory subtree. It cannot expand a boundary or an excluded path. The operation inherits inventory's filesystem and ignore scope: included dirty/untracked files, nested ignore rules, explicit configuration exclusions, configuration control inputs, and no following links or nested repositories. See the [inventory contract](local-inventory-v1.md).

The command hashes all inventory inputs even with a narrow search path. It searches source text only in the selected scope, writes nothing in the project, and executes no project scripts. `-B` also avoids ordinary Python bytecode writes in the tool checkout. A host redirecting stdout should save exports outside the inspected project or in an excluded location to avoid adding its own output as an input.

## Literal selection

`--query` is required, contains 1..256 Unicode characters, and has non-whitespace text. UTF-8 representability is required. ASCII controls other than tab/CR/LF and DEL are rejected. Apply Unicode casefold, split on whitespace, deduplicate, then sort terms. Allow at most 16 distinct terms.

Each term is a literal substring, with no regex, glob, stemming, synonyms, or symbol resolution. A file matches if any term occurs in its path or eligible decoded contents. `admin` matches `administrator`; `archive*` includes a literal asterisk. Content matching covers the complete eligible file, not just the returned excerpt.

Order files by the number of **distinct** terms matched in the union of path and contents, descending; ties use inventory path order. Repeating a term or mentioning it many times does not boost that count. This deterministic ordering is a retrieval heuristic, not a finding of architectural importance or task relevance.

`--limit` defaults to 10 and accepts 1..50. `--offset` defaults to 0 and is nonnegative. `matches.total` counts all matching files in the selection. `omitted` counts all matches absent from the page, including preceding pages; `next_offset` is null at the end. An offset past the end returns an empty page with the full omitted count.

Only regular files of at most 262,144 source bytes are text-searched. Decode strict UTF-8 without normalization; NUL-containing or undecodable files remain opaque. Larger files retain inventory identity but are not text-read for retrieval. Their paths can still match. `coverage.gap_counts` and a bounded gap list expose `file_too_large`, `nul_bytes`, and `not_utf8`. An empty UTF-8 file is searched but has no excerpt. An unreadable included input is a failure, never a successful search gap.

## Exact excerpts and connected structure

For a textual match, excerpt up to two lines before and after the first content-matching line. For a path-only match, use the first three lines. Lines are delimited by LF; CR bytes in CRLF stay in the text. `first_content_line` and `matching_lines_total` describe complete content search, while the excerpt is only the first window. No excerpt implies neither an empty file nor absence of behavior.

An excerpt contains exact decoded source text, zero-based half-open `start_byte`/`end_byte`, one-based `start_line`/`end_line` for emitted text, the unclipped `window_end_byte`, and `truncated`. Byte locations refer to original UTF-8 source, not casefolded text or JSON escaping. Returning source slice `[start_byte:end_byte]` reproduces the excerpt bytes. End line denotes the last emitted line; a final LF does not add an empty line. CR-only files are one LF-delimited line.

Clip each window to at most 2,048 UTF-8 bytes without splitting a code point. `--max-bytes` defaults to 8,192 and accepts 128..65,536, shared across the page in rank order. It counts **source text only**, not JSON transport bytes, metadata, or model tokens. A later excerpt can be reduced to a few characters, or become null with `text_status: excerpt_budget_exhausted`. `truncated` shows any per-file or shared-budget clipping. A matching term late in a long line may fall outside the emitted prefix. Use the match location and the host's ordinary file reader for more detail; this increment has no arbitrary line-range operation.

Each selected file retains its path, parent, exact byte count and content ID, filename/extension classification hypotheses, separate path/content match terms, and snapshot-qualified evidence. Ancestor `contains` edges connect selected files back toward the root. These establish containment only: co-occurrence of words in two files is not a call, dependency, permission, or behavior relationship.

The view also returns an inventory outline for the selection, project-wide guidance candidates, configuration document links with unresolved reasons, exclusions, and filesystem boundaries. Guidance is identified by filename; instruction applicability is not established. Knowledge-record text is not interpreted as authenticated intent. Source text is labeled `untrusted_project_data`; this command supplies no secret redaction, prompt-injection filter, or disclosure authorization. Existing host policies govern which included content reaches an external model.

Outline, guidance, document-link, exclusion, boundary, and text-gap lists each show at most 20 entries, with totals and omitted counts. Ancestor edges show at most 200, also with explicit counts. Expand structural lists with `inventory --full`; change search scope, query, limits, or pagination for source matches. Metadata is bounded by counts, not a fixed total-byte budget.

## Identity and freshness

Output is `uir.context.v1`, with `retriever: literal.v1` and the Python Unicode database version in `unicode_version` for reproducing casefold behavior. Its snapshot is the unchanged `inventory.v1` manifest identity. Query, pagination, excerpt budgets, local root, and timestamps do not change source identity. Different queries are views of the same snapshot, not interchangeable retrieval results. Keep selection, retriever, and Unicode compatibility fields alongside excerpts.

For each attempt:

1. Capture the full inventory manifest and local metadata tokens.
2. Read eligible selected files with bounded reads, checking opened/path identities, parent boundaries, and exact content hashes against that manifest. Build matches and excerpts.
3. Capture inventory again. Compare the complete captures, including metadata observations, before returning a view or selection error.

Retry detected changes up to three attempts; then fail with `unstable_inputs`. Read/selection errors are reported only after matching captures, or superseded by a retry if the surrounding inputs changed. No partial detected view or old cache fallback is returned. There is no watcher, persisted retrieval, or cache option.

Success uses `freshness: matching_captures_around_context_reads`, observation start/end, resolved root, and `atomic: false`. This remains an optimistic observation on a trusted local filesystem. Arbitrary malicious swaps, changes restored between observations, or later edits are outside its guarantee; use externally frozen inputs if atomicity is needed. Narrow output does not narrow the input identity or make verification free.

`--expected-snapshot` optionally pins a lowercase `sha256:` identity from inventory or a prior context page. After successful matching capture, a different identity returns `stale_snapshot`; no context page is emitted. Use the pin on continuation and expansion, and retain query/scope explicitly. Without it each request uses fresh current inputs and pages can shift after edits. Restart catches included additions, removals, text, ignore, and configuration changes through full recapture; it restores no source files.

## Outcomes and validation

| Exit | Meaning |
| --- | --- |
| 0 | JSON success on stdout, including zero matches, opaque-file gaps, omissions, unresolved documents, and unknown semantics. No matches means no literal matches in searched coverage. |
| 2 | JSON error on stderr for invalid arguments/scope/configuration/root, unreadable inputs, missing/failed Git, or `stale_snapshot`. No success view. |
| 3 | JSON `unstable_inputs` error on stderr after three failed capture attempts. Retry on settled or frozen inputs. |

Errors after argument parsing use `uir.context.v1`; parser syntax errors retain the existing `uir.inventory.v1` adapter envelope. Inventory error codes remain compatible. No result claims tests passed, software is healthy, a developer approved text, or excluded/unsupported relationships are absent.

`tests/test_context.py` exercises exact byte/line evidence, Unicode/CRLF, path-only matches, deterministic ordering, pagination/pins, bounds, opaque coverage, scope/ignore/configuration changes, nested boundaries, races before and after reads, unreadability, equivalent checkouts, the real CLI, and source preservation. Required Windows/Linux CI runs it before optional crypto installation.

Future retrieval comparison must hold task acceptance, project inputs, model settings, budgets, and failure accounting constant across ordinary file search, this literal view, and optional enrichment. Measure full extraction/verification, retrieval, transport/context tokens, agent work, checking, repair, latency, and review effort. No token savings, semantic coverage, or completed-agent-task improvement is measured here.
