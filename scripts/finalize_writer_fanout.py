#!/usr/bin/env python3
"""Validate, assemble, render, and atomically promote a Writer fan-out batch."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from assemble_writer_results import assemble
from materialize_writer_result import materialize, write_yaml_atomic
from sandbox_workspace import remove_tree_force, verify_workspace
from validate_writer_result import validate_result
from validate_writer_part import validate_part
from writer_task_common import load_json, sha256_file, write_json


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _remove_stage(path: Path, session: Path) -> None:
    if path.exists():
        if not _inside(path, session) or not path.name.startswith(".writer-staging-"):
            raise ValueError(f"Unsafe staging path: {path}")
        shutil.rmtree(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    session = args.session.resolve()
    sessions_root = (root / "tailoring/sessions").resolve()
    if not _inside(session, sessions_root):
        raise SystemExit("Session must be inside tailoring/sessions")
    manifest_path = session / "writer-manifest.json"
    writer_path = session / "writer"
    if not manifest_path.is_file() or writer_path.exists():
        raise SystemExit("Writer manifest is missing or output already exists")
    original_manifest = manifest_path.read_text(encoding="utf-8-sig")
    manifest = json.loads(original_manifest)
    if manifest.get("pipeline") != "resume-writer-fanout" or manifest.get("status") != "pending":
        raise SystemExit("Writer finalization requires a pending fan-out manifest")
    context_path = Path(manifest["snapshots"]["context_pack"]["path"])
    base_path = Path(manifest["snapshots"]["base_resume"]["path"])
    base_source = Path(manifest["source"]["base_resume"]["path"])
    for record in (
        manifest["snapshots"]["context_pack"], manifest["snapshots"]["base_resume"],
        manifest["source"]["base_resume"], manifest["context_builder"]["context_pack_source"],
        manifest["context_builder"]["manifest"], manifest["context_builder"]["claim_snapshot"],
    ):
        path = Path(record["path"])
        if not path.is_file() or sha256_file(path) != record["sha256"]:
            raise SystemExit(f"Writer input changed: {path}")
    context = load_json(context_path)
    import yaml
    base = yaml.safe_load(base_path.read_text(encoding="utf-8-sig"))
    assignments_dir = session / "writer-inputs/assignments"
    results = {}
    for task_id, task in manifest["tasks"].items():
        assignment = Path(task["assignment"]["path"])
        if sha256_file(assignment) != task["assignment"]["sha256"]:
            raise SystemExit(f"Assignment changed: {task_id}")
        verified = verify_workspace(Path(task["sandbox"]), expected_manifest_sha256=task["manifest_sha256"], require_output=True)
        result = load_json(Path(verified["output"]))
        errors = validate_part(result, load_json(assignment), task["assignment"]["sha256"])
        if errors:
            raise SystemExit(f"Invalid Writer part {task_id}: {'; '.join(errors)}")
        results[task_id] = Path(verified["output"])
    if set(results) != set(manifest["tasks"]):
        raise SystemExit("Writer result batch is incomplete")

    stage = session / f".writer-staging-{uuid.uuid4().hex}"
    promoted = False
    try:
        partials = stage / "partials"
        partials.mkdir(parents=True)
        for task_id, source in results.items():
            shutil.copy2(source, partials / f"{task_id}.json")
        result = assemble(assignments_dir, partials, context_path, base_path)
        result_path = stage / "result.json"
        write_json(result_path, result)
        errors = validate_result(
            result, context, base,
            result_context_sha256=sha256_file(context_path),
            result_base_sha256=sha256_file(base_path),
        )
        if errors:
            raise ValueError("Invalid assembled Writer result: " + "; ".join(errors))
        artifacts = {"result": {"path": "result.json", "sha256": sha256_file(result_path)}, "partials": {}}
        for task_id in sorted(results):
            artifacts["partials"][task_id] = {"path": f"partials/{task_id}.json", "sha256": sha256_file(partials / f"{task_id}.json")}
        if result["status"] == "ready":
            yaml_path = stage / "resume.yaml"
            pdf_path = stage / "resume.pdf"
            checks_path = stage / "pdf-checks.json"
            write_yaml_atomic(materialize(result, base), yaml_path)
            rendercv = root / ".venv/Scripts/rendercv.exe"
            subprocess.run([
                str(rendercv), "render", str(yaml_path), "--output-folder", str(stage),
                "--typst-path", "render-temp/resume.typ", "--pdf-path", "resume.pdf",
                "--dont-generate-markdown", "--dont-generate-html", "--dont-generate-png", "--quiet",
            ], check=True)
            render_temp = stage / "render-temp"
            if render_temp.exists():
                shutil.rmtree(render_temp)
            subprocess.run([
                sys.executable, str(root / "qa/resume-qa/scripts/pdf_checks.py"),
                "--resume", str(pdf_path), "--output", str(checks_path),
            ], check=True)
            checks = load_json(checks_path)
            failed = [name for name, value in checks["checks"].items() if not value["passed"]]
            if failed:
                raise ValueError("Writer PDF failed checks: " + ", ".join(failed))
            artifacts.update({
                "resume_yaml": {"path": "resume.yaml", "sha256": sha256_file(yaml_path)},
                "resume_pdf": {"path": "resume.pdf", "sha256": sha256_file(pdf_path)},
                "pdf_checks": {"path": "pdf-checks.json", "sha256": sha256_file(checks_path)},
            })
            preflight = "passed"
        else:
            artifacts.update({"resume_yaml": None, "resume_pdf": None, "pdf_checks": None})
            preflight = "not-applicable"
        if sha256_file(base_source) != manifest["source"]["base_resume"]["sha256"]:
            raise ValueError("Canonical base resume changed during finalization")
        completed = datetime.now(timezone.utc).isoformat()
        receipt = {
            "schema_version": 2,
            "pipeline": "resume-writer-fanout",
            "session_id": manifest["session_id"],
            "status": result["status"],
            "completed_at": completed,
            "inputs": result["inputs"],
            "source_guard": {"base_resume_path": str(base_source), "base_resume_sha256": sha256_file(base_source), "unchanged": True},
            "checks": {"writer_parts": "passed", "deterministic_assembly": "passed", "writer_result": "passed", "pdf_preflight": preflight},
            "artifacts": artifacts,
        }
        write_json(stage / "receipt.json", receipt)
        stage.replace(writer_path)
        promoted = True
        manifest["status"] = result["status"]
        manifest["completed_at"] = completed
        manifest["promotion"] = {"path": str(writer_path), "result_sha256": sha256_file(writer_path / "result.json"), "promoted_at": completed}
        manifest["cleanup"] = {"status": "completed", "completed_at": completed}
        for task in manifest["tasks"].values():
            task["status"] = "validated"
        write_json(manifest_path, manifest)
        sandbox_root = Path(manifest["sandbox_root"]).resolve()
        if sandbox_root.anchor == str(sandbox_root) or _inside(root, sandbox_root) or _inside(session, sandbox_root):
            raise ValueError(f"Unsafe sandbox cleanup target: {sandbox_root}")
        expected_children = {Path(task["sandbox"]).resolve() for task in manifest["tasks"].values()}
        actual_children = {path.resolve() for path in sandbox_root.iterdir()}
        if actual_children != expected_children:
            raise ValueError("Writer sandbox root contains unexpected entries")
        remove_tree_force(sandbox_root)
    except Exception:
        if promoted and writer_path.exists():
            shutil.rmtree(writer_path)
            manifest_path.write_text(original_manifest, encoding="utf-8")
        _remove_stage(stage, session)
        raise
    print(writer_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
