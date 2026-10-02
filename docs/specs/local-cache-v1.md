# Verified local snapshot storage

**Status:** Implemented prototype increment under [decision 0008](../design/0008-verified-local-snapshots.md). This extends [local inventory version 1](local-inventory-v1.md), not executable IR or shared snapshot import.

## Operation and ownership

From the tool checkout, opt into storage with Python 3.12+ and Git:

~~~sh
python -m universal_ir inventory /path/to/project --cache-dir /outside/project/cache
~~~

The host selects an ordinary local directory outside the selected project. It may exist or be created. The tool owns only the reserved `uir-inventory-cache-v1/` namespace beneath it. That namespace cannot contain the inventoried project. Existing non-directory parents, links, junctions, and non-regular artifacts are rejected without overwriting them. Cache errors leave the fresh inventory usable with an explicit diagnostic.

Without `--cache-dir`, no persistent snapshot storage is attempted and no `cache` field is added. With the flag, only the specified external cache is written. Application files, `.uir/` metadata, and Git state remain untouched. Python's ordinary tool-checkout bytecode behavior still applies; use `python -B` when needed. Project configuration and future durable knowledge still belong in committed `.uir/` records. This prototype does not yet create or interpret conversational knowledge.

This external placement refines the broader specification's proposed `.uir/cache/` layout for this increment. Inventory version 1 includes directory membership and omission paths in identity; creating cache ancestors inside a project could change that identity. The flag therefore rejects in-project storage even if that location would be ignored. Host-managed baseline exports can still use the inventory contract's excluded locations. Future repository-local storage needs an explicit extraction compatibility decision.

## Contents and compatibility

Each accepted snapshot has one artifact named `<64-character snapshot digest>.json`. The exact envelope fields are `format`, `snapshot`, and `manifest`; format is `uir.local-cache.v1`. The manifest is the full inventory manifest, including scope/configuration, control hashes, input identities, boundaries, omissions, and extractor/ignore-engine versions. Store canonical UTF-8 JSON followed by LF. No timestamps, absolute source paths, developer attribution, views, source bytes, model interpretations, or mutable latest pointer are stored.

Compatible identical inputs may reuse an artifact across different checkouts. Each result retains the new invocation's local root and observation times. Different relevant inputs or extraction versions identify different artifacts. An old artifact's mere presence never makes a newer source revision known or remotely validated. Artifacts are not automatically committed, downloaded, or uploaded.

Lookup is by the **freshly computed** snapshot ID. Validate strict JSON, exact envelope fields, format, digest, and canonical equality with the freshly established manifest. Bound the cache read to twice the expected canonical envelope byte length plus 4,096 bytes; larger files are corrupt. This allows modest formatting differences while preventing an arbitrary cache file from driving unbounded reads. A self-consistent digest or self-asserted producer identity cannot replace local verification. There is no authenticated producer or shared-cache trust protocol here.

Different extractor, ignore-engine, configuration, or source contents normally produce a miss at a different ID; older artifacts remain. An unsupported cache-envelope version found at the requested version-1 location is incompatible and reconstructed there. Malformed or mismatching regular artifacts are corrupt and reconstructed there. Accepted valid artifacts have immutable meaning; repair replaces invalid bytes, not a prior accepted source version.

## Freshness and publication

1. Run the existing full two-pass inventory and bounded retry protocol against current source.
2. Validate view arguments and any explicit baseline comparison before attempting cache writes.
3. Look up and verify the artifact for those current facts. Reuse only an exact match.
4. On miss, corruption, or incompatibility, write a complete replacement to a uniquely created temporary file in the same cache namespace, flush and synchronize it, then replace the artifact name.
5. Return current local observation evidence and separate cache lookup/publication results.

All included contents are reread on every request. Restoring a file's size or modification time cannot turn changed bytes into a hit. Restart detects additions, deletions, changed configuration, and changed ignore controls through the same local capture. There is no watcher while running or stopped, metadata-only freshness shortcut, incremental invalidation, or reduced extraction-cost claim.

Freshness is still `verified_consecutive_captures`, with `atomic: false`. Cache lookup and publication occur after that observation; they do not extend it to cover later source changes. Local capture failure returns the inventory error and never serves an older cache entry. Previously returned snapshots remain historical evidence, not live state.

