#!/usr/bin/env python3
"""Split one context pack into maximally isolated Writer assignments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from writer_task_common import card_matches_experience, normalize, profile_anchor_skill_groups, write_json


def _criteria_for(cards: list[dict[str, Any]], criteria: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = {card["criterion_id"] for card in cards}
    return [row for row in criteria if row["criterion_id"] in ids]


def build_assignments(context: dict[str, Any], base: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sections = base["cv"]["sections"]
    cards = [card for card in context["evidence_cards"] if card["use_status"] == "include"]
    common_constraints = {
        "knowledge_base_is_read_only": True,
        "use_only_include_evidence_cards": True,
        "no_invented_facts_metrics_technologies_or_ownership": True,
        "forbid_unicode_u2014": True,
    }
    assignments: dict[str, dict[str, Any]] = {}
    company_counts: dict[str, int] = {}
    for entry in sections["Experience"]:
        company_key = normalize(entry["company"].split("(", 1)[0].strip())
        company_counts[company_key] = company_counts.get(company_key, 0) + 1
    for index, entry in enumerate(sections["Experience"]):
        company_key = normalize(entry["company"].split("(", 1)[0].strip())
        scoped = [
            card for card in cards
            if card_matches_experience(card, entry, allow_organization=company_counts[company_key] == 1)
        ]
        task_id = f"experience-{index}"
        assignments[task_id] = {
            "schema_version": 1,
            "task": {"task_id": task_id, "kind": "experience", "source_index": index},
            "job": context["job"],
            "criteria": _criteria_for(scoped, context["criteria"]),
            "baseline": entry,
            "evidence_cards": scoped,
            "constraints": {**common_constraints, "highlight_count": {"minimum": 1, "maximum": 3}},
        }

    project_cards = [card for card in cards if card["source_file"].startswith("knowledge-base/projects/")]
    assignments["projects"] = {
        "schema_version": 1,
        "task": {"task_id": "projects", "kind": "projects"},
        "job": context["job"],
        "criteria": _criteria_for(project_cards, context["criteria"]),
        "baseline": sections["Projects & Open Source"],
        "evidence_cards": project_cards,
        "constraints": {**common_constraints, "maximum_entries": len(sections["Projects & Open Source"])},
    }
    assignments["technical-skills"] = {
        "schema_version": 1,
        "task": {"task_id": "technical-skills", "kind": "technical-skills"},
        "job": context["job"],
        "criteria": context["criteria"],
        "baseline": sections["Technical Skills"],
        "evidence_cards": cards,
        "constraints": {
            **common_constraints,
            "maximum_entries": len(sections["Technical Skills"]),
            "profile_anchor_groups": profile_anchor_skill_groups(sections["Technical Skills"]),
            "ordering_policy": "Order groups by relevance to the offer; keep secondary profile anchors concise and place them later rather than deleting them.",
            "density_guidance": {
                "preferred_group_count": {"minimum": 3, "maximum": 5},
                "maximum_items_per_group": 7,
                "maximum_total_items": 24,
                "do_not_pad_to_reach_a_target": True,
            },
        },
    }
    return assignments


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context-pack", required=True, type=Path)
    parser.add_argument("--base-resume", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.output_dir.exists():
        print(f"ERROR: output directory already exists: {args.output_dir}", file=sys.stderr)
        return 1
    try:
        context = json.loads(args.context_pack.read_text(encoding="utf-8-sig"))
        base = yaml.safe_load(args.base_resume.read_text(encoding="utf-8-sig"))
        assignments = build_assignments(context, base)
        args.output_dir.mkdir(parents=True)
        for task_id, assignment in assignments.items():
            write_json(args.output_dir / f"{task_id}.json", assignment)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"task_ids": list(assignments)}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
