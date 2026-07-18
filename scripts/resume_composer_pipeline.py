#!/usr/bin/env python3
"""Orchestrate advisory scouts and one global Resume Composer."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import pypdf
import yaml

from sandbox_workspace import create_workspace, remove_tree_force, verify_workspace


ROOT = Path(__file__).resolve().parents[1]
SESSIONS_ROOT = (ROOT / "tailoring/sessions").resolve()
DEFAULT_BASE = ROOT / "resumes/vincenzo-rosciano-one-page.yaml"
SCOUT_SKILL = ROOT / ".codex/skills/scout-resume-evidence"
COMPOSER_SKILL = ROOT / ".codex/skills/compose-tailored-resume"
RENDERCV = ROOT / ".venv/Scripts/rendercv.exe"
PDF_CHECKS = ROOT / "qa/resume-qa/scripts/pdf_checks.py"
JOB_VALIDATOR = ROOT / "qa/resume-qa/scripts/validate_job_intake.py"
JOB_RENDERER = ROOT / "qa/resume-qa/scripts/render_job_description.py"
RETRIEVER = ROOT / "scripts/retrieve_claims.py"
CLAIM_TOOL = ROOT / "scripts/knowledge_claims.py"
SESSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
STRONG = re.compile(r"\*\*|__|<\s*/?\s*(?:strong|b)(?:\s+[^<>]*)?\s*>", re.I)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def run(command: list[str | Path]) -> None:
    subprocess.run([str(value) for value in command], check=True)


def inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def safe_session(path: Path) -> Path:
    resolved = path.resolve()
    if not inside(resolved, SESSIONS_ROOT):
        raise ValueError("Session must be inside tailoring/sessions")
    return resolved


def safe_sandbox_root(path: Path, session: Path) -> Path:
    resolved = path.resolve()
    if (
        resolved == Path(resolved.anchor)
        or resolved == ROOT.resolve()
        or inside(ROOT, resolved)
        or resolved == session
        or inside(session, resolved)
        or inside(resolved, session)
    ):
        raise ValueError(f"Unsafe sandbox root: {resolved}")
    return resolved


def remove_if_safe(path: Path, parent: Path) -> None:
    if path.exists():
        if not inside(path, parent):
            raise ValueError(f"Unsafe cleanup target: {path}")
        remove_tree_force(path)


def set_read_only_tree(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            path.chmod(path.stat().st_mode & ~0o222)


def source_markdown() -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = {}
    for domain in ("experience", "projects"):
        folder = ROOT / "knowledge-base" / domain
        files = [path for path in sorted(folder.glob("*.md")) if path.name.casefold() != "readme.md"]
        if not files:
            raise ValueError(f"No canonical Markdown found in {folder}")
        result[domain] = files
    return result


def relative_source(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def job_identity(intake: dict[str, Any]) -> str:
    job = intake.get("job", {})
    label = f"{job.get('company', 'job')}-{job.get('title', 'resume')}".lower()
    return re.sub(r"[^a-z0-9]+", "-", label).strip("-") or "resume"


def retrieval_hints(candidate_pool: dict[str, Any], domain: str) -> list[dict[str, Any]]:
    prefix = f"knowledge-base/{domain}/"
    by_source: dict[str, dict[str, Any]] = {}
    for criterion in candidate_pool.get("criteria", []):
        criterion_id = criterion.get("id")
        for candidate in [*criterion.get("candidates", []), *criterion.get("narrative_candidates", [])]:
            source = candidate.get("source_file")
            if not isinstance(source, str) or not source.startswith(prefix):
                continue
            row = by_source.setdefault(source, {"source_file": source, "maximum_score": 0.0, "criterion_ids": []})
            row["maximum_score"] = max(float(row["maximum_score"]), float(candidate.get("score", 0)))
            if isinstance(criterion_id, str) and criterion_id not in row["criterion_ids"]:
                row["criterion_ids"].append(criterion_id)
    return sorted(by_source.values(), key=lambda item: (-item["maximum_score"], item["source_file"]))


def start(args: argparse.Namespace) -> Path:
    intake_source = args.job_intake.resolve()
    base_source = args.base_resume.resolve()
    if not intake_source.is_file() or not base_source.is_file():
        raise ValueError("Job intake and baseline resume must exist")
    run([sys.executable, JOB_VALIDATOR, intake_source])
    run([sys.executable, CLAIM_TOOL, "check", "--root", ROOT])
    intake = load_json(intake_source)
    session_id = args.session_id or f"{datetime.now():%Y%m%d-%H%M%S}-{job_identity(intake)}"
    if not SESSION_RE.fullmatch(session_id):
        raise ValueError("Session ID contains unsupported characters")
    session = SESSIONS_ROOT / session_id
    if session.exists():
        raise ValueError(f"Session already exists: {session}")
    sandbox_root = safe_sandbox_root(
        args.sandbox_root.resolve() if args.sandbox_root else ROOT / ".sandbox/tailoring" / session_id,
        session,
    )
    if sandbox_root.exists():
        raise ValueError(f"Sandbox root already exists: {sandbox_root}")

    try:
        inputs = session / "inputs"
        inputs.mkdir(parents=True)
        intake_copy = inputs / "job-intake.json"
        job_copy = inputs / "job-description.md"
        base_copy = inputs / "base-resume.yaml"
        candidate_copy = inputs / "candidate-pool.json"
        shutil.copy2(intake_source, intake_copy)
        shutil.copy2(base_source, base_copy)
        run([sys.executable, JOB_RENDERER, "--input", intake_copy, "--output", job_copy])
        run([sys.executable, RETRIEVER, "--job-intake", intake_copy, "--output", candidate_copy, "--root", ROOT])
        candidate_pool = load_json(candidate_copy)

        knowledge_rows: list[dict[str, str]] = []
        domains = source_markdown()
        for files in domains.values():
            for source in files:
                relative = relative_source(source)
                destination = inputs / Path(*PurePosixPath(relative).parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                knowledge_rows.append({
                    "path": relative,
                    "sha256": sha256_file(destination),
                    "source": str(source.resolve()),
                })
        knowledge_manifest = {
            "schema_version": 1,
            "sources": sorted(knowledge_rows, key=lambda item: item["path"]),
        }
        knowledge_manifest_path = inputs / "knowledge-manifest.json"
        write_json(knowledge_manifest_path, knowledge_manifest)

        assignments_dir = inputs / "scout-assignments"
        assignments_dir.mkdir()
        sandbox_scout_root = sandbox_root / "scouts"
        tasks: dict[str, Any] = {}
        prompt_lines = [
            "# Advisory scout tasks",
            "",
            "Create every task below as a new top-level Codex task with model `gpt-5.6-terra` and reasoning `xhigh`.",
            "Never use subagents, forks, reused tasks, or parent-chat context. Launch both before reading either result.",
            "",
        ]
        for domain, files in domains.items():
            task_id = f"{domain}-scout"
            assignment_path = assignments_dir / f"{task_id}.json"
            assignment = {
                "schema_version": 1,
                "assignment_id": domain,
                "domain": domain,
                "job_sha256": sha256_file(job_copy),
                "knowledge_manifest_sha256": sha256_file(knowledge_manifest_path),
                "source_files": [relative_source(path) for path in files],
                "retrieval_hints": retrieval_hints(candidate_pool, domain),
            }
            write_json(assignment_path, assignment)
            sandbox = sandbox_scout_root / task_id
            scout_inputs: list[tuple[Path, PurePosixPath]] = [
                (assignment_path, PurePosixPath("assignment.json")),
                (job_copy, PurePosixPath("job-description.md")),
                (knowledge_manifest_path, PurePosixPath("knowledge-manifest.json")),
            ]
            for source in files:
                relative = relative_source(source)
                scout_inputs.append((inputs / Path(*PurePosixPath(relative).parts), PurePosixPath(relative)))
            created = create_workspace(
                sandbox,
                pipeline="resume-composer",
                session_id=session_id,
                task_id=task_id,
                skill_source=SCOUT_SKILL,
                inputs=scout_inputs,
                promote_to=session / "scouts" / f"{task_id}.json",
                output_names=["result.json"],
                network="deny",
            )
            tasks[task_id] = {
                "status": "pending",
                "model": "gpt-5.6-terra",
                "reasoning": "xhigh",
                "assignment": {"path": str(assignment_path), "sha256": sha256_file(assignment_path)},
                "sandbox": str(sandbox),
                "manifest_sha256": created["manifest_sha256"],
                "output_sha256": None,
            }
            prompt_lines.extend([
                f"## {task_id}",
                "",
                f"Open and follow `{sandbox / 'skill/SKILL.md'}`. Treat `{sandbox}` as the complete workspace.",
                f"Read the declared inputs and write only `{sandbox / 'outbox/result.json'}`.",
                "Return only `completed` and the output path.",
                "",
            ])

        manifest = {
            "schema_version": 3,
            "pipeline": "resume-composer",
            "session_id": session_id,
            "status": "scouts-pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "session_path": str(session),
            "sandbox_root": str(sandbox_root),
            "source": {
                "base_resume": {"path": str(base_source), "sha256": sha256_file(base_source)},
                "knowledge": knowledge_rows,
            },
            "snapshots": {
                "job_intake": {"path": str(intake_copy), "sha256": sha256_file(intake_copy)},
                "job_description": {"path": str(job_copy), "sha256": sha256_file(job_copy)},
                "base_resume": {"path": str(base_copy), "sha256": sha256_file(base_copy)},
                "candidate_pool": {"path": str(candidate_copy), "sha256": sha256_file(candidate_copy)},
                "knowledge_manifest": {"path": str(knowledge_manifest_path), "sha256": sha256_file(knowledge_manifest_path)},
            },
            "tasks": {"scouts": tasks, "composer": None},
            "promotion": None,
            "cleanup": {"status": "pending", "completed_at": None},
        }
        write_json(session / "manifest.json", manifest)
        prompt_lines.extend([
            "## Coordinator step",
            "",
            "After both tasks finish:",
            "",
            "```powershell",
            f'.\\tailoring\\scripts\\start-writer.ps1 -Session "{session}"',
            "```",
        ])
        (session / "scout-task-prompts.md").write_text("\n".join(prompt_lines) + "\n", encoding="utf-8")
        set_read_only_tree(inputs)
        return session
    except Exception:
        remove_if_safe(sandbox_root, sandbox_root.parent)
        remove_if_safe(session, SESSIONS_ROOT)
        raise


def exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} keys differ, expected={sorted(expected)}, actual={sorted(value)}")


def validate_scout(result: dict[str, Any], assignment: dict[str, Any], inputs_root: Path) -> None:
    exact_keys(result, {"schema_version", "assignment_id", "domain", "ranked_sources", "gaps", "conflicts"}, "scout result")
    if result["schema_version"] != 1 or result["assignment_id"] != assignment["assignment_id"] or result["domain"] != assignment["domain"]:
        raise ValueError("Scout identity disagrees with assignment")
    if not isinstance(result["gaps"], list) or not isinstance(result["conflicts"], list):
        raise ValueError("Scout gaps and conflicts must be arrays")
    rows = result["ranked_sources"]
    if not isinstance(rows, list) or len(rows) > 8:
        raise ValueError("Scout ranked_sources must contain at most eight rows")
    allowed = set(assignment["source_files"])
    if [row.get("rank") for row in rows if isinstance(row, dict)] != list(range(1, len(rows) + 1)):
        raise ValueError("Scout ranks must be consecutive from one")
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"ranked_sources[{index}] must be an object")
        exact_keys(row, {"rank", "source_file", "reason", "excerpts", "caveats"}, f"ranked_sources[{index}]")
        source_file = row["source_file"]
        if source_file not in allowed or source_file in seen:
            raise ValueError(f"Invalid or duplicate scout source: {source_file}")
        seen.add(source_file)
        if not isinstance(row["reason"], str) or not row["reason"].strip() or not isinstance(row["caveats"], list):
            raise ValueError(f"Invalid scout reason or caveats for {source_file}")
        excerpts = row["excerpts"]
        if not isinstance(excerpts, list) or len(excerpts) > 3:
            raise ValueError(f"Scout source {source_file} has too many excerpts")
        source_lines = (inputs_root / Path(*PurePosixPath(source_file).parts)).read_text(encoding="utf-8-sig").splitlines()
        for excerpt in excerpts:
            if not isinstance(excerpt, dict) or set(excerpt) != {"line_start", "line_end", "text"}:
                raise ValueError(f"Invalid scout excerpt shape for {source_file}")
            start, end = excerpt["line_start"], excerpt["line_end"]
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(source_lines):
                raise ValueError(f"Invalid scout line range for {source_file}")
            if excerpt["text"] != "\n".join(source_lines[start - 1:end]):
                raise ValueError(f"Scout excerpt does not match {source_file}:{start}-{end}")


def verify_snapshot(record: dict[str, Any]) -> Path:
    path = Path(record["path"])
    if not path.is_file() or sha256_file(path) != record["sha256"]:
        raise ValueError(f"Snapshot changed: {path}")
    return path


def prepare_composer(args: argparse.Namespace) -> Path:
    session = safe_session(args.session)
    manifest_path = session / "manifest.json"
    manifest = load_json(manifest_path)
    if manifest.get("pipeline") != "resume-composer" or manifest.get("status") != "scouts-pending":
        raise ValueError("Composer preparation requires a scouts-pending session")
    inputs_root = session / "inputs"
    for record in manifest["snapshots"].values():
        verify_snapshot(record)
    for record in manifest["source"]["knowledge"]:
        source = Path(record["source"])
        snapshot = inputs_root / Path(*PurePosixPath(record["path"]).parts)
        if not source.is_file() or sha256_file(source) != record["sha256"] or sha256_file(snapshot) != record["sha256"]:
            raise ValueError(f"Knowledge source changed: {record['path']}")
    source_base = Path(manifest["source"]["base_resume"]["path"])
    if not source_base.is_file() or sha256_file(source_base) != manifest["source"]["base_resume"]["sha256"]:
        raise ValueError("Canonical baseline changed")

    scouts_stage = session / f".scouts-staging-{uuid.uuid4().hex}"
    scouts_final = session / "scouts"
    if scouts_final.exists():
        raise ValueError("Scout reports already exist")
    scouts_stage.mkdir()
    valid_scouts: list[Path] = []
    try:
        for task_id, task in manifest["tasks"]["scouts"].items():
            assignment_path = verify_snapshot(task["assignment"])
            assignment = load_json(assignment_path)
            verified = verify_workspace(
                Path(task["sandbox"]),
                expected_manifest_sha256=task["manifest_sha256"],
                require_output=True,
            )
            result_path = Path(verified["output"])
            result = load_json(result_path)
            validate_scout(result, assignment, Path(task["sandbox"]) / "inputs")
            destination = scouts_stage / f"{task_id}.json"
            shutil.copy2(result_path, destination)
            task["status"] = "validated"
            task["output_sha256"] = sha256_file(destination)
            valid_scouts.append(destination)
        scouts_stage.replace(scouts_final)
        valid_scouts = [scouts_final / path.name for path in valid_scouts]

        sandbox_root = Path(manifest["sandbox_root"])
        composer_sandbox = sandbox_root / "composer"
        composer_inputs: list[tuple[Path, PurePosixPath]] = [
            (Path(manifest["snapshots"]["job_description"]["path"]), PurePosixPath("job-description.md")),
            (Path(manifest["snapshots"]["base_resume"]["path"]), PurePosixPath("base-resume.yaml")),
            (Path(manifest["snapshots"]["knowledge_manifest"]["path"]), PurePosixPath("knowledge-manifest.json")),
        ]
        for record in manifest["source"]["knowledge"]:
            source = inputs_root / Path(*PurePosixPath(record["path"]).parts)
            composer_inputs.append((source, PurePosixPath(record["path"])))
        for scout in sorted(valid_scouts):
            composer_inputs.append((scout, PurePosixPath(f"scouts/{scout.name}")))
        created = create_workspace(
            composer_sandbox,
            pipeline="resume-composer",
            session_id=manifest["session_id"],
            task_id="resume-composer",
            skill_source=COMPOSER_SKILL,
            inputs=composer_inputs,
            promote_to=session / "composer/result.json",
            output_names=["result.json", "resume.yaml", "resume.pdf"],
            network="deny",
        )
        manifest["tasks"]["composer"] = {
            "status": "pending",
            "model": "gpt-5.6-sol",
            "reasoning": "high",
            "sandbox": str(composer_sandbox),
            "manifest_sha256": created["manifest_sha256"],
            "outputs": None,
        }
        manifest["status"] = "composer-pending"
        write_json(manifest_path, manifest)
        for task in manifest["tasks"]["scouts"].values():
            remove_tree_force(Path(task["sandbox"]))
        scout_root = sandbox_root / "scouts"
        if scout_root.exists() and not any(scout_root.iterdir()):
            scout_root.rmdir()

        render_command = (
            f'& "{RENDERCV}" render "{composer_sandbox / "work/resume.yaml"}" '
            f'--output-folder "{composer_sandbox / "work"}" --typst-path "render-temp/resume.typ" '
            '--pdf-path "resume.pdf" --png-path "resume.png" --dont-generate-markdown '
            '--dont-generate-html --quiet'
        )
        prompt = f"""# Global Resume Composer task

