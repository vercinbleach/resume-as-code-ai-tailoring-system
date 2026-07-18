#!/usr/bin/env python3
"""Rank structured resume claims for atomic job criteria without an LLM."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from context_common import extract_criteria, job_identity, load_claims, load_json, normalize, sha256_file, tokens


STOPWORDS = {
    "ability", "and", "are", "build", "building", "comfortable", "experience",
    "for", "have", "including", "into", "not", "of", "or", "such", "that",
    "the", "their", "this", "to", "using", "with", "work", "working",
}


def useful_tokens(value: str) -> set[str]:
    return {token for token in tokens(value) if token not in STOPWORDS}


def claim_fields(claim: dict[str, Any]) -> dict[str, set[str]]:
    return {
        "statement": useful_tokens(claim["statement"]),
        "technologies": useful_tokens(" ".join(claim["technologies"])),
        "aliases": useful_tokens(" ".join(claim["aliases"])),
        "dimensions": useful_tokens(" ".join(claim["dimensions"])),
    }


def inverse_document_frequency(fields: dict[str, dict[str, set[str]]]) -> dict[str, float]:
    document_frequency: Counter[str] = Counter()
    for values in fields.values():
        combined: set[str] = set()
        for field_tokens in values.values():
            combined.update(field_tokens)
        document_frequency.update(combined)
    count = len(fields)
    return {
        token: math.log((count + 1) / (frequency + 1)) + 1
        for token, frequency in document_frequency.items()
    }


def score_claim(
    criterion: dict[str, Any],
    claim: dict[str, Any],
    fields: dict[str, set[str]],
    idf: dict[str, float],
) -> tuple[float, list[str]]:
    search_terms = [criterion["text"], *criterion.get("search_terms", [])]
    query_tokens: set[str] = set()
    for term in search_terms:
        query_tokens.update(useful_tokens(term))

    score = 0.0
    signals: list[str] = []
    weights = {"statement": 1.0, "technologies": 3.5, "aliases": 2.5, "dimensions": 2.0}
    for field_name, weight in weights.items():
        overlap = sorted(query_tokens & fields[field_name])
        for token in overlap:
            score += idf.get(token, 1.0) * weight
            signals.append(f"{field_name}:{token}")

    normalized_statement = normalize(claim["statement"])
    normalized_technologies = {normalize(value) for value in claim["technologies"]}
    normalized_aliases = {normalize(value) for value in claim["aliases"]}
    for term in search_terms:
        normalized_term = normalize(term)
        if len(normalized_term) < 3:
            continue
        if normalized_term in normalized_technologies:
            score += 6.0
            signals.append(f"exact-technology:{normalized_term}")
        if normalized_term in normalized_aliases:
            score += 5.0
            signals.append(f"exact-alias:{normalized_term}")
        if normalized_term in normalized_statement:
            score += 3.0
            signals.append(f"statement-phrase:{normalized_term}")

    return score, sorted(set(signals))


def knowledge_coverage(root: Path, claims: dict[str, dict[str, Any]]) -> dict[str, Any]:
    structured = sorted({claim["source_file"] for claim in claims.values()})
    candidates: list[str] = []
    for path in sorted((root / "knowledge-base").rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        parts = path.relative_to(root / "knowledge-base").parts
        if parts[0] in {"contracts", "generated"} or path.name == "README.md":
            continue
        candidates.append(relative)
    unstructured = sorted(set(candidates) - set(structured))
    return {
        "claim_count": len(claims),
        "structured_source_count": len(structured),
        "unstructured_source_count": len(unstructured),
        "structured_sources": structured,
        "unstructured_sources": unstructured,
        "limitation": "Narrative-only files are ranked for coverage work but never returned as usable resume evidence.",
    }


def narrative_documents(root: Path, structured_sources: set[str]) -> dict[str, str]:
    documents: dict[str, str] = {}
    for path in sorted((root / "knowledge-base").rglob("*.md")):
        parts = path.relative_to(root / "knowledge-base").parts
        relative = path.relative_to(root).as_posix()
        if (
            parts[0] in {"contracts", "generated"}
            or path.name == "README.md"
            or relative in structured_sources
        ):
            continue
        documents[relative] = path.read_text(encoding="utf-8")
    return documents


def rank_narrative_sources(
    criterion: dict[str, Any],
    documents: dict[str, str],
    limit: int = 3,
) -> list[dict[str, Any]]:
    query = useful_tokens(" ".join([criterion["text"], *criterion.get("search_terms", [])]))
    ranked: list[dict[str, Any]] = []
    for source_file, content in documents.items():
        content_tokens = useful_tokens(content)
        path_tokens = useful_tokens(source_file)
        content_overlap = sorted(query & content_tokens)
        path_overlap = sorted(query & path_tokens)
        score = len(content_overlap) + (2 * len(path_overlap))
        normalized_query = normalize(criterion["text"])
        if normalized_query and normalized_query in normalize(content):
            score += 3
        if score <= 0:
            continue
        signals = [f"content:{token}" for token in content_overlap]
        signals.extend(f"path:{token}" for token in path_overlap)
        ranked.append(
            {"source_file": source_file, "score": float(score), "signals": sorted(set(signals))}
        )
    ranked.sort(key=lambda item: (-item["score"], item["source_file"]))
    return ranked[:limit]


def retrieve(
    root: Path,
    intake_path: Path,
    claims_path: Path,
    max_per_criterion: int,
    min_score: float,
) -> dict[str, Any]:
    intake = load_json(intake_path)
    claims = load_claims(claims_path)
    criteria = extract_criteria(intake)
    fields = {claim_id: claim_fields(claim) for claim_id, claim in claims.items()}
    idf = inverse_document_frequency(fields)
    structured_sources = {claim["source_file"] for claim in claims.values()}
    narratives = narrative_documents(root, structured_sources)

    results: list[dict[str, Any]] = []
    for criterion in criteria:
        ranked: list[dict[str, Any]] = []
        for claim_id, claim in claims.items():
            score, signals = score_claim(criterion, claim, fields[claim_id], idf)
            if score < min_score:
                continue
            ranked.append(
                {
                    "claim_id": claim_id,
                    "score": round(score, 3),
                    "signals": signals,
                    "status": claim["status"],
                    "resume_safe": claim["resume_safe"],
                    "source_file": claim["source_file"],
                }
            )
        ranked.sort(key=lambda item: (-item["score"], item["claim_id"]))
        results.append(
            {
                **criterion,
                "candidates": ranked[:max_per_criterion],
                "narrative_candidates": rank_narrative_sources(criterion, narratives),
            }
        )

    return {
        "schema_version": 1,
        "job": job_identity(intake),
        "inputs": {
            "job_intake": intake_path.resolve().as_posix(),
            "job_intake_sha256": sha256_file(intake_path),
            "claim_index": claims_path.resolve().as_posix(),
            "claim_index_sha256": sha256_file(claims_path),
        },
        "retrieval": {
            "engine": "lexical-idf-metadata-v1",
            "semantic_model": None,
            "max_candidates_per_criterion": max_per_criterion,
            "minimum_score": min_score,
            "ranking_signals": ["statement", "technologies", "aliases", "dimensions", "idf"],
        },
        "coverage": knowledge_coverage(root, claims),
        "criteria": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-intake", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-per-criterion", type=int, default=8)
    parser.add_argument("--min-score", type=float, default=1.5)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    if not 1 <= args.max_per_criterion <= 20:
        parser.error("--max-per-criterion must be between 1 and 20")
    if args.min_score < 0:
        parser.error("--min-score cannot be negative")

    root = args.root.resolve()
    claims_path = root / "knowledge-base" / "generated" / "claims.jsonl"
    try:
        result = retrieve(
            root,
            args.job_intake.resolve(),
            claims_path,
            args.max_per_criterion,
            args.min_score,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
