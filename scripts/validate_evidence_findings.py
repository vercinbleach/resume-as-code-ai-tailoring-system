#!/usr/bin/env python3
"""Validate evidence-review and claim-use-critic packets with exact source spans."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT_KEYS = {"schema_version", "role", "findings"}
FINDING_KEYS = {
    "finding_id",
    "criterion_id",
    "status",
    "evidence_strength",
    "evidence_units",
    "reason",
    "caveats",
    "follow_up_questions",
    "resume_safe",
}
UNIT_KEYS = {
    "evidence_id",
    "source_file",
    "line_start",
    "line_end",
    "excerpt",
    "claim_ids",
}
ROLES = {"evidence-reviewer", "claim-risk-critic"}
STATUSES = {"strong", "partial", "missing", "conflict"}
STRENGTHS = {"high", "medium", "low", "none"}
FINDING_ID_RE = re.compile(r"^finding-[a-z0-9]+(?:-[a-z0-9]+)*$")
EVIDENCE_ID_RE = re.compile(r"^evidence-[a-z0-9]+(?:-[a-z0-9]+)*$")


def _load_index(path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    claims: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    if not path.exists():
        return {}, [f"claim index does not exist: {path}"]
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            claim = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_number}: invalid JSON: {exc}")
            continue
        claim_id = claim.get("id")
        if not isinstance(claim_id, str):
            errors.append(f"{path}:{line_number}: claim has no string id")
        elif claim_id in claims:
            errors.append(f"{path}:{line_number}: duplicate claim ID {claim_id}")
        else:
            claims[claim_id] = claim
    return claims, errors


def _string_array(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
        and len(value) == len(set(value))
    )


def _safe_source(source_root: Path, relative: str) -> Path | None:
    if not relative.endswith(".md") or "\\" in relative:
        return None
    candidate = (source_root / relative).resolve()
    try:
        candidate.relative_to(source_root.resolve())
    except ValueError:
        return None
    return candidate


def _validate_unit(
    unit: Any,
    label: str,
    claims: dict[str, dict[str, Any]],
    errors: list[str],
    source_root: Path | None,
) -> str | None:
    if not isinstance(unit, dict) or set(unit) != UNIT_KEYS:
        errors.append(f"{label} must contain exactly {sorted(UNIT_KEYS)}")
        return None
    evidence_id = unit["evidence_id"]
    if not isinstance(evidence_id, str) or not EVIDENCE_ID_RE.fullmatch(evidence_id):
        errors.append(f"{label}.evidence_id is invalid")
        evidence_id = None
    source_file = unit["source_file"]
    if not isinstance(source_file, str) or not source_file.startswith("knowledge-base/"):
        errors.append(f"{label}.source_file must be a knowledge-base Markdown path")
    start = unit["line_start"]
    end = unit["line_end"]
    if type(start) is not int or type(end) is not int or start < 1 or end < start:
        errors.append(f"{label} must have a valid inclusive line range")
    excerpt = unit["excerpt"]
    if not isinstance(excerpt, str) or not excerpt.strip() or excerpt != excerpt.strip("\n"):
        errors.append(f"{label}.excerpt must be non-empty and omit outer newlines")
    elif len(excerpt) > 12000:
        errors.append(f"{label}.excerpt exceeds 12000 characters")
    claim_ids = unit["claim_ids"]
    if not _string_array(claim_ids):
        errors.append(f"{label}.claim_ids must be a unique string array")
        claim_ids = []
    for claim_id in claim_ids:
        claim = claims.get(claim_id)
        if claim is None:
            errors.append(f"{label}: unknown claim ID {claim_id}")
        elif claim.get("source_file") != source_file:
            errors.append(f"{label}: claim {claim_id} belongs to another source file")
    if source_root is not None and isinstance(source_file, str):
        source = _safe_source(source_root, source_file)
        if source is None or not source.is_file():
            errors.append(f"{label}: source file is missing or unsafe: {source_file}")
        elif type(start) is int and type(end) is int and start >= 1 and end >= start:
            lines = source.read_text(encoding="utf-8-sig").splitlines()
            if end > len(lines):
                errors.append(f"{label}: line range exceeds {source_file}")
            elif isinstance(excerpt, str) and "\n".join(lines[start - 1 : end]) != excerpt:
                errors.append(f"{label}: excerpt does not exactly match its source lines")
    return evidence_id


def validate_packet(
    packet: Any,
    claims: dict[str, dict[str, Any]],
    source_root: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(packet, dict):
        return ["packet root must be an object"]
    if set(packet) != ROOT_KEYS:
        return [f"packet root must contain exactly {sorted(ROOT_KEYS)}"]
    if packet["schema_version"] != 3:
        errors.append("schema_version must be 3")
    role = packet["role"]
    if role not in ROLES:
        errors.append(f"role must be one of {sorted(ROLES)}")
    if not isinstance(packet["findings"], list):
        return errors + ["findings must be an array"]

    finding_ids: set[str] = set()
    evidence_ids: set[str] = set()
    use_keys: set[tuple[str, str]] = set()
    for index, finding in enumerate(packet["findings"]):
        label = f"findings[{index}]"
        if not isinstance(finding, dict) or set(finding) != FINDING_KEYS:
            errors.append(f"{label} must contain exactly {sorted(FINDING_KEYS)}")
            continue
        finding_id = finding["finding_id"]
        if not isinstance(finding_id, str) or not FINDING_ID_RE.fullmatch(finding_id):
            errors.append(f"{label}.finding_id is invalid")
        elif finding_id in finding_ids:
            errors.append(f"{label}.finding_id is duplicated")
        else:
            finding_ids.add(finding_id)
        criterion_id = finding["criterion_id"]
        if not isinstance(criterion_id, str) or not criterion_id.strip():
            errors.append(f"{label}.criterion_id must be a non-empty string")
            criterion_id = ""
        if finding["status"] not in STATUSES:
            errors.append(f"{label}.status is invalid")
        if finding["evidence_strength"] not in STRENGTHS:
            errors.append(f"{label}.evidence_strength is invalid")
        if not isinstance(finding["reason"], str) or not finding["reason"].strip():
            errors.append(f"{label}.reason must be a non-empty string")
        if not _string_array(finding["caveats"]):
            errors.append(f"{label}.caveats must be a unique string array")
        if not _string_array(finding["follow_up_questions"]):
            errors.append(f"{label}.follow_up_questions must be a unique string array")
        if not isinstance(finding["resume_safe"], bool):
            errors.append(f"{label}.resume_safe must be boolean")
        units = finding["evidence_units"]
        if not isinstance(units, list):
            errors.append(f"{label}.evidence_units must be an array")
            continue
        if finding["status"] == "missing":
            if units:
                errors.append(f"{label}: missing findings cannot contain evidence units")
            if finding["evidence_strength"] != "none" or finding["resume_safe"]:
                errors.append(f"{label}: missing findings require none strength and resume_safe false")
        elif not units:
            errors.append(f"{label}: non-missing findings require evidence units")
        if role == "claim-risk-critic" and len(units) != 1:
            errors.append(f"{label}: critic findings must contain exactly one evidence unit")

        referenced_claims: list[dict[str, Any]] = []
        for unit_index, unit in enumerate(units):
            unit_label = f"{label}.evidence_units[{unit_index}]"
            evidence_id = _validate_unit(unit, unit_label, claims, errors, source_root)
            if evidence_id:
                if evidence_id in evidence_ids:
                    errors.append(f"{unit_label}.evidence_id is duplicated")
                else:
                    evidence_ids.add(evidence_id)
                key = (criterion_id, evidence_id)
                if key in use_keys:
                    errors.append(f"{unit_label}: duplicate criterion and evidence use")
                else:
                    use_keys.add(key)
            if isinstance(unit, dict) and isinstance(unit.get("claim_ids"), list):
                referenced_claims.extend(
                    claims[item] for item in unit["claim_ids"] if item in claims
                )
        if finding["resume_safe"] and any(not claim.get("resume_safe") for claim in referenced_claims):
            errors.append(f"{label}: cannot be resume_safe because a referenced claim is unsafe")
        if finding["status"] == "strong" and any(
            claim.get("status") in {"unverified", "conflicting"} for claim in referenced_claims
        ):
            errors.append(f"{label}: strong findings cannot rely on unsafe claim status")
        if finding["status"] in {"missing", "conflict"} and finding["resume_safe"]:
            errors.append(f"{label}: missing or conflicting findings cannot be resume_safe")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--claim-index", type=Path)
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    claim_index = args.claim_index.resolve() if args.claim_index else root / "knowledge-base/generated/claims.jsonl"
    claims, errors = _load_index(claim_index)
    try:
        packet = json.loads(args.packet.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"could not read evidence packet: {exc}")
        packet = None
    errors.extend(validate_packet(packet, claims, args.source_root.resolve() if args.source_root else None))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated {len(packet['findings'])} findings from {packet['role']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
