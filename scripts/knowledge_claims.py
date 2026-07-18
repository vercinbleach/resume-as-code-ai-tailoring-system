#!/usr/bin/env python3
"""Validate structured knowledge-base claims and build a deterministic index."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


START_MARKER = "<!-- structured-claims:start -->"
END_MARKER = "<!-- structured-claims:end -->"
SCHEMA_VERSION = 1

CLAIM_KEYS = {
    "id",
    "statement",
    "dimensions",
    "technologies",
    "evidence",
    "confidence",
    "status",
    "resume_safe",
    "sensitivity",
    "aliases",
    "caveats",
}
GAP_KEYS = {"id", "question", "importance", "status", "affects_claims"}
EVIDENCE_KEYS = {"source_type", "locator", "checked"}

DIMENSIONS = {
    "ai",
    "collaboration",
    "impact",
    "infrastructure",
    "leadership",
    "open-source",
    "operations",
    "product",
    "reliability",
    "security",
    "technical",
}
SOURCE_TYPES = {
    "historical-cv",
    "inferred",
    "linkedin",
    "local-verification",
    "repository-verified",
    "user-confirmed",
}
CONFIDENCE = {"high", "medium", "low"}
CLAIM_STATUS = {"confirmed", "partial", "unverified", "conflicting"}
SENSITIVITY = {"public", "internal-anonymized", "confidential"}
IMPORTANCE = {"high", "medium", "low"}
GAP_STATUS = {"open", "resolved", "unrecoverable"}

CLAIM_ID_RE = re.compile(r"^claim-[a-z0-9]+(?:-[a-z0-9]+)*$")
GAP_ID_RE = re.compile(r"^gap-[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class ClaimDocument:
    path: Path
    project_id: str
    payload: dict[str, Any]


def _is_string_list(value: Any, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (not nonempty or bool(value))
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
        and len(value) == len(set(value))
    )


def _project_id(markdown: str) -> str | None:
    if not markdown.startswith("---"):
        return None
    end = markdown.find("\n---", 3)
    if end == -1:
        return None
    match = re.search(r"(?m)^id:\s*([^\s#]+)\s*$", markdown[3:end])
    return match.group(1) if match else None


def extract_claim_document(path: Path) -> tuple[ClaimDocument | None, list[str]]:
    markdown = path.read_text(encoding="utf-8")
    starts = markdown.count(START_MARKER)
    ends = markdown.count(END_MARKER)
    if starts == 0 and ends == 0:
        return None, []
    if starts != 1 or ends != 1:
        return None, [f"{path}: expected exactly one start and end marker"]

    start = markdown.index(START_MARKER) + len(START_MARKER)
    end = markdown.index(END_MARKER, start)
    fenced = markdown[start:end].strip()
    match = re.fullmatch(r"```json\s*\n(.*)\n```", fenced, re.DOTALL)
    if not match:
        return None, [f"{path}: claim block must contain one fenced JSON object"]

    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        return None, [f"{path}: invalid claim JSON: {exc}"]

    project_id = _project_id(markdown)
    if not project_id:
        return None, [f"{path}: participating file needs an id in YAML frontmatter"]
    if not isinstance(payload, dict):
        return None, [f"{path}: claim block root must be an object"]
    return ClaimDocument(path=path, project_id=project_id, payload=payload), []


def _validate_evidence(value: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list) or not value:
        return [f"{label}.evidence must be a non-empty array"]
    for index, item in enumerate(value):
        here = f"{label}.evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{here} must be an object")
            continue
        if set(item) != EVIDENCE_KEYS:
            errors.append(f"{here} must contain exactly {sorted(EVIDENCE_KEYS)}")
            continue
        if item["source_type"] not in SOURCE_TYPES:
            errors.append(f"{here}.source_type is not allowed")
        if not isinstance(item["locator"], str) or not item["locator"].strip():
            errors.append(f"{here}.locator must be a non-empty string")
        try:
            dt.date.fromisoformat(item["checked"])
        except (TypeError, ValueError):
            errors.append(f"{here}.checked must be an ISO date")
    return errors


def _validate_claim(claim: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(claim, dict):
        return [f"{label} must be an object"]
    if set(claim) != CLAIM_KEYS:
        return [f"{label} must contain exactly {sorted(CLAIM_KEYS)}"]

    claim_id = claim["id"]
    if not isinstance(claim_id, str) or not CLAIM_ID_RE.fullmatch(claim_id):
        errors.append(f"{label}.id must be a stable claim-* identifier")
    if not isinstance(claim["statement"], str) or len(claim["statement"].strip()) < 10:
        errors.append(f"{label}.statement must contain one atomic fact")
    if not _is_string_list(claim["dimensions"], nonempty=True):
        errors.append(f"{label}.dimensions must be a non-empty unique string array")
    elif not set(claim["dimensions"]).issubset(DIMENSIONS):
        errors.append(f"{label}.dimensions contains an unsupported dimension")
    if not _is_string_list(claim["technologies"]):
        errors.append(f"{label}.technologies must be a unique string array")
    errors.extend(_validate_evidence(claim["evidence"], label))
    if claim["confidence"] not in CONFIDENCE:
        errors.append(f"{label}.confidence is not allowed")
    if claim["status"] not in CLAIM_STATUS:
        errors.append(f"{label}.status is not allowed")
    if not isinstance(claim["resume_safe"], bool):
        errors.append(f"{label}.resume_safe must be boolean")
    if claim["sensitivity"] not in SENSITIVITY:
        errors.append(f"{label}.sensitivity is not allowed")
    if not _is_string_list(claim["aliases"]):
        errors.append(f"{label}.aliases must be a unique string array")
    if not _is_string_list(claim["caveats"]):
        errors.append(f"{label}.caveats must be a unique string array")

    if claim["status"] in {"unverified", "conflicting"} and claim["resume_safe"]:
        errors.append(f"{label}: unverified or conflicting claims cannot be resume_safe")
    if claim["sensitivity"] == "confidential" and claim["resume_safe"]:
        errors.append(f"{label}: confidential claims cannot be resume_safe")
    if claim["status"] in {"partial", "unverified", "conflicting"} and not claim["caveats"]:
        errors.append(f"{label}: non-confirmed claims need at least one caveat")
    return errors


def _validate_gap(gap: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(gap, dict):
        return [f"{label} must be an object"]
    if set(gap) != GAP_KEYS:
        return [f"{label} must contain exactly {sorted(GAP_KEYS)}"]
    if not isinstance(gap["id"], str) or not GAP_ID_RE.fullmatch(gap["id"]):
        errors.append(f"{label}.id must be a stable gap-* identifier")
    if not isinstance(gap["question"], str) or len(gap["question"].strip()) < 10:
        errors.append(f"{label}.question must be a specific question")
    if gap["importance"] not in IMPORTANCE:
        errors.append(f"{label}.importance is not allowed")
    if gap["status"] not in GAP_STATUS:
        errors.append(f"{label}.status is not allowed")
    if not _is_string_list(gap["affects_claims"]):
        errors.append(f"{label}.affects_claims must be a unique string array")
    elif any(not CLAIM_ID_RE.fullmatch(item) for item in gap["affects_claims"]):
        errors.append(f"{label}.affects_claims contains an invalid claim ID")
    return errors


def validate_documents(documents: Iterable[ClaimDocument]) -> list[str]:
    errors: list[str] = []
    claim_locations: dict[str, Path] = {}
    gap_locations: dict[str, Path] = {}
    gap_references: list[tuple[str, str, Path]] = []

    for document in documents:
        payload = document.payload
        label = str(document.path)
        if set(payload) != {"schema_version", "claims", "evidence_gaps"}:
            errors.append(f"{label}: root must contain schema_version, claims, and evidence_gaps")
            continue
        if payload["schema_version"] != SCHEMA_VERSION:
            errors.append(f"{label}: unsupported schema_version")
        if not isinstance(payload["claims"], list):
            errors.append(f"{label}: claims must be an array")
            continue
        if not isinstance(payload["evidence_gaps"], list):
            errors.append(f"{label}: evidence_gaps must be an array")
            continue

        for index, claim in enumerate(payload["claims"]):
            here = f"{label}:claims[{index}]"
            errors.extend(_validate_claim(claim, here))
            if isinstance(claim, dict) and isinstance(claim.get("id"), str):
                claim_id = claim["id"]
                if claim_id in claim_locations:
                    errors.append(
                        f"{here}: duplicate {claim_id}; first seen in {claim_locations[claim_id]}"
                    )
                else:
                    claim_locations[claim_id] = document.path

        for index, gap in enumerate(payload["evidence_gaps"]):
            here = f"{label}:evidence_gaps[{index}]"
            errors.extend(_validate_gap(gap, here))
            if isinstance(gap, dict) and isinstance(gap.get("id"), str):
                gap_id = gap["id"]
                if gap_id in gap_locations:
                    errors.append(
                        f"{here}: duplicate {gap_id}; first seen in {gap_locations[gap_id]}"
                    )
                else:
                    gap_locations[gap_id] = document.path
                for claim_id in gap.get("affects_claims", []):
                    gap_references.append((gap_id, claim_id, document.path))

    for gap_id, claim_id, path in gap_references:
        if claim_id not in claim_locations:
            errors.append(f"{path}: {gap_id} references unknown {claim_id}")
    return errors


def discover(root: Path) -> tuple[list[ClaimDocument], list[str]]:
    documents: list[ClaimDocument] = []
    errors: list[str] = []
    for path in sorted((root / "knowledge-base").rglob("*.md")):
        relative_parts = path.relative_to(root / "knowledge-base").parts
        if relative_parts[0] in {"contracts", "generated"}:
            continue
        document, extraction_errors = extract_claim_document(path)
        errors.extend(extraction_errors)
        if document:
            documents.append(document)
    errors.extend(validate_documents(documents))
    if not documents:
        errors.append("No structured claim blocks found")
    return documents, errors


def render_index(root: Path, documents: Iterable[ClaimDocument]) -> str:
    rows: list[dict[str, Any]] = []
    for document in documents:
        relative = document.path.relative_to(root).as_posix()
        for claim in document.payload["claims"]:
            rows.append({"project_id": document.project_id, "source_file": relative, **claim})
    rows.sort(key=lambda row: row["id"])
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )


def run(command: str, root: Path) -> int:
    documents, errors = discover(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    index_path = root / "knowledge-base" / "generated" / "claims.jsonl"
    rendered = render_index(root, documents)
    if command == "build":
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"Wrote {sum(len(doc.payload['claims']) for doc in documents)} claims to {index_path}")
    elif command == "check":
        current = index_path.read_text(encoding="utf-8") if index_path.exists() else None
        if current != rendered:
            print(f"ERROR: generated claim index is stale: {index_path}", file=sys.stderr)
            return 1
        print(f"Validated {len(documents)} claim documents and current index")
    else:
        print(
            f"Validated {len(documents)} claim documents with "
            f"{sum(len(doc.payload['claims']) for doc in documents)} claims"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build", "check"))
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root",
    )
    args = parser.parse_args()
    return run(args.command, args.root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
