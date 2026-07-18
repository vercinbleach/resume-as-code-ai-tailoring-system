#!/usr/bin/env python3
"""Assemble reviewed and use-audited source evidence into a bounded context pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from context_common import extract_criteria, job_identity, load_claims, load_json, sha256_file
from validate_evidence_findings import validate_packet


EVIDENCE_RANK = {"strong": 0, "partial": 1, "conflict": 2, "missing": 3}
STRENGTH_RANK = {"high": 0, "medium": 1, "low": 2, "none": 3}


def unique_strings(values: list[str]) -> list[str]:
    return sorted({value.strip() for value in values if isinstance(value, str) and value.strip()})


def load_packet(path: Path, claims: dict[str, dict[str, Any]], source_root: Path) -> dict[str, Any]:
    packet = load_json(path)
    errors = validate_packet(packet, claims, source_root)
    if errors:
        raise ValueError(f"Invalid evidence packet {path}: {'; '.join(errors)}")
    return packet


def units_by_use(packet: dict[str, Any]) -> dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any]]]:
    result: dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any]]] = {}
    for finding in packet["findings"]:
        for unit in finding["evidence_units"]:
            result[(finding["criterion_id"], unit["evidence_id"])] = (finding, unit)
    return result


def validate_critic_coverage(
    reviewer_packet: dict[str, Any], critic_packet: dict[str, Any]
) -> dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any]]]:
    reviewer = units_by_use(reviewer_packet)
    critic = units_by_use(critic_packet)
    missing = sorted(set(reviewer) - set(critic))
    extra = sorted(set(critic) - set(reviewer))
    errors: list[str] = []
    if missing:
        errors.append("critic omitted proposed evidence uses: " + ", ".join(f"{a}/{b}" for a, b in missing))
    if extra:
        errors.append("critic added unproposed evidence uses: " + ", ".join(f"{a}/{b}" for a, b in extra))
    for key in sorted(set(reviewer) & set(critic)):
        if reviewer[key][1] != critic[key][1]:
            errors.append(f"critic changed evidence unit {key[0]}/{key[1]}")
    if errors:
        raise ValueError("; ".join(errors))
    return critic


def _frontmatter(source: Path) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8-sig")
    if not text.startswith("---\n"):
        return {}
    marker = text.find("\n---", 4)
    if marker == -1:
        return {}
    value = yaml.safe_load(text[4:marker])
    return value if isinstance(value, dict) else {}


def _source_metadata(source_root: Path, source_file: str) -> dict[str, Any]:
    metadata = _frontmatter(source_root / source_file)
    allowed = ("id", "name", "aliases", "organization", "related_experience", "repository", "type")
    return {key: metadata[key] for key in allowed if key in metadata}


def _unit_status(
    reviewer: dict[str, Any], critic: dict[str, Any], unit: dict[str, Any], claims: dict[str, dict[str, Any]]
) -> tuple[str | None, str | None]:
    if reviewer["status"] in {"missing", "conflict"} or not reviewer["resume_safe"]:
        return None, "evidence reviewer rejected this source use"
    if critic["status"] in {"missing", "conflict"} or not critic["resume_safe"]:
        return None, "claim-use critic rejected this source use"
    linked = [claims[item] for item in unit["claim_ids"]]
    for claim in linked:
        if not claim["resume_safe"] or claim["sensitivity"] == "confidential":
            return None, "linked claim is not resume safe"
        if claim["status"] in {"unverified", "conflicting"}:
            return None, f"linked claim status is {claim['status']}"
    if reviewer["status"] == "partial" or critic["status"] == "partial" or any(
        claim["status"] == "partial" for claim in linked
    ):
        return "maybe", None
    return "include", None


def assemble(
    intake_path: Path,
    claim_index_path: Path,
    candidate_path: Path,
    evidence_path: Path,
    critic_path: Path,
    source_root: Path,
    max_per_criterion: int,
    max_total: int,
) -> dict[str, Any]:
    intake = load_json(intake_path)
    criteria = extract_criteria(intake)
    criterion_map = {criterion["id"]: criterion for criterion in criteria}
    claims = load_claims(claim_index_path)
    candidate_pool = load_json(candidate_path)
    candidate_inputs = candidate_pool.get("inputs", {})
    if candidate_inputs.get("job_intake_sha256") != sha256_file(intake_path):
        raise ValueError("Candidate pool does not belong to the supplied job-intake snapshot")
    if candidate_inputs.get("claim_index_sha256") != sha256_file(claim_index_path):
        raise ValueError("Candidate pool does not belong to the supplied claim-index snapshot")
    narrative_by_criterion = {
        item["id"]: item.get("narrative_candidates", []) for item in candidate_pool.get("criteria", [])
    }

    reviewer_packet = load_packet(evidence_path, claims, source_root)
    critic_packet = load_packet(critic_path, claims, source_root)
    if reviewer_packet["role"] != "evidence-reviewer":
        raise ValueError("--evidence-review must point to evidence-reviewer output")
    if critic_packet["role"] != "claim-risk-critic":
        raise ValueError("--claim-use-risk must point to claim-risk-critic output")
    critic_map = validate_critic_coverage(reviewer_packet, critic_packet)

    findings_by_criterion: dict[str, list[dict[str, Any]]] = {}
    for finding in reviewer_packet["findings"]:
        if finding["criterion_id"] not in criterion_map:
            raise ValueError(f"evidence-reviewer referenced unknown criterion {finding['criterion_id']}")
        findings_by_criterion.setdefault(finding["criterion_id"], []).append(finding)

    selected_cards: dict[str, dict[str, Any]] = {}
    selected_claim_status: dict[str, str] = {}
    criterion_rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []

    for criterion in criteria:
        entries = findings_by_criterion.get(criterion["id"], [])
        candidates: list[tuple[dict[str, Any], dict[str, Any]]] = []
        reasons: list[str] = []
        caveats: list[str] = []
        questions: list[str] = []
        for finding in entries:
            reasons.append(f"evidence-reviewer: {finding['reason']}")
            caveats.extend(finding["caveats"])
            questions.extend(finding["follow_up_questions"])
            candidates.extend((finding, unit) for unit in finding["evidence_units"])
            if not finding["evidence_units"]:
                exclusions.append({"criterion_id": criterion["id"], "evidence_id": None, "reason": finding["reason"]})

        ordered = sorted(
            candidates,
            key=lambda item: (
                EVIDENCE_RANK[item[0]["status"]],
                STRENGTH_RANK[item[0]["evidence_strength"]],
                item[1]["evidence_id"],
            ),
        )
        include_ids: list[str] = []
        maybe_ids: list[str] = []
        for reviewer, unit in ordered:
            critic, _ = critic_map[(criterion["id"], unit["evidence_id"])]
            reasons.append(f"claim-risk-critic: {critic['reason']}")
            caveats.extend(critic["caveats"])
            questions.extend(critic["follow_up_questions"])
            status, rejection = _unit_status(reviewer, critic, unit, claims)
            if rejection:
                exclusions.append({"criterion_id": criterion["id"], "evidence_id": unit["evidence_id"], "reason": rejection})
                continue
            if len(include_ids) + len(maybe_ids) >= max_per_criterion:
                exclusions.append({"criterion_id": criterion["id"], "evidence_id": unit["evidence_id"], "reason": "per-criterion context cap reached"})
                continue
            if unit["evidence_id"] not in selected_cards and len(selected_cards) >= max_total:
                exclusions.append({"criterion_id": criterion["id"], "evidence_id": unit["evidence_id"], "reason": "global context cap reached"})
                continue
            linked_claims = [claims[item] for item in unit["claim_ids"]]
            card = {
                "id": unit["evidence_id"],
                "criterion_id": criterion["id"],
                "source_file": unit["source_file"],
                "line_start": unit["line_start"],
                "line_end": unit["line_end"],
                "excerpt": unit["excerpt"],
                "excerpt_sha256": hashlib.sha256(unit["excerpt"].encode("utf-8")).hexdigest(),
                "claim_ids": unit["claim_ids"],
                "technologies": unique_strings([tech for claim in linked_claims for tech in claim.get("technologies", [])]),
                "source_metadata": _source_metadata(source_root, unit["source_file"]),
                "reason": reviewer["reason"],
                "caveats": unique_strings(reviewer["caveats"] + critic["caveats"] + [c for claim in linked_claims for c in claim.get("caveats", [])]),
                "use_status": status,
            }
            selected_cards[unit["evidence_id"]] = card
            for claim_id in unit["claim_ids"]:
                if selected_claim_status.get(claim_id) != "include":
                    selected_claim_status[claim_id] = status
            (include_ids if status == "include" else maybe_ids).append(unit["evidence_id"])

        decision = "include" if include_ids else "maybe" if maybe_ids else "exclude"
        if not entries:
            reasons.append("No evidence reviewer finding reported this criterion.")
        criterion_rows.append({
            "criterion_id": criterion["id"],
            "text": criterion["text"],
            "kind": criterion["kind"],
            "decision": decision,
            "include_evidence_ids": include_ids,
            "maybe_evidence_ids": maybe_ids,
            "reasons": unique_strings(reasons),
            "caveats": unique_strings(caveats),
            "follow_up_questions": unique_strings(questions),
        })

    claim_rows = [{**claims[item], "use_status": selected_claim_status[item]} for item in sorted(selected_claim_status)]
    cards = [selected_cards[item] for item in sorted(selected_cards)]
    coverage_queue: list[dict[str, Any]] = []
    for row in criterion_rows:
        if row["decision"] == "include":
            continue
        for candidate in narrative_by_criterion.get(row["criterion_id"], [])[:3]:
            coverage_queue.append({
                "criterion_id": row["criterion_id"],
                "source_file": candidate["source_file"],
                "retrieval_score": candidate["score"],
                "reason": "Potential source was not approved as an include evidence unit.",
            })
    include_count = sum(row["decision"] == "include" for row in criterion_rows)
    maybe_count = sum(row["decision"] == "maybe" for row in criterion_rows)
    return {
        "schema_version": 2,
        "job": job_identity(intake),
        "inputs": {
            "job_intake_sha256": sha256_file(intake_path),
            "claim_index_sha256": sha256_file(claim_index_path),
            "candidate_pool_sha256": sha256_file(candidate_path),
            "evidence_review": {"role": reviewer_packet["role"], "sha256": sha256_file(evidence_path)},
            "claim_use_risk": {"role": critic_packet["role"], "sha256": sha256_file(critic_path)},
        },
        "policy": {
            "max_evidence_per_criterion": max_per_criterion,
            "max_unique_evidence": max_total,
            "include_rule": "Use only exact source evidence approved by both reviewer and critic.",
            "maybe_rule": "Maybe evidence is not available to isolated Writers.",
            "exclude_rule": "Excluded evidence is never usable support.",
        },
        "summary": {
            "status": "ready" if cards else "needs-knowledge-base-work",
            "criterion_count": len(criterion_rows),
            "included_criteria": include_count,
            "maybe_criteria": maybe_count,
            "excluded_criteria": len(criterion_rows) - include_count - maybe_count,
            "selected_unique_evidence": len(cards),
            "selected_unique_claims": len(claim_rows),
            "excluded_items": len(exclusions),
        },
        "criteria": criterion_rows,
        "evidence_cards": cards,
        "claims": claim_rows,
        "coverage_queue": sorted(coverage_queue, key=lambda item: (item["criterion_id"], -item["retrieval_score"], item["source_file"])),
        "exclusions": sorted(exclusions, key=lambda item: (item["criterion_id"], item["evidence_id"] or "", item["reason"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-intake", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--evidence-review", required=True, type=Path)
    parser.add_argument("--claim-use-risk", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-per-criterion", type=int, default=3)
    parser.add_argument("--max-total", type=int, default=20)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--claim-index", type=Path)
    args = parser.parse_args()
    if not 1 <= args.max_per_criterion <= 10 or not 1 <= args.max_total <= 50:
        parser.error("context caps are outside allowed ranges")
    root = args.root.resolve()
    claim_index = args.claim_index.resolve() if args.claim_index else root / "knowledge-base/generated/claims.jsonl"
    try:
        result = assemble(
            args.job_intake.resolve(), claim_index, args.candidates.resolve(),
            args.evidence_review.resolve(), args.claim_use_risk.resolve(), args.source_root.resolve(),
            args.max_per_criterion, args.max_total,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
