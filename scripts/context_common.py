#!/usr/bin/env python3
"""Shared deterministic helpers for resume context retrieval and assembly."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable


CRITERION_KINDS = {
    "eligibility",
    "must-have",
    "preferred",
    "responsibility",
    "unclear",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9+#.]+", " ", ascii_text.casefold()).strip()


def tokens(value: str) -> set[str]:
    return {token for token in normalize(value).split() if len(token) > 1}


def load_claims(path: Path) -> dict[str, dict[str, Any]]:
    claims: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        claim = json.loads(line)
        claim_id = claim.get("id")
        if not isinstance(claim_id, str):
            raise ValueError(f"{path}:{line_number}: claim has no string id")
        if claim_id in claims:
            raise ValueError(f"{path}:{line_number}: duplicate claim ID {claim_id}")
        claims[claim_id] = claim
    if not claims:
        raise ValueError(f"No claims found in {path}")
    return claims


def _fallback_items(job: dict[str, Any]) -> Iterable[tuple[str, list[dict[str, Any]]]]:
    requirements = job.get("requirements", {})
    yield "must-have", requirements.get("must_have", [])
    yield "preferred", requirements.get("preferred", [])
    yield "unclear", requirements.get("unclear", [])
    yield "responsibility", job.get("responsibilities", [])


def extract_criteria(intake: dict[str, Any]) -> list[dict[str, Any]]:
    job = intake.get("job")
    if not isinstance(job, dict):
        raise ValueError("job-intake.json has no job object")

    supplied = job.get("criteria")
    if isinstance(supplied, list) and supplied:
        criteria: list[dict[str, Any]] = []
        for item in supplied:
            criteria.append(
                {
                    "id": item["id"],
                    "text": item["text"],
                    "kind": item["kind"],
                    "search_terms": list(item.get("search_terms", [])),
                    "source": item.get("source"),
                }
            )
        return criteria

    criteria = []
    seen_text: set[str] = set()
    counters: dict[str, int] = {}
    for kind, items in _fallback_items(job):
        for item in items:
            text = item.get("text") if isinstance(item, dict) else None
            if not isinstance(text, str) or not text.strip():
                continue
            normalized = normalize(text)
            if normalized in seen_text:
                continue
            seen_text.add(normalized)
            counters[kind] = counters.get(kind, 0) + 1
            criteria.append(
                {
                    "id": f"{kind}-{counters[kind]:03d}",
                    "text": text.strip(),
                    "kind": kind,
                    "search_terms": [],
                    "source": item.get("source"),
                }
            )
    if not criteria:
        raise ValueError("No atomic or fallback job criteria were found")
    return criteria


def job_identity(intake: dict[str, Any]) -> dict[str, Any]:
    job = intake["job"]
    capture = intake.get("capture", {})
    return {
        "company": job.get("company"),
        "title": job.get("title"),
        "job_id": job.get("job_id"),
        "source_url": capture.get("canonical_url") or capture.get("source_url"),
    }
