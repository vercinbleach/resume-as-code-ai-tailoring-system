#!/usr/bin/env python3
"""Validate an assembled multi-Writer result against pinned inputs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from writer_task_common import card_matches_experience, normalize, profile_anchor_skill_groups, sha256_file


ROOT_KEYS = {"schema_version", "status", "inputs", "job", "content", "blocking_reasons", "questions"}
STRONG = re.compile(r"\*\*|__|<\s*/?\s*(?:strong|b)(?:\s+[^<>]*)?\s*>", re.I)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def _strings(value: Any, minimum: int = 0) -> bool:
    return isinstance(value, list) and len(value) >= minimum and all(
        isinstance(item, str) and bool(item.strip()) for item in value
    ) and len(value) == len(set(value))


def _authored(
    field: Any,
    label: str,
    cards: dict[str, dict[str, Any]],
    allowed: set[str],
    errors: list[str],
    used: set[str],
    *,
    bullet: bool = False,
) -> None:
    expected = {"mode", "text", "supporting_evidence_ids"}
    if not isinstance(field, dict) or set(field) != expected or field.get("mode") != "authored":
        errors.append(f"{label} must be an authored text field")
        return
    text = field["text"]
    if not isinstance(text, str) or not text.strip() or text != text.strip() or "\u2014" in text:
        errors.append(f"{label}.text is invalid")
    elif bullet and STRONG.search(text):
        errors.append(f"{label}.text cannot contain strong-emphasis markup")
    ids = field["supporting_evidence_ids"]
    if not _strings(ids, 1):
        errors.append(f"{label}.supporting_evidence_ids is invalid")
        return
    for evidence_id in ids:
        if evidence_id not in allowed or evidence_id not in cards:
            errors.append(f"{label} references unavailable evidence {evidence_id}")
        else:
            used.add(evidence_id)


def validate_result(
    result: Any,
    context_pack: Any,
    base_resume: Any,
    *,
    result_context_sha256: str,
    result_base_sha256: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(result, dict) or set(result) != ROOT_KEYS:
        return [f"writer result must contain exactly {sorted(ROOT_KEYS)}"]
    if result["schema_version"] != 2:
        errors.append("writer result schema_version must be 2")
    if result["inputs"] != {
        "context_pack_sha256": result_context_sha256,
        "base_resume_sha256": result_base_sha256,
    }:
        errors.append("writer result input hashes do not match")
    if result["job"] != context_pack.get("job"):
        errors.append("writer result job must exactly equal context pack job")
    if not _strings(result["blocking_reasons"]) or not _strings(result["questions"]):
        errors.append("blocking_reasons and questions must be unique string arrays")
    if result["status"] not in {"ready", "needs-evidence"}:
        return errors + ["status must be ready or needs-evidence"]
    if result["status"] == "needs-evidence":
        if result["content"] is not None or not result["blocking_reasons"]:
            errors.append("needs-evidence requires null content and blocking reasons")
        return errors
    if result["blocking_reasons"]:
        errors.append("ready result blocking_reasons must be empty")
    content = result["content"]
    if not isinstance(content, dict) or set(content) != {"experience", "projects", "technical_skills"}:
        return errors + ["ready content has an invalid shape"]
    sections = base_resume["cv"]["sections"]
    cards = {card["id"]: card for card in context_pack["evidence_cards"] if card["use_status"] == "include"}
    used: set[str] = set()
    company_counts: dict[str, int] = {}
    for entry in sections["Experience"]:
        key = normalize(entry["company"].split("(", 1)[0].strip())
        company_counts[key] = company_counts.get(key, 0) + 1

    experience = content["experience"]
    if not isinstance(experience, list) or len(experience) != len(sections["Experience"]):
        errors.append("experience must retain every baseline entry")
    else:
        for index, decision in enumerate(experience):
            label = f"experience[{index}]"
            if not isinstance(decision, dict) or set(decision) != {"source_index", "highlights"} or decision.get("source_index") != index:
                errors.append(f"{label} has an invalid source identity")
                continue
            highlights = decision["highlights"]
            if not isinstance(highlights, list) or not 1 <= len(highlights) <= 3:
                errors.append(f"{label}.highlights must contain one to three items")
                continue
            company_key = normalize(sections["Experience"][index]["company"].split("(", 1)[0].strip())
            allowed = {
                card_id for card_id, card in cards.items()
                if card_matches_experience(
                    card,
                    sections["Experience"][index],
                    allow_organization=company_counts[company_key] == 1,
                )
            }
            for field_index, field in enumerate(highlights):
                field_label = f"{label}.highlights[{field_index}]"
                if isinstance(field, dict) and field.get("mode") == "preserve":
                    if set(field) != {"mode", "baseline_index"} or type(field.get("baseline_index")) is not int or not 0 <= field["baseline_index"] < len(sections["Experience"][index]["highlights"]):
                        errors.append(f"{field_label} has an invalid preserve reference")
                else:
                    _authored(field, field_label, cards, allowed, errors, used, bullet=True)

    projects = content["projects"]
    if not isinstance(projects, list) or not 1 <= len(projects) <= len(sections["Projects & Open Source"]):
        errors.append("projects must contain between one and the baseline project count")
    else:
        identities: set[tuple[str, Any]] = set()
        for index, item in enumerate(projects):
            label = f"projects[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be an object")
                continue
            if item.get("mode") == "preserve":
                if set(item) != {"mode", "source_index"} or type(item.get("source_index")) is not int or not 0 <= item["source_index"] < len(sections["Projects & Open Source"]):
                    errors.append(f"{label} has an invalid preserve reference")
                    continue
                identity = ("source", item["source_index"])
            else:
                expected = {"mode", "project_id", "label", "details", "supporting_evidence_ids"}
                if set(item) != expected or item.get("mode") != "authored":
                    errors.append(f"{label} has an invalid authored shape")
                    continue
                project_id = item["project_id"]
                ids = item["supporting_evidence_ids"]
                allowed = {card_id for card_id, card in cards.items() if card.get("source_metadata", {}).get("id") == project_id}
                if not isinstance(project_id, str) or not project_id.startswith("project-"):
                    errors.append(f"{label}.project_id is invalid")
                if not _strings(ids, 1) or any(value not in allowed for value in ids):
                    errors.append(f"{label} cites evidence from another project")
                else:
                    used.update(ids)
                for field in ("label", "details"):
                    if not isinstance(item[field], str) or not item[field].strip() or item[field] != item[field].strip() or "\u2014" in item[field]:
                        errors.append(f"{label}.{field} is invalid")
                identity = ("project", project_id)
            if identity in identities:
                errors.append(f"{label} duplicates a project identity")
            identities.add(identity)

    skills = content["technical_skills"]
    if not isinstance(skills, list) or not 1 <= len(skills) <= len(sections["Technical Skills"]):
        errors.append("technical_skills must contain between one and the baseline skill count")
    else:
        identities: set[tuple[str, Any]] = set()
        selected_labels: set[str] = set()
        for index, item in enumerate(skills):
            label = f"technical_skills[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be an object")
                continue
            if item.get("mode") == "preserve":
                if set(item) != {"mode", "source_index"} or type(item.get("source_index")) is not int or not 0 <= item["source_index"] < len(sections["Technical Skills"]):
                    errors.append(f"{label} has an invalid preserve reference")
                    continue
                identity = ("source", item["source_index"])
                selected_labels.add(normalize(sections["Technical Skills"][item["source_index"]]["label"]))
            else:
                expected = {"mode", "skill_group_id", "label", "details", "supporting_evidence_ids"}
                if set(item) != expected or item.get("mode") != "authored":
                    errors.append(f"{label} has an invalid authored shape")
                    continue
                ids = item["supporting_evidence_ids"]
                if not _strings(ids, 1) or any(value not in cards for value in ids):
                    errors.append(f"{label} references unavailable evidence")
                else:
                    used.update(ids)
                for field in ("skill_group_id", "label", "details"):
                    if not isinstance(item[field], str) or not item[field].strip() or "\u2014" in item[field]:
                        errors.append(f"{label}.{field} is invalid")
                if isinstance(item.get("label"), str):
                    selected_labels.add(normalize(item["label"]))
                identity = ("group", item.get("skill_group_id"))
            if identity in identities:
                errors.append(f"{label} duplicates a skill identity")
            identities.add(identity)
        for anchor in profile_anchor_skill_groups(sections["Technical Skills"]):
            if normalize(anchor) not in selected_labels:
                errors.append(f"technical_skills must retain profile anchor '{anchor}'")
    if not used:
        errors.append("ready content must contain at least one evidence-backed authored field")
    return errors


def validate_files(result_path: Path, context_path: Path, base_path: Path) -> tuple[Any, Any, Any, list[str]]:
    result = load_json(result_path)
    context = load_json(context_path)
    base = load_yaml(base_path)
    return result, context, base, validate_result(
        result, context, base,
        result_context_sha256=sha256_file(context_path),
        result_base_sha256=sha256_file(base_path),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--context-pack", required=True, type=Path)
    parser.add_argument("--base-resume", required=True, type=Path)
    args = parser.parse_args()
    try:
        _, _, _, errors = validate_files(args.result, args.context_pack, args.base_resume)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        errors = [str(exc)]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated writer result: {args.result.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
