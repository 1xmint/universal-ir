# Local inventory cost baseline

This measures the current inventory/storage core, not completed AI coding tasks. It supplies an early correctness and cost baseline before incremental extraction. There are no performance thresholds or token-saving claims.

## Reproduce

With Python 3.12+ and Git, run from the checkout:

~~~sh
python -B scripts/measure_inventory.py --repetitions 3
python -B scripts/measure_inventory.py --root /path/to/project --repetitions 3
~~~

On Windows use `.venv\Scripts\python` in place of `python`. The default creates a fixed temporary non-Git fixture: 100 opaque mixed-extension files in ten directories, README/AGENTS guidance, `.gitignore`, and an excluded vendor directory. These are inventory inputs, not executable application behavior. The 103 included files contain 80,057 bytes. No application scripts or models run.

Each trial launches three fresh Python workers in fixed order: uncached, cold tool-cache, warm tool-cache. Workers use the same inventory/cache/view core as the product CLI. Each trial has a new external temporary cache; the warm worker uses the cold worker's artifact. An optional existing project is read-only. Temporary storage is outside that project and removed after the run. A selected root containing the system temporary directory is rejected before scratch creation.

Save stdout as UTF-8 bytes for inspection; in Windows PowerShell, use a binary subprocess export like the [inventory example](../examples/local-inventory.md#stop-edit-and-compare) rather than legacy default redirection encoding. Reports never include source contents. Temporary artifact paths are replaced with `<temporary workspace>` in report metadata; measured context sizes use the actual worker output before that replacement.

## What the report means

`uir.inventory-cost.v1` records Python/platform, UTC capture time, content identities of the tool's Python sources, raw samples, all comparison outcomes, and median successful-worker wall times. Source hashes are checked before/after the run; a mismatch prevents successful benchmark completion. Keep the tool checkout unchanged during a run; this is an optimistic check, not an atomic build provenance system.

| Measurement | Boundary |
| --- | --- |
| `inventory_with_freshness_ns` | Full local inventory, including both capture passes, retries, and isolated Git ignore evaluation. Extraction and freshness verification are not separately instrumented. |
| `cache_total_ns` | Optional lookup/validation/publication together; zero when storage is not requested. Finer read/write breakdown is unmeasured. |
| `view_ns`, `json_encoding_ns` | Default bounded view construction and encoding with the product CLI's JSON style. |
| `worker_wall_ns` | Timed core work and measurement bookkeeping after worker imports. |
| `process_wall_ns` | Parent-observed worker startup, core work, metric-report transport, and process completion. It is not end-to-end product CLI graph-output transport or agent latency. |
| `worker_cpu_ns_excluding_git` | CPU consumed by that Python worker, excluding Git child CPU and parent CPU; not total compute. |
| `context_json_bytes` | Encoded default inventory view size, including cache metadata where requested. Bytes are not model tokens. |
| `artifact_bytes` | One selected snapshot's stored size, not total historical storage or transfer. |
| Snapshot/identity/cache outcomes | Digest self-consistency, matching inputs across modes, cold miss/store, and warm hit/reuse. They do not prove semantic correctness or completed software changes. |

Cold means empty **tool** cache. The script does not flush OS filesystem caches or alternate mode order, so order and filesystem warmth can influence results. Platform, Git, source versions, workload, and raw attempts remain visible. Three trials on one machine cannot establish a broadly applicable latency or improvement.

Capture errors, worker failures/timeouts, changed inputs, and failed cache expectations remain in the report. Exit 0 requires all trial comparisons to match and tool sources to remain unchanged; exit 1 preserves an unsuccessful comparison report; exit 2 reports invalid setup/arguments on stderr. Summary `successful_samples` counts successful worker inventories, including a worker from an otherwise incomparable trial; inspect raw trial outcomes before comparing medians. No failed attempt is silently retried or dropped.

Model calls and network transfer are zero for this tool's local operations. Model tokens, agent task correctness, repair attempts, review effort, Git child CPU, peak memory, and detailed phase separation are explicitly unmeasured. The later [whole-task comparison](../ROADMAP.md#4-measure-the-benefit) and [sharing experiment](../docs/specs/project-coherence.md#future-cost-comparison-protocol) remain open.

## Recorded Windows run

The [raw three-trial report](results/local-inventory-windows.json) was recorded on October 2, 2026 UTC (October 1 locally), with Python 3.14.4, Git 2.53.0, and Windows build 19045. The report's tool-source ID identifies the code used, including the then-uncommitted measurement script; it does not mislabel that code as the preceding Git commit.

| Mode | Median worker-process wall time | Successful samples |
| --- | --- | --- |
| Uncached | 1.070 seconds | 3 |
| Cold tool-cache | 1.058 seconds | 3 |
| Warm tool-cache | 1.061 seconds | 3 |

All nine samples had matching inventory IDs and expected storage states. The snapshot artifact was 17,774 bytes; the first trial's default context JSON was about 15.9 KB without cache metadata and 16.2 KB with it. Use the raw report for exact values.

These timings are close, and the experiment supports no general speedup claim. Warm requests still perform full source verification. The benchmark's failure behavior and report arithmetic are tested in Windows/Linux CI; that does not reproduce this Windows timing on every runner. Expand corpora, record finer costs, and use fair task-level comparisons before selecting optimizations.