Successful file replacement publishes a whole artifact on supported ordinary local filesystems. A caught interruption cleans only that invocation's temporary file where possible. A process killed before replacement can leave a `.pending-*.tmp` file; later calls never treat it as a snapshot or delete other runs' temporary files. File synchronization is not a promise of directory durability through every power failure. Network/distributed filesystem guarantees are outside this increment. These limits follow the [Python file-replacement interface](https://docs.python.org/3/library/os.html#os.replace) and [temporary-file interface](https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp).

Concurrent identical writers publish identical canonical contents. Different input IDs use different artifacts, so a delayed older capture cannot overwrite a newer capture's artifact or move a latest pointer backwards. This does not coordinate application source edits or provide a live collaboration service. Path checks assume the same trusted local filesystem as inventory; they are not a sandbox against malicious concurrent path swaps.

Before replacement, a writer accepts an identical completed artifact left by another writer. It leaves those bytes in place. Windows access/sharing/lock errors (5, 32, 33) during this publication check or replacement allow at most four attempts, with three 50 ms pauses. Persistent failure remains an explicit cache diagnostic alongside the fresh view; it never authorizes stale fallback. Other errors are not retried by this protocol.

## Results and failure meanings

With the flag, successful inventory output gains a `cache` object:

~~~json
{
  "format": "uir.local-cache.v1",
  "lookup": "hit",
  "publication": "reused",
  "verification": "full_local_capture",
  "artifact": "/outside/project/cache/uir-inventory-cache-v1/<digest>.json"
}
~~~

The example's artifact path is explanatory, not an actual digest. `artifact` is omitted when preparation cannot establish a location. The fields remain outside snapshot identity.

| Situation | Lookup | Publication | Outcome |
| --- | --- | --- | --- |
| No artifact for current facts | `miss` | `stored` | Fresh local manifest persisted. |
| Artifact matches fresh facts | `hit` | `reused` | Verified manifest reused with new local observation. |
| Malformed, oversized, or mismatching regular file | `corrupt` | `stored` | Fresh facts replace invalid cache bytes. |
| Unsupported envelope at requested location | `incompatible` | `stored` | Fresh version-1 artifact reconstructed. |
| Invalid location or unavailable cache read | `unavailable` | `not_attempted` | Fresh local view, no attempted publication. |
| Publication fails after a miss/rejection | Prior lookup result | `unavailable` | Fresh local view; publication failure reported. |
| Local capture, selection, or baseline fails | No cache object | No attempt | Inventory exit 2 or 3; no successful view or cache write. |

Cache unavailability adds `diagnostic` with `code: cache_unavailable`, `phase` (`prepare`, `lookup`, or `publication`), and a message. It does not change a valid local inventory's exit 0 into a failure or silently claim storage succeeded. A host that requires persistence must inspect publication status. Rejected unsafe paths are treated as unavailable optional storage, not silently replaced with another directory.

## Acceptance and cost boundaries

The Windows/Linux suite checks cold and warm runs, separate-process restart, full byte verification despite restored metadata, add/delete/configuration/ignore changes, equivalent checkouts, corrupt/incompatible/false artifacts, missing files, interrupted replace/flush, unavailable storage, directory/link/junction boundaries, abandoned temporary files, concurrent writers, and late older publication. It also checks that source failure cannot fall back to cache and invalid requests cannot create cache files.

Storage is disposable. Deleting the reserved namespace while the tool is stopped permits reconstruction on the next call; do not delete project configuration or durable knowledge. Automated retention, pruning, storage quotas, encrypted storage, snapshot exchange, and remote awareness remain future work. Historical artifacts accumulate until the host removes them.

Before optimization, measure uncached, cold-cache, and warm-cache requests separately. Count deterministic extraction, freshness verification, artifact validation/read/write, bytes stored, wall latency, output context size, and correctness. Model calls are zero here; model interpretation and completed agent-task tokens must be measured separately when integrated. This increment establishes persistent verified state and recovery, not demonstrated speed or token savings. Keep the broader [sharing cost protocol](project-coherence.md#future-cost-comparison-protocol) and full-task roadmap experiment separate.
