#!/usr/bin/env python3
"""Deterministically assemble isolated Writer parts into one resume result."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_writer_part import validate_part
from writer_task_common import load_json, sha256_file, write_json


def assemble(assignments_dir: Path, results_dir: Path, context_path: Path, base_path: Path) -> dict:
    context = load_json(context_path)
    assignments = {path.stem: load_json(path) for path in sorted(assignments_dir.glob("*.json"))}
    expected = set(assignments)
    result_paths = {path.stem: path for path in results_dir.glob("*.json")}
    if set(result_paths) != expected:
        raise ValueError(f"Writer result set must be exactly {sorted(expected)}")
    parts = {}
    errors: list[str] = []
    for task_id in sorted(expected):
        part = load_json(result_paths[task_id])
        violations = validate_part(part, assignments[task_id], sha256_file(assignments_dir / f"{task_id}.json"))
        if violations:
            errors.extend(f"{task_id}: {item}" for item in violations)
        parts[task_id] = part
    if errors:
        raise ValueError("; ".join(errors))

    blocked = [part for part in parts.values() if part["status"] == "needs-evidence"]
    if blocked:
        return {
            "schema_version": 2,
            "status": "needs-evidence",
            "inputs": {"context_pack_sha256": sha256_file(context_path), "base_resume_sha256": sha256_file(base_path)},
            "job": context["job"],
            "content": None,
            "blocking_reasons": sorted({reason for part in blocked for reason in part["blocking_reasons"]}),
            "questions": sorted({question for part in blocked for question in part["questions"]}),
        }
    experience_ids = sorted(
        (task_id for task_id, assignment in assignments.items() if assignment["task"]["kind"] == "experience"),
        key=lambda task_id: assignments[task_id]["task"]["source_index"],
    )
    return {
        "schema_version": 2,
        "status": "ready",
        "inputs": {"context_pack_sha256": sha256_file(context_path), "base_resume_sha256": sha256_file(base_path)},
        "job": context["job"],
        "content": {
            "experience": [parts[task_id]["content"] for task_id in experience_ids],
            "projects": parts["projects"]["content"]["projects"],
            "technical_skills": parts["technical-skills"]["content"]["technical_skills"],
        },
        "blocking_reasons": [],
        "questions": sorted({question for part in parts.values() for question in part["questions"]}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assignments-dir", required=True, type=Path)
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--context-pack", required=True, type=Path)
    parser.add_argument("--base-resume", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = assemble(args.assignments_dir, args.results_dir, args.context_pack, args.base_resume)
        write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
