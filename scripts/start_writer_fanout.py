#!/usr/bin/env python3
"""Create isolated experience, project, and skills Writer sandboxes."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from prepare_writer_assignments import build_assignments
from sandbox_workspace import create_workspace
from validate_context_artifact import validate_context_pack
from context_common import load_claims
from writer_task_common import sha256_file, write_json


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--sandbox-root", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sessions_root = (root / "tailoring/sessions").resolve()
    session = args.session.resolve()
    if not _inside(session, sessions_root):
        raise SystemExit("Session must be inside tailoring/sessions")
    session_id = session.name
    context_manifest_path = session / "manifest.json"
    context_path = session / "output/context-pack.json"
    base_source = root / "resumes/vincenzo-rosciano-one-page.yaml"
    for path in (context_manifest_path, context_path, base_source):
        if not path.is_file():
            raise SystemExit(f"Missing required Writer input: {path}")
    context_manifest = json.loads(context_manifest_path.read_text(encoding="utf-8-sig"))
    if context_manifest.get("pipeline") != "resume-context-builder" or context_manifest.get("status") != "completed":
        raise SystemExit("Writer requires a completed Context Builder session")
    promoted = context_manifest.get("promotion", {}).get("context_pack", {})
    if Path(promoted.get("path", "")).resolve() != context_path or promoted.get("sha256") != sha256_file(context_path):
        raise SystemExit("Context pack disagrees with the Context Builder manifest")
    claim_snapshot = Path(context_manifest["snapshots"]["claim_index"]["path"]).resolve()
    if sha256_file(claim_snapshot) != context_manifest["snapshots"]["claim_index"]["sha256"]:
        raise SystemExit("Context Builder claim snapshot changed")
    context = json.loads(context_path.read_text(encoding="utf-8-sig"))
    context_errors = validate_context_pack(context, load_claims(claim_snapshot))
    if context_errors:
        raise SystemExit("Invalid context pack: " + "; ".join(context_errors))
    base = yaml.safe_load(base_source.read_text(encoding="utf-8-sig"))

    writer_inputs = session / "writer-inputs"
    writer_manifest_path = session / "writer-manifest.json"
    prompt_path = session / "writer-task-prompts.md"
    writer_output = session / "writer"
    for reserved in (writer_inputs, writer_manifest_path, prompt_path, writer_output):
        if reserved.exists():
            raise SystemExit(f"Writer state already exists: {reserved}")
    sandbox_root = (args.sandbox_root or (root / ".sandbox/writer" / session_id)).resolve()
    if sandbox_root.anchor == str(sandbox_root) or _inside(root, sandbox_root) or _inside(session, sandbox_root) or _inside(sandbox_root, session):
        raise SystemExit(f"Unsafe Writer sandbox root: {sandbox_root}")
    if sandbox_root.exists():
        raise SystemExit(f"Writer sandbox already exists: {sandbox_root}")

    try:
        writer_inputs.mkdir(parents=True)
        context_snapshot = writer_inputs / "context-pack.json"
        base_snapshot = writer_inputs / "base-resume.yaml"
        shutil.copy2(context_path, context_snapshot)
        shutil.copy2(base_source, base_snapshot)
        assignments_dir = writer_inputs / "assignments"
        assignments_dir.mkdir()
        assignments = build_assignments(context, base)
        for task_id, assignment in assignments.items():
            write_json(assignments_dir / f"{task_id}.json", assignment)
        for path in writer_inputs.rglob("*"):
            if path.is_file():
                path.chmod(path.stat().st_mode & ~0o222)

        skill_for = {
            "experience": root / ".codex/skills/write-xyz-resume-bullets",
            "projects": root / ".codex/skills/select-resume-projects",
            "technical-skills": root / ".codex/skills/select-resume-skills",
        }
        tasks = {}
        prompt_sections = [
            "# Isolated resume Writer tasks",
            "",
            "Run every section below in a different fresh top-level Codex task. Never use subagents, forks, reused tasks, or parent-chat context.",
            "",
        ]
        for task_id, assignment in assignments.items():
            assignment_path = assignments_dir / f"{task_id}.json"
            sandbox = sandbox_root / task_id
            skill = skill_for[assignment["task"]["kind"]]
            created = create_workspace(
                sandbox,
                pipeline="resume-writer-fanout",
                session_id=session_id,
                task_id=task_id,
                skill_source=skill,
                inputs=[(assignment_path, Path("assignment.json"))],
                output_name="result.json",
                promote_to=writer_output / "partials" / f"{task_id}.json",
                network="deny",
            )
            tasks[task_id] = {
                "kind": assignment["task"]["kind"],
                "status": "pending",
                "assignment": {"path": str(assignment_path), "sha256": sha256_file(assignment_path)},
                "sandbox": str(sandbox),
                "manifest_sha256": created["manifest_sha256"],
                "output": str(sandbox / "outbox/result.json"),
            }
            prompt_sections.extend([
                f"## {task_id}", "",
                f"Open and follow `{sandbox / 'skill/SKILL.md'}`. Treat `{sandbox}` as the complete workspace and do not read outside it.", "",
                f"Read only `{sandbox / 'inputs/assignment.json'}` and files inside `{sandbox / 'skill'}`.", "",
                f"Copy this exact `assignment_sha256`: `{sha256_file(assignment_path)}`.", "",
                f"Write only `{sandbox / 'outbox/result.json'}`. Return only `completed` and the output path.", "",
            ])
        manifest = {
            "schema_version": 2,
            "pipeline": "resume-writer-fanout",
            "session_id": session_id,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "context_builder": {
                "manifest": {"path": str(context_manifest_path), "sha256": sha256_file(context_manifest_path)},
                "context_pack_source": {"path": str(context_path), "sha256": sha256_file(context_path)},
                "claim_snapshot": {"path": str(claim_snapshot), "sha256": sha256_file(claim_snapshot)},
            },
            "source": {"base_resume": {"path": str(base_source), "sha256": sha256_file(base_source)}},
            "snapshots": {
                "context_pack": {"path": str(context_snapshot), "sha256": sha256_file(context_snapshot)},
                "base_resume": {"path": str(base_snapshot), "sha256": sha256_file(base_snapshot)},
            },
            "sandbox_root": str(sandbox_root),
            "tasks": tasks,
            "promotion": None,
            "cleanup": {"status": "pending", "completed_at": None},
        }
        write_json(writer_manifest_path, manifest)
        prompt_path.write_text("\n".join(prompt_sections), encoding="utf-8")
    except Exception:
        if sandbox_root.exists():
            shutil.rmtree(sandbox_root, onerror=lambda func, path, _: (os.chmod(path, 0o700), func(path)))
        if writer_inputs.exists():
            shutil.rmtree(writer_inputs, onerror=lambda func, path, _: (os.chmod(path, 0o700), func(path)))
        for path in (writer_manifest_path, prompt_path):
            path.unlink(missing_ok=True)
        raise
    print(prompt_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
