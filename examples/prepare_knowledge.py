"""Fictional external proposal through the real read-only preparation CLI."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from universal_ir.inventory import canonical, identity, inventory
from universal_ir.knowledge import inspect_knowledge, source_projection


def run_demo():
    tool = Path(__file__).resolve().parents[1]
    root = tool / "examples/fixtures/knowledge-project"
    before = inspect_knowledge(root, selected_id="retention", full=True)
    heads = before["groups"]["entries"][0]["heads"]
    manifest = inventory(root)["manifest"]
    path = "README.md"
    data = (root / path).read_bytes()
    body = {"id": "retention", "category": "requirement", "text": "Retain archived tasks for 60 days.",
            "scope": ["."], "origin": {"kind": "ai_interpretation", "host_id": "fictional-agent",
            "method": "scripted proposal", "assumptions": ["60 days is a proposal, not an established requirement."]},
            "input_id": identity(source_projection(manifest, ["."])),
            "evidence": [{"kind": "file", "path": path, "content_id": "sha256:" + hashlib.sha256(data).hexdigest()}],
            "supersedes": heads, "state": "active"}
    unsigned = {"format": "uir.knowledge.v1", "project_id": before["project_id"], "body": body}
    candidate = dict(unsigned, record_id=identity(unsigned))
    with TemporaryDirectory(prefix="uir-fictional-preparation-") as scratch:
        candidate_path = Path(scratch) / "candidate.json"
        candidate_path.write_bytes(canonical(candidate) + b"\n")
        process = subprocess.run([sys.executable, "-B", "-m", "universal_ir", "prepare-knowledge", str(root),
                                  str(candidate_path), "--expected-snapshot", before["snapshot"]],
                                 cwd=tool, capture_output=True, check=True)
        prepared = json.loads(process.stdout)
    after = inspect_knowledge(root, selected_id="retention", full=True)
    if before["snapshot"] != after["snapshot"] or before["records"] != after["records"] or before["groups"] != after["groups"]:
        raise RuntimeError("Candidate preparation changed the fictional project.")
    if prepared["candidate"]["already_included"] or prepared["transition"]["would_leave_competing_heads"]:
        raise RuntimeError("Fictional proposal did not produce the expected unpersisted structural preview.")
    return {"format": "uir.fictional-preparation-demo.v1", "status": "ok", "preparation": prepared,
            "stored_heads_unchanged": heads, "project_writes": False,
            "real_user_approval": "not_demonstrated", "accepted_resolution": "not_established"}


if __name__ == "__main__":
    print(json.dumps(run_demo(), ensure_ascii=True, indent=2, allow_nan=False))