Create exactly one new top-level Codex task with model `gpt-5.6-sol` and reasoning `high`.
Never use a subagent, fork, reused task, or parent-chat context.

Open and follow `{composer_sandbox / 'skill/SKILL.md'}`. Treat `{composer_sandbox}` as the complete workspace.
Read its result contract completely. Read every declared Markdown input completely.

Use this pinned RenderCV command after writing `work/resume.yaml`:

```powershell
{render_command}
```

After each render, inspect `{composer_sandbox / 'work/resume_1.png'}` with the image viewer. The final inspected PNG must come from the same final PDF copied to the outbox.

When ready, copy the final YAML and PDF to:

- `{composer_sandbox / 'outbox/resume.yaml'}`
- `{composer_sandbox / 'outbox/resume.pdf'}`

Write `{composer_sandbox / 'outbox/result.json'}` last. Return only `completed` and the output path.

After completion run:

```powershell
.\\tailoring\\scripts\\finalize-writer.ps1 -Session "{session}"
```
"""
        prompt_path = session / "composer-task-prompt.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        return prompt_path
    except Exception:
        remove_if_safe(scouts_stage, session)
        raise


def json_pointer(document: Any, pointer: str) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError(f"Invalid JSON Pointer: {pointer}")
    current = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if not token.isdigit() or int(token) >= len(current):
                raise ValueError(f"Pointer index does not resolve: {pointer}")
            current = current[int(token)]
        elif isinstance(current, dict) and token in current:
            current = current[token]
        else:
            raise ValueError(f"Pointer does not resolve: {pointer}")
    return current


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def locked_resume(resume: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(resume)
    sections = value["cv"]["sections"]
    for entry in sections["Experience"]:
        entry.pop("highlights", None)
    sections["Projects & Open Source"] = "<mutable>"
    sections["Technical Skills"] = "<mutable>"
    return value


def skill_items(resume: dict[str, Any]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for index, group in enumerate(resume["cv"]["sections"]["Technical Skills"]):
        details = group.get("details")
        if not isinstance(details, str):
            raise ValueError(f"Technical Skills group {index} has invalid details")
        for item in [value.strip() for value in details.split(",") if value.strip()]:
            items.append((f"/cv/sections/Technical Skills/{index}/details", item))
    return items


def extract_pdf_text(path: Path) -> str:
    reader = pypdf.PdfReader(str(path))
    return normalized("\n".join(page.extract_text() or "" for page in reader.pages))


def validate_result(
    result: dict[str, Any],
    resume: dict[str, Any],
    base: dict[str, Any],
    manifest: dict[str, Any],
    sandbox: Path,
) -> None:
    exact_keys(
        result,
        {"schema_version", "status", "inputs", "artifacts", "provenance", "visual_inspection", "blocking_reasons", "questions"},
        "Composer result",
    )
    if result["schema_version"] != 1 or result["status"] not in {"ready", "needs-evidence"}:
        raise ValueError("Invalid Composer schema or status")
    if result["status"] != "ready":
        raise ValueError("needs-evidence Composer output cannot be promoted as a resume")
    if result["blocking_reasons"] or result["questions"]:
        raise ValueError("Ready Composer result cannot contain blockers or questions")
    expected_inputs = {
        "baseline_sha256": manifest["snapshots"]["base_resume"]["sha256"],
        "job_sha256": manifest["snapshots"]["job_description"]["sha256"],
        "knowledge_manifest_sha256": manifest["snapshots"]["knowledge_manifest"]["sha256"],
        "scout_result_sha256": [
            manifest["tasks"]["scouts"][task_id]["output_sha256"]
            for task_id in sorted(manifest["tasks"]["scouts"])
        ],
    }
    if result["inputs"] != expected_inputs:
        raise ValueError("Composer input hashes disagree with the session manifest")
    yaml_path = sandbox / "outbox/resume.yaml"
    pdf_path = sandbox / "outbox/resume.pdf"
    artifacts = result["artifacts"]
    if artifacts != {
        "resume_yaml": {"path": "resume.yaml", "sha256": sha256_file(yaml_path)},
        "resume_pdf": {"path": "resume.pdf", "sha256": sha256_file(pdf_path)},
    }:
        raise ValueError("Composer artifact hashes or paths are invalid")
    if locked_resume(resume) != locked_resume(base):
        raise ValueError("Composer changed locked baseline content")
    if "\u2014" in yaml_path.read_text(encoding="utf-8-sig"):
        raise ValueError("Composer YAML contains Unicode U+2014")
    experience = resume["cv"]["sections"]["Experience"]
    projects = resume["cv"]["sections"]["Projects & Open Source"]
    base_experience = base["cv"]["sections"]["Experience"]
    base_projects = base["cv"]["sections"]["Projects & Open Source"]
    minimum_projects = min(2, len(base_projects))
    if not isinstance(projects, list) or len(projects) < minimum_projects:
        raise ValueError(f"Composer must keep at least {minimum_projects} projects")
    baseline_bullet_count = sum(len(entry.get("highlights", [])) for entry in base_experience)
    final_bullet_count = sum(len(entry.get("highlights", [])) for entry in experience)
    if final_bullet_count < baseline_bullet_count:
        raise ValueError(
            "Composer cannot reduce total Experience bullet density below the baseline"
        )
    expected_targets: list[tuple[str, str, str | None]] = []
    experience_text: list[str] = []
    for entry_index, entry in enumerate(experience):
        highlights = entry.get("highlights")
        if not isinstance(highlights, list) or not highlights:
            raise ValueError(f"Experience entry {entry_index} has no highlights")
        for bullet_index, bullet in enumerate(highlights):
            if not isinstance(bullet, str) or not bullet.strip() or STRONG.search(bullet):
                raise ValueError(f"Invalid experience bullet at {entry_index}/{bullet_index}")
            target = f"/cv/sections/Experience/{entry_index}/highlights/{bullet_index}"
            expected_targets.append(("experience-bullet", target, None))
            experience_text.append(normalized(bullet))
    project_text: list[str] = []
    for index, project in enumerate(projects):
        if not isinstance(project, dict) or not isinstance(project.get("label"), str) or not isinstance(project.get("details"), str):
            raise ValueError(f"Invalid project entry {index}")
        expected_targets.append(("project", f"/cv/sections/Projects & Open Source/{index}", None))
        project_text.append(normalized(project["details"]))
    for target, item in skill_items(resume):
        expected_targets.append(("skill", target, item))

    provenance = result["provenance"]
    if not isinstance(provenance, list):
        raise ValueError("Composer provenance must be an array")
    observed: list[tuple[str, str, str | None]] = []
    experience_sources: set[tuple[str, int, int]] = set()
    project_sources: set[tuple[str, int, int]] = set()
    knowledge_manifest = load_json(Path(manifest["snapshots"]["knowledge_manifest"]["path"]))
    allowed_sources = {row["path"]: row for row in knowledge_manifest["sources"]}
    for index, row in enumerate(provenance):
        if not isinstance(row, dict) or set(row) not in ({"kind", "target", "sources"}, {"kind", "target", "item", "sources"}):
            raise ValueError(f"Invalid provenance entry {index}")
        kind, target = row["kind"], row["target"]
        item = row.get("item")
        observed.append((kind, target, item))
        json_pointer(resume, target)
        sources = row["sources"]
        if not isinstance(sources, list) or not sources:
            raise ValueError(f"Provenance entry {index} has no sources")
        for source in sources:
            if not isinstance(source, dict) or source.get("type") not in {"knowledge-base", "baseline"}:
                raise ValueError(f"Invalid provenance source at entry {index}")
            if source["type"] == "baseline":
                if set(source) != {"type", "pointer"} or json_pointer(base, source["pointer"]) != json_pointer(resume, target):
                    raise ValueError(f"Invalid baseline provenance at entry {index}")
                continue
            if set(source) != {"type", "file", "line_start", "line_end"}:
                raise ValueError(f"Invalid knowledge provenance at entry {index}")
            file = source["file"]
            start, end = source["line_start"], source["line_end"]
            if file not in allowed_sources or type(start) is not int or type(end) is not int:
                raise ValueError(f"Unknown knowledge provenance at entry {index}")
            lines = (sandbox / "inputs" / Path(*PurePosixPath(file).parts)).read_text(encoding="utf-8-sig").splitlines()
            if not 1 <= start <= end <= len(lines):
                raise ValueError(f"Invalid knowledge line range at entry {index}")
            signature = (file, start, end)
            if kind == "experience-bullet":
                experience_sources.add(signature)
            elif kind == "project":
                project_sources.add(signature)
    if sorted(observed) != sorted(expected_targets):
        raise ValueError("Composer provenance does not cover every bullet, project, and skill exactly once")
    if experience_sources & project_sources:
        raise ValueError("The same evidence range is reused across Experience and Projects")
    if set(experience_text) & set(project_text):
        raise ValueError("Experience and Projects repeat the same content")

    inspection = result["visual_inspection"]
    exact_keys(inspection, {"inspected", "pdf_sha256", "page_count", "pages_viewed", "checks", "issues"}, "visual_inspection")
    required_checks = {"no_clipping_or_overlap", "legible_text", "balanced_spacing", "consistent_hierarchy"}
    if (
        inspection["inspected"] is not True
        or inspection["pdf_sha256"] != sha256_file(pdf_path)
        or inspection["page_count"] != 1
        or inspection["pages_viewed"] != [1]
        or set(inspection["checks"]) != required_checks
        or not all(value is True for value in inspection["checks"].values())
        or inspection["issues"] != []
    ):
        raise ValueError("Composer visual inspection is incomplete or disagrees with the final PDF")


def finalize(args: argparse.Namespace) -> Path:
    session = safe_session(args.session)
    manifest_path = session / "manifest.json"
    manifest = load_json(manifest_path)
    if manifest.get("pipeline") != "resume-composer" or manifest.get("status") != "composer-pending":
        raise ValueError("Finalization requires a composer-pending session")
    for record in manifest["snapshots"].values():
        verify_snapshot(record)
    for record in manifest["source"]["knowledge"]:
        source = Path(record["source"])
        if not source.is_file() or sha256_file(source) != record["sha256"]:
            raise ValueError(f"Canonical knowledge changed: {record['path']}")
    base_source = Path(manifest["source"]["base_resume"]["path"])
    if not base_source.is_file() or sha256_file(base_source) != manifest["source"]["base_resume"]["sha256"]:
        raise ValueError("Canonical baseline changed")

    composer = manifest["tasks"]["composer"]
    sandbox = Path(composer["sandbox"])
    verified = verify_workspace(sandbox, expected_manifest_sha256=composer["manifest_sha256"], require_output=True)
    result_path = Path(verified["outputs"]["result.json"]["path"])
    yaml_path = Path(verified["outputs"]["resume.yaml"]["path"])
    pdf_path = Path(verified["outputs"]["resume.pdf"]["path"])
    result = load_json(result_path)
    resume = yaml.safe_load(yaml_path.read_text(encoding="utf-8-sig"))
    base = yaml.safe_load(Path(manifest["snapshots"]["base_resume"]["path"]).read_text(encoding="utf-8-sig"))
    validate_result(result, resume, base, manifest, sandbox)

    output = session / "composer"
    if output.exists():
        raise ValueError("Composer output already exists")
    stage = session / f".composer-staging-{uuid.uuid4().hex}"
    try:
        stage.mkdir()
        shutil.copy2(result_path, stage / "result.json")
        shutil.copy2(yaml_path, stage / "resume.yaml")
        shutil.copy2(pdf_path, stage / "resume.pdf")
        run([sys.executable, PDF_CHECKS, "--resume", stage / "resume.pdf", "--output", stage / "pdf-checks.json"])
        checks = load_json(stage / "pdf-checks.json")
        failed = [name for name, row in checks["checks"].items() if not row["passed"]]
        if failed:
            raise ValueError("Composer PDF failed checks: " + ", ".join(failed))

        rerender = stage / "rerender"
        rerender.mkdir()
        rerender_yaml = rerender / "resume.yaml"
        shutil.copy2(stage / "resume.yaml", rerender_yaml)
        rerender_yaml.chmod(rerender_yaml.stat().st_mode | 0o200)
        run([
            RENDERCV, "render", rerender_yaml,
            "--output-folder", rerender,
            "--typst-path", "render-temp/resume.typ",
            "--pdf-path", "resume.pdf",
            "--dont-generate-markdown",
            "--dont-generate-html",
            "--dont-generate-png",
            "--quiet",
        ])
        if extract_pdf_text(stage / "resume.pdf") != extract_pdf_text(rerender / "resume.pdf"):
            raise ValueError("Submitted PDF text disagrees with a deterministic rerender of resume.yaml")
        shutil.rmtree(rerender)
        completed = datetime.now(timezone.utc).isoformat()
        receipt = {
            "schema_version": 3,
            "pipeline": "resume-composer",
            "session_id": manifest["session_id"],
            "status": "ready",
            "completed_at": completed,
            "execution": {"model": composer["model"], "reasoning": composer["reasoning"]},
            "checks": {
                "sandbox": "passed",
                "contract": "passed",
                "provenance": "passed",
                "locked_metadata": "passed",
                "visual_inspection": "passed",
                "deterministic_rerender": "passed",
                "pdf_preflight": "passed",
            },
            "artifacts": {
                name: {"path": name, "sha256": sha256_file(stage / name)}
                for name in ("result.json", "resume.yaml", "resume.pdf", "pdf-checks.json")
            },
        }
        write_json(stage / "receipt.json", receipt)
        stage.replace(output)
        manifest["status"] = "completed"
        manifest["completed_at"] = completed
        manifest["tasks"]["composer"]["status"] = "validated"
        manifest["tasks"]["composer"]["outputs"] = receipt["artifacts"]
        manifest["promotion"] = {"path": str(output), "promoted_at": completed}
        manifest["cleanup"] = {"status": "completed", "completed_at": completed}
        write_json(manifest_path, manifest)
        sandbox_root = Path(manifest["sandbox_root"])
        remove_tree_force(sandbox_root)
        return output
    except Exception:
        remove_if_safe(stage, session)
        raise


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    start_parser = commands.add_parser("start")
    start_parser.add_argument("--job-intake", required=True, type=Path)
    start_parser.add_argument("--base-resume", type=Path, default=DEFAULT_BASE)
    start_parser.add_argument("--session-id")
    start_parser.add_argument("--sandbox-root", type=Path)
    composer_parser = commands.add_parser("prepare-composer")
    composer_parser.add_argument("--session", required=True, type=Path)
    finalize_parser = commands.add_parser("finalize")
    finalize_parser.add_argument("--session", required=True, type=Path)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "start":
            output = start(args)
        elif args.command == "prepare-composer":
            output = prepare_composer(args)
        else:
            output = finalize(args)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
