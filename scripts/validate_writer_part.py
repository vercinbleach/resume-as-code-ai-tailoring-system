#!/usr/bin/env python3
"""Validate one isolated Writer result against its exact assignment."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from writer_task_common import normalize, sha256_file


ROOT_KEYS = {"schema_version", "task_id", "assignment_sha256", "status", "content", "blocking_reasons", "questions"}
AUTHORED_KEYS = {"mode", "text", "supporting_evidence_ids"}
PRESERVE_HIGHLIGHT_KEYS = {"mode", "baseline_index"}
STRONG = re.compile(r"\*\*|__|<\s*/?\s*(?:strong|b)(?:\s+[^<>]*)?\s*>", re.I)


def _strings(value: Any, minimum: int = 0) -> bool:
    return isinstance(value, list) and len(value) >= minimum and all(
        isinstance(item, str) and bool(item.strip()) for item in value
    ) and len(value) == len(set(value))


def _authored(field: Any, label: str, allowed: set[str], errors: list[str], *, bullet: bool = False) -> None:
    if not isinstance(field, dict) or set(field) != AUTHORED_KEYS or field.get("mode") != "authored":
        errors.append(f"{label} must be an authored text field")
        return
    text = field["text"]
    if not isinstance(text, str) or not text.strip() or text != text.strip():
        errors.append(f"{label}.text must be a trimmed non-empty string")
    elif "\u2014" in text:
        errors.append(f"{label}.text cannot contain Unicode U+2014")
    elif bullet and STRONG.search(text):
        errors.append(f"{label}.text cannot contain strong-emphasis markup")
    ids = field["supporting_evidence_ids"]
    if not _strings(ids, 1):
        errors.append(f"{label}.supporting_evidence_ids must be a unique non-empty string array")
    elif any(item not in allowed for item in ids):
        errors.append(f"{label} references evidence outside this assignment")


def validate_part(result: Any, assignment: dict[str, Any], assignment_sha256: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(result, dict) or set(result) != ROOT_KEYS:
        return [f"writer part must contain exactly {sorted(ROOT_KEYS)}"]
    if result["schema_version"] != 1:
        errors.append("schema_version must be 1")
    task = assignment["task"]
    if result["task_id"] != task["task_id"]:
        errors.append("task_id disagrees with assignment")
    if result["assignment_sha256"] != assignment_sha256:
        errors.append("assignment_sha256 disagrees with assignment")
    if not _strings(result["blocking_reasons"]) or not _strings(result["questions"]):
        errors.append("blocking_reasons and questions must be unique string arrays")
    if result["status"] not in {"ready", "needs-evidence"}:
        return errors + ["status must be ready or needs-evidence"]
    if result["status"] == "needs-evidence":
        if result["content"] is not None or not result["blocking_reasons"]:
            errors.append("needs-evidence requires null content and a blocking reason")
        return errors
    if result["blocking_reasons"]:
        errors.append("ready results cannot have blocking reasons")
    content = result["content"]
    allowed = {card["id"] for card in assignment["evidence_cards"] if card["use_status"] == "include"}
    kind = task["kind"]

    if kind == "experience":
        if not isinstance(content, dict) or set(content) != {"source_index", "highlights"}:
            return errors + ["experience content must contain source_index and highlights"]
        if content["source_index"] != task["source_index"]:
            errors.append("experience source_index disagrees with assignment")
        highlights = content["highlights"]
        if not isinstance(highlights, list) or not 1 <= len(highlights) <= 3:
            errors.append("experience highlights must contain between one and three items")
        else:
            base_count = len(assignment["baseline"].get("highlights", []))
            for index, field in enumerate(highlights):
                label = f"highlights[{index}]"
                if isinstance(field, dict) and field.get("mode") == "preserve":
                    if set(field) != PRESERVE_HIGHLIGHT_KEYS or type(field.get("baseline_index")) is not int or not 0 <= field["baseline_index"] < base_count:
                        errors.append(f"{label} has an invalid preserve reference")
                else:
                    _authored(field, label, allowed, errors, bullet=True)
    elif kind == "projects":
        if not isinstance(content, dict) or set(content) != {"projects"}:
            return errors + ["project content must contain projects"]
        projects = content["projects"]
        maximum = assignment["constraints"]["maximum_entries"]
        if not isinstance(projects, list) or not 1 <= len(projects) <= maximum:
            errors.append("projects must respect the assignment entry limit")
        else:
            used: set[tuple[str, Any]] = set()
            for index, item in enumerate(projects):
                label = f"projects[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{label} must be an object")
                    continue
                if item.get("mode") == "preserve":
                    if set(item) != {"mode", "source_index"} or type(item.get("source_index")) is not int or not 0 <= item["source_index"] < len(assignment["baseline"]):
                        errors.append(f"{label} has an invalid preserve reference")
                        continue
                    identity = ("source", item["source_index"])
                else:
                    if set(item) != {"mode", "project_id", "label", "details", "supporting_evidence_ids"} or item.get("mode") != "authored":
                        errors.append(f"{label} has an invalid authored project shape")
                        continue
                    ids = item["supporting_evidence_ids"]
                    if not _strings(ids, 1) or any(value not in allowed for value in ids):
                        errors.append(f"{label} references evidence outside this assignment")
                    project_id = item["project_id"]
                    if not isinstance(project_id, str) or not project_id.startswith("project-"):
                        errors.append(f"{label}.project_id is invalid")
                    elif any(
                        card["id"] in ids and card.get("source_metadata", {}).get("id") != project_id
                        for card in assignment["evidence_cards"]
                    ):
                        errors.append(f"{label} cites evidence from another project")
                    for field in ("label", "details"):
                        text = item[field]
                        if not isinstance(text, str) or not text.strip() or text != text.strip() or "\u2014" in text:
                            errors.append(f"{label}.{field} is invalid")
                    identity = ("project", project_id)
                if identity in used:
                    errors.append(f"{label} duplicates a project identity")
                used.add(identity)
    else:
        if not isinstance(content, dict) or set(content) != {"technical_skills"}:
            return errors + ["technical skills content must contain technical_skills"]
        skills = content["technical_skills"]
        maximum = assignment["constraints"]["maximum_entries"]
        if not isinstance(skills, list) or not 1 <= len(skills) <= maximum:
            errors.append("technical_skills must respect the assignment entry limit")
        else:
            used: set[tuple[str, Any]] = set()
            selected_labels: set[str] = set()
            for index, item in enumerate(skills):
                label = f"technical_skills[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{label} must be an object")
                    continue
                if item.get("mode") == "preserve":
                    if set(item) != {"mode", "source_index"} or type(item.get("source_index")) is not int or not 0 <= item["source_index"] < len(assignment["baseline"]):
                        errors.append(f"{label} has an invalid preserve reference")
                        continue
                    identity = ("source", item["source_index"])
                    selected_labels.add(normalize(assignment["baseline"][item["source_index"]]["label"]))
                else:
                    if set(item) != {"mode", "skill_group_id", "label", "details", "supporting_evidence_ids"} or item.get("mode") != "authored":
                        errors.append(f"{label} has an invalid authored skill shape")
                        continue
                    ids = item["supporting_evidence_ids"]
                    if not _strings(ids, 1) or any(value not in allowed for value in ids):
                        errors.append(f"{label} references evidence outside this assignment")
                    for field in ("skill_group_id", "label", "details"):
                        if not isinstance(item[field], str) or not item[field].strip() or "\u2014" in item[field]:
                            errors.append(f"{label}.{field} is invalid")
                    if isinstance(item.get("label"), str):
                        selected_labels.add(normalize(item["label"]))
                    identity = ("group", item.get("skill_group_id"))
                if identity in used:
                    errors.append(f"{label} duplicates a skill identity")
                used.add(identity)
            for anchor in assignment["constraints"].get("profile_anchor_groups", []):
                if normalize(anchor) not in selected_labels:
                    errors.append(f"technical_skills must retain profile anchor '{anchor}'")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--assignment", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = json.loads(args.result.read_text(encoding="utf-8-sig"))
        assignment = json.loads(args.assignment.read_text(encoding="utf-8-sig"))
        errors = validate_part(result, assignment, sha256_file(args.assignment))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated writer part: {args.result.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
