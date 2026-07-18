#!/usr/bin/env python3
"""Run deterministic Ashby-like full-text search proxies against a resume PDF."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from pypdf import PdfReader


TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9+#./-]*")
MODE_DESCRIPTIONS = {
    "matches": "All query tokens occur somewhere in the extracted resume text, case-insensitive.",
    "contains": "The exact phrase occurs contiguously, case-insensitive.",
    "equals": "The exact phrase occurs contiguously with the same capitalization.",
    "similar": "Local stem/prefix approximation; not Ashby's proprietary similarity implementation.",
}


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def tokens(value: str) -> list[str]:
    return [token.casefold() for token in TOKEN_RE.findall(value)]


def stem(token: str) -> str:
    lowered = token.casefold()
    for suffix in ("ization", "ation", "ments", "ment", "ingly", "edly", "ing", "ers", "er", "ed", "es", "s"):
        if len(lowered) - len(suffix) >= 4 and lowered.endswith(suffix):
            return lowered[: -len(suffix)]
    return lowered


def extracted_text(resume: Path) -> tuple[str, list[str]]:
    reader = PdfReader(str(resume))
    page_texts = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(page_texts)
    return text, [normalize_space(line) for line in text.splitlines() if normalize_space(line)]


def first_snippet(lines: list[str], term: str, mode: str) -> str | None:
    term_fold = term.casefold()
    query_tokens = tokens(term)
    query_stems = [stem(token) for token in query_tokens]
    for line in lines:
        folded = line.casefold()
        if mode == "equals" and term in line:
            return line[:240]
        if mode == "contains" and term_fold in folded:
            return line[:240]
        if mode == "matches" and query_tokens and all(token in tokens(line) for token in query_tokens):
            return line[:240]
        if mode == "similar" and query_stems:
            line_stems = [stem(token) for token in tokens(line)]
            if all(any(item.startswith(query) or query.startswith(item) for item in line_stems) for query in query_stems):
                return line[:240]
    return None


def run_term(text: str, lines: list[str], term: str) -> dict[str, dict[str, Any]]:
    normalized = normalize_space(text)
    folded = normalized.casefold()
    document_tokens = set(tokens(normalized))
    document_stems = {stem(token) for token in document_tokens}
    query_tokens = tokens(term)
    query_stems = [stem(token) for token in query_tokens]
    results = {
        "matches": bool(query_tokens) and all(token in document_tokens for token in query_tokens),
        "contains": bool(term.strip()) and normalize_space(term).casefold() in folded,
        "equals": bool(term.strip()) and normalize_space(term) in normalized,
        "similar": bool(query_stems) and all(any(item.startswith(query) or query.startswith(item) for item in document_stems) for query in query_stems),
    }
    return {
        mode: {"matched": matched, "snippet": first_snippet(lines, normalize_space(term), mode) if matched else None}
        for mode, matched in results.items()
    }


def criteria_from_intake(data: dict[str, Any]) -> list[dict[str, Any]]:
    if data.get("schema_version") == "1.1" and data.get("job", {}).get("criteria"):
        return [
            {
                "id": item["id"],
                "kind": item["kind"],
                "criterion": item["text"],
                "search_terms": item["search_terms"],
            }
            for item in data["job"]["criteria"]
        ]

    job = data.get("job", {})
    criteria: list[dict[str, Any]] = []
    for index, item in enumerate(job.get("technologies", []), start=1):
        text = item.get("text", "").strip()
        if text:
            criteria.append({"id": f"legacy-technology-{index}", "kind": "must-have", "criterion": text, "search_terms": [text]})
    if criteria:
        return criteria
    index = 0
    for kind, field in (("must-have", "must_have"), ("preferred", "preferred")):
        for item in job.get("requirements", {}).get(field, []):
            index += 1
            text = item.get("text", "").strip()
            if text:
                criteria.append({"id": f"legacy-{kind}-{index}", "kind": kind, "criterion": text, "search_terms": [text]})
    return criteria


def criteria_from_markdown(markdown: str) -> list[dict[str, Any]]:
    criteria: list[dict[str, Any]] = []
    pattern = re.compile(
        r"(?ms)^###\s+(?P<id>[^\n]+)\n\s*\n- Kind:\s*(?P<kind>[^\n]+)\n"
        r"- Criterion:\s*(?P<criterion>[^\n]+)\n- Search terms:\s*(?P<terms>[^\n]+)"
    )
    for match in pattern.finditer(markdown):
        terms = [term.strip() for term in match.group("terms").split("|") if term.strip() and term.strip() != "none"]
        criteria.append(
            {
                "id": match.group("id").strip(),
                "kind": match.group("kind").strip(),
                "criterion": match.group("criterion").strip(),
                "search_terms": terms,
            }
        )
    if criteria:
        return criteria
    heading = re.search(r"(?ms)^## Technologies and methods\s*$\n(?P<body>.*?)(?=^## |\Z)", markdown)
    if heading:
        for index, line in enumerate(re.findall(r"(?m)^-\s+(.+)$", heading.group("body")), start=1):
            term = line.split(" (source:", 1)[0].strip()
            if term and term != "None observed.":
                criteria.append({"id": f"legacy-technology-{index}", "kind": "must-have", "criterion": term, "search_terms": [term]})
    return criteria


def analyze(resume: Path, criteria: list[dict[str, Any]], source: str) -> dict[str, Any]:
    text, lines = extracted_text(resume)
    rows: list[dict[str, Any]] = []
    for criterion in criteria:
        term_results = [
            {"term": term, "modes": run_term(text, lines, term)}
            for term in criterion["search_terms"]
        ]
        aggregate = {
            mode: any(result["modes"][mode]["matched"] for result in term_results)
            for mode in MODE_DESCRIPTIONS
        }
        rows.append({**criterion, "term_results": term_results, "aggregate_any_term": aggregate})
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "local-observable-text-search-proxy",
        "source": source,
        "resume": str(resume.resolve()),
        "official_ashby_result": False,
        "disclaimer": "Deterministic local approximations of documented search modes; no employer ATS or Ashby system was queried.",
        "mode_definitions": MODE_DESCRIPTIONS,
        "criteria": rows,
        "summary": {
            "criteria": len(rows),
            "matches": sum(1 for row in rows if row["aggregate_any_term"]["matches"]),
            "contains": sum(1 for row in rows if row["aggregate_any_term"]["contains"]),
            "equals": sum(1 for row in rows if row["aggregate_any_term"]["equals"]),
            "similar": sum(1 for row in rows if row["aggregate_any_term"]["similar"]),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", required=True, type=Path)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--job-intake", type=Path)
    source.add_argument("--job-description", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.job_intake:
        data = json.loads(args.job_intake.read_text(encoding="utf-8-sig"))
        criteria = criteria_from_intake(data)
        source = str(args.job_intake.resolve())
    else:
        markdown = args.job_description.read_text(encoding="utf-8-sig")
        criteria = criteria_from_markdown(markdown)
        source = str(args.job_description.resolve())
    result = analyze(args.resume, criteria, source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
