# Try the local inventory prototype

This is a working read-only workflow. It helps your existing coding agent navigate files and linked guidance. It does not build or edit an application, infer its purpose, or validate software behavior.

## First overview

Install Python 3.12+ and Git. Open a terminal in the Universal IR checkout, then point the command at your own project:

~~~sh
python -m universal_ir inventory /path/to/your/project
~~~

On this repository's Windows development setup:

~~~powershell
.venv\Scripts\python -m universal_ir inventory "C:\path\to\your\project"
~~~

The project can be a Git checkout or an ordinary folder. Nothing is initialized or written there. The command returns JSON with a content snapshot ID, observation boundary, file and directory counts, language hypotheses, guidance candidates, exclusions, unknown semantics, and up to 20 entries linked by containment.

Ask your coding agent:

> Use the local Universal IR inventory command to map this project. Expand relevant folders and read the identified guidance and source yourself. Keep language guesses, inferred purpose, and established file relationships distinct. Show exclusions and unknown behavior before making a change.

Your agent must have permission to run terminal tools and know the Universal IR checkout location. Installation into an agent and automatic invocation are not implemented. Authentication and model costs remain with your existing agent.

## Expand relevant detail

Suppose the overview identifies a `services` directory:

~~~sh
python -m universal_ir inventory /path/to/your/project --path services --limit 10
python -m universal_ir inventory /path/to/your/project --path services --limit 10 --offset 10
~~~

Use the returned `next_offset` to continue. Every call rechecks the entire included project; selection bounds output, not scan cost. A snapshot change between pages means they describe different inputs. Do not combine them as one unchanged view. Exclusions and boundaries remain explicit, and file containment does not imply call or data-flow relationships.

## Add optional project-owned guidance links

A developer may create `.uir/config/project.json` through the project's ordinary review workflow:

~~~json
{
  "version": 1,
  "project_id": "my-project",
  "exclude": ["vendor"],
  "documents": ["README.md", "docs/architecture.md"]
}
~~~

Run inventory again. The overview identifies this project and the links have source evidence. Missing or excluded documents are unresolved with a reason. Linked documents retain their existing location and authority; the tool does not duplicate or interpret their declarations. Keep `.uir/cache/` ignored if the host uses it for local exports.

## Stop, edit, and compare

Save a full inventory outside the selected project. On a POSIX shell:

~~~sh
python -m universal_ir inventory /path/to/your/project --full > /outside/project/before.json
~~~

On Windows, save UTF-8 without a BOM; Windows PowerShell's default redirection encoding is unsuitable for this JSON contract. From the Universal IR checkout, this Python host snippet works across platforms after replacing the project and export paths:

~~~python
from pathlib import Path
import subprocess
import sys

with Path("C:/existing-export-folder/before.json").open("wb") as output:
    subprocess.run(
        [sys.executable, "-m", "universal_ir", "inventory",
         "C:/path/to/your/project", "--full"],
        stdout=output, check=True,
    )
~~~

Make ordinary source edits, add a file, or remove one. Later, run:

~~~sh
python -m universal_ir inventory /path/to/your/project --baseline /outside/project/before.json
~~~

The tool reconstructs current inputs and reports added, removed, or changed inventory entries and configuration/control changes. A removed entry might be newly excluded rather than deleted. It preserves source bytes and never restores the saved state. No watcher or running service is needed between calls.

An edited, malformed, incomplete, or incompatible baseline produces an error rather than a current view. Byte integrity does not establish producer trust. A valid baseline is used only for comparison; current extraction is always local.

## Keep disposable local snapshots

Choose a local cache outside your project and pass the same path on later calls:

~~~sh
python -m universal_ir inventory /path/to/your/project --cache-dir /outside/project/cache
~~~

For example, when your Windows project is on the Desktop, use a separate cache under your local application data:

~~~powershell
.venv\Scripts\python -m universal_ir inventory "C:\path\to\your\project" --cache-dir "$env:LOCALAPPDATA\universal-ir"
~~~

The first call reports `cache.lookup: miss` and `cache.publication: stored`. An unchanged later call reports `hit` and `reused`, with a new local observation. Edit source while the tool is stopped and run again: changed inputs select a new snapshot; the tool never restores old source. It fully rereads files even on a hit, so this establishes persistent state and recovery rather than faster scanning.

Only manifests are stored beneath the reserved `uir-inventory-cache-v1/` namespace. Missing or damaged artifacts are rebuilt. If storage is unavailable, exit 0 can still contain a fresh view with `cache.diagnostic`; a host requiring persistence must inspect that result. Source capture failures still return exit 2 or 3 and cannot fall back to an old snapshot. There is no background watcher.

Do not point this flag inside the selected project, including `.uir/cache/`: this increment rejects that location without creating it. Committed configuration and future durable knowledge still travel in `.uir/`; local cache is disposable and has no authenticated producer or remote sharing. Historical artifacts accumulate until the host removes them. See the [cache contract](../docs/specs/local-cache-v1.md) for compatibility, interruption, concurrency, and storage limits.

## Harness integration and limits

A custom harness can invoke the command as a subprocess, parse stdout on exit 0, and parse stderr diagnostics on exit 2 or 3. Enforce your own tool permissions and budget. Exit 3 means detected input instability; retry when files settle. Successful output reports consecutive matching captures, not an atomic filesystem snapshot or ongoing monitoring.

There are no model calls in inventory. Your agent can interpret the evidence using its existing model, but persistence of conversational knowledge and authenticated developer provenance are future increments. GLiNER and Jev are optional evaluation candidates for later enrichment and retrieval, with no integration here.

See the [version-1 contract](../docs/specs/local-inventory-v1.md) for exact scope, identity, configuration, ignore behavior, output bounds, failure meanings, and remaining gates.
