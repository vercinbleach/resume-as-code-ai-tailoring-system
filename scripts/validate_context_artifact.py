#!/usr/bin/env python3
"""Validate deterministic candidate-pool and writer context-pack artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from context_common import load_claims, load_json, sha256_file


def exact_keys(value: Any, expected: set[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    if set(value) != expected:
        return [f"{label} must contain exactly {sorted(expected)}"]
    return []


def validate_candidate_pool(pool: Any, root: Path, claims: dict[str, dict[str, Any]]) -> list[str]:
    errors = exact_keys(
        pool,
        {"schema_version", "job", "inputs", "retrieval", "coverage", "criteria"},
        "candidate pool",
    )
    if errors:
        return errors
    if pool["schema_version"] != 1:
        errors.append("candidate pool schema_version must be 1")
    expected_hash = sha256_file(root / "knowledge-base" / "generated" / "claims.jsonl")
    if pool["inputs"].get("claim_index_sha256") != expected_hash:
        errors.append("candidate pool claim index hash is stale")
    maximum = pool["retrieval"].get("max_candidates_per_criterion")
    if not isinstance(maximum, int) or maximum < 1:
        errors.append("candidate pool maximum must be a positive integer")
        maximum = 0

    criterion_ids: set[str] = set()
    for index, criterion in enumerate(pool["criteria"]):
        label = f"criteria[{index}]"
        criterion_id = criterion.get("id")
        if not isinstance(criterion_id, str) or not criterion_id:
            errors.append(f"{label}.id must be a non-empty string")
        elif criterion_id in criterion_ids:
            errors.append(f"{label}.id is duplicated")
        else:
            criterion_ids.add(criterion_id)
        candidates = criterion.get("candidates")
        if not isinstance(candidates, list):
            errors.append(f"{label}.candidates must be an array")
            continue
        if len(candidates) > maximum:
            errors.append(f"{label}.candidates exceeds the configured cap")
        seen_claims: set[str] = set()
        previous_score: float | None = None
        for candidate_index, candidate in enumerate(candidates):
            here = f"{label}.candidates[{candidate_index}]"
            claim_id = candidate.get("claim_id")
            if claim_id in seen_claims:
                errors.append(f"{here}.claim_id is duplicated")
            seen_claims.add(claim_id)
            claim = claims.get(claim_id)
            if claim is None:
                errors.append(f"{here} references unknown claim {claim_id}")
                continue
            for field in ("status", "resume_safe", "source_file"):
                if candidate.get(field) != claim[field]:
                    errors.append(f"{here}.{field} disagrees with the claim index")
            score = candidate.get("score")
            if not isinstance(score, (int, float)) or score < 0:
                errors.append(f"{here}.score must be non-negative")
            elif previous_score is not None and score > previous_score:
                errors.append(f"{label}.candidates are not sorted by descending score")
            else:
                previous_score = float(score)
        narratives = criterion.get("narrative_candidates")
        if not isinstance(narratives, list):
            errors.append(f"{label}.narrative_candidates must be an array")
            continue
        for narrative_index, narrative in enumerate(narratives):
            source_file = narrative.get("source_file")
            if not isinstance(source_file, str) or not (root / source_file).is_file():
                errors.append(
                    f"{label}.narrative_candidates[{narrative_index}] points to a missing source"
                )
    return errors


def validate_context_pack(
    pack: Any,
    claims: dict[str, dict[str, Any]],
    source_root: Path | None = None,
) -> list[str]:
    errors = exact_keys(
        pack,
        {
            "schema_version", "job", "inputs", "policy", "summary", "criteria",
            "evidence_cards", "claims", "coverage_queue", "exclusions",
        },
        "context pack",
    )
    if errors:
        return errors
    if pack["schema_version"] != 2:
        errors.append("context pack schema_version must be 2")
    per_criterion = pack["policy"].get("max_evidence_per_criterion")
    max_unique = pack["policy"].get("max_unique_evidence")
    selected: dict[str, dict[str, Any]] = {}
    for index, claim in enumerate(pack["claims"]):
        claim_id = claim.get("id")
        source = claims.get(claim_id)
        if source is None:
            errors.append(f"claims[{index}] references unknown claim {claim_id}")
            continue
        if claim_id in selected:
            errors.append(f"claims[{index}] duplicates {claim_id}")
        selected[claim_id] = claim
        if not source["resume_safe"] or source["status"] in {"unverified", "conflicting"}:
            errors.append(f"claims[{index}] is not safe for a writer context")
        if source["sensitivity"] == "confidential":
            errors.append(f"claims[{index}] is confidential")
        if claim.get("use_status") not in {"include", "maybe"}:
            errors.append(f"claims[{index}].use_status is invalid")
        for field in ("statement", "source_file", "project_id", "resume_safe"):
            if claim.get(field) != source[field]:
                errors.append(f"claims[{index}].{field} disagrees with the claim index")
    cards: dict[str, dict[str, Any]] = {}
    for index, card in enumerate(pack["evidence_cards"]):
        label = f"evidence_cards[{index}]"
        card_id = card.get("id") if isinstance(card, dict) else None
        if not isinstance(card_id, str) or not card_id:
            errors.append(f"{label}.id must be a non-empty string")
            continue
        if card_id in cards:
            errors.append(f"{label}.id is duplicated")
        cards[card_id] = card
        if card.get("use_status") not in {"include", "maybe"}:
            errors.append(f"{label}.use_status is invalid")
        excerpt = card.get("excerpt")
        if not isinstance(excerpt, str) or not excerpt.strip():
            errors.append(f"{label}.excerpt must be non-empty")
        elif card.get("excerpt_sha256") != hashlib.sha256(excerpt.encode("utf-8")).hexdigest():
            errors.append(f"{label}.excerpt_sha256 is invalid")
        claim_ids = card.get("claim_ids")
        if not isinstance(claim_ids, list) or any(item not in selected for item in claim_ids):
            errors.append(f"{label}.claim_ids must reference selected claims")
        source_file = card.get("source_file")
        start = card.get("line_start")
        end = card.get("line_end")
        if not isinstance(source_file, str) or type(start) is not int or type(end) is not int or start < 1 or end < start:
            errors.append(f"{label} has invalid source provenance")
        elif source_root is not None:
            source = (source_root / source_file).resolve()
            try:
                source.relative_to(source_root.resolve())
            except ValueError:
                errors.append(f"{label}.source_file escapes source root")
            else:
                if not source.is_file():
                    errors.append(f"{label}.source_file is missing")
                else:
                    lines = source.read_text(encoding="utf-8-sig").splitlines()
                    if end > len(lines) or "\n".join(lines[start - 1 : end]) != excerpt:
                        errors.append(f"{label} does not match its exact source lines")
    if isinstance(max_unique, int) and len(cards) > max_unique:
        errors.append("context pack exceeds its unique evidence cap")

    decisions = {"include": 0, "maybe": 0, "exclude": 0}
    for index, criterion in enumerate(pack["criteria"]):
        included = criterion.get("include_evidence_ids", [])
        maybe = criterion.get("maybe_evidence_ids", [])
        if set(included) & set(maybe):
            errors.append(f"criteria[{index}] includes the same evidence in include and maybe")
        if isinstance(per_criterion, int) and len(included) + len(maybe) > per_criterion:
            errors.append(f"criteria[{index}] exceeds its evidence cap")
        for evidence_id in [*included, *maybe]:
            if evidence_id not in cards:
                errors.append(f"criteria[{index}] references unselected evidence {evidence_id}")
        decision = criterion.get("decision")
        if decision not in decisions:
            errors.append(f"criteria[{index}].decision is invalid")
            continue
        decisions[decision] += 1
        expected = "include" if included else "maybe" if maybe else "exclude"
        if decision != expected:
            errors.append(f"criteria[{index}].decision should be {expected}")

    summary = pack["summary"]
    expected_summary = {
        "criterion_count": len(pack["criteria"]),
        "included_criteria": decisions["include"],
        "maybe_criteria": decisions["maybe"],
        "excluded_criteria": decisions["exclude"],
        "selected_unique_claims": len(selected),
        "selected_unique_evidence": len(cards),
        "excluded_items": len(pack["exclusions"]),
    }
    for field, expected in expected_summary.items():
        if summary.get(field) != expected:
            errors.append(f"summary.{field} should be {expected}")
    expected_status = "ready" if cards else "needs-knowledge-base-work"
    if summary.get("status") != expected_status:
        errors.append(f"summary.status should be {expected_status}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("candidate-pool", "context-pack"))
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--claim-index",
        type=Path,
        help="Immutable claim-index snapshot; defaults to the repository index",
    )
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        artifact = load_json(args.artifact)
        claim_index = (
            args.claim_index.resolve()
            if args.claim_index
            else root / "knowledge-base" / "generated" / "claims.jsonl"
        )
        claims = load_claims(claim_index)
        if args.kind == "candidate-pool":
            errors = validate_candidate_pool(artifact, root, claims)
        else:
            errors = validate_context_pack(
                artifact,
                claims,
                args.source_root.resolve() if args.source_root else None,
            )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated {args.kind}: {args.artifact.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
