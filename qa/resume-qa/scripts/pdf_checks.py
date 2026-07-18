#!/usr/bin/env python3
"""Run deterministic checks against a resume PDF without storing its full text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pypdf
from pypdf import PdfReader


EXPECTED_SECTIONS = ("education", "experience", "projects", "technical skills")
MAX_FILE_BYTES = 2 * 1024 * 1024
ASHBY_UPLOAD_MAX_BYTES = 50 * 1024 * 1024
ASHBY_FULLTEXT_MAX_BYTES = 16 * 1024 * 1024
MIN_WORD_COUNT = 150


def check_result(passed: bool, **details: Any) -> dict[str, Any]:
    return {"passed": passed, **details}


def classify_link(uri: str) -> str:
    lowered = uri.lower()
    if "linkedin.com" in lowered:
        return "linkedin"
    if "github.com" in lowered:
        return "github"
    if lowered.startswith("mailto:"):
        return "email"
    if lowered.startswith("tel:"):
        return "phone"
    return "other"


def extract_links(reader: PdfReader) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        annotations = page.get("/Annots") or []
        for annotation_ref in annotations:
            try:
                annotation = annotation_ref.get_object()
                action = annotation.get("/A")
                uri = action.get("/URI") if action else None
            except (AttributeError, TypeError):
                uri = None
            if uri:
                uri_text = str(uri)
                links.append(
                    {
                        "page": str(page_number),
                        "type": classify_link(uri_text),
                        "uri": uri_text,
                    }
                )
    return links


def page_dimensions(reader: PdfReader) -> list[dict[str, float | int]]:
    dimensions: list[dict[str, float | int]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        width_points = float(page.mediabox.width)
        height_points = float(page.mediabox.height)
        dimensions.append(
            {
                "page": page_number,
                "width_points": round(width_points, 2),
                "height_points": round(height_points, 2),
                "width_inches": round(width_points / 72, 2),
                "height_inches": round(height_points / 72, 2),
            }
        )
    return dimensions


def analyze(resume_path: Path) -> dict[str, Any]:
    file_bytes = resume_path.read_bytes()
    reader = PdfReader(str(resume_path))
    encrypted = bool(reader.is_encrypted)
    texts: list[str] = []
    extraction_error: str | None = None
    try:
        texts = [(page.extract_text() or "") for page in reader.pages]
    except Exception as exc:  # pypdf exposes several parser-specific exceptions.
        extraction_error = f"{type(exc).__name__}: {exc}"

    combined_text = "\n".join(texts)
    normalized_text = re.sub(r"\s+", " ", combined_text).strip().lower()
    word_count = len(re.findall(r"\b[\w+#.-]+\b", combined_text, flags=re.UNICODE))
    section_positions = {
        section: normalized_text.find(section) for section in EXPECTED_SECTIONS
    }
    found_sections = [name for name, position in section_positions.items() if position >= 0]
    missing_sections = [name for name, position in section_positions.items() if position < 0]
    present_positions = [section_positions[name] for name in EXPECTED_SECTIONS if section_positions[name] >= 0]
    sections_in_order = not missing_sections and present_positions == sorted(present_positions)

    links = extract_links(reader)
    detected_link_types = sorted({link["type"] for link in links})
    required_link_types = ["linkedin", "github"]
    missing_link_types = [item for item in required_link_types if item not in detected_link_types]

    metadata = {}
    if reader.metadata:
        metadata = {
            str(key).lstrip("/"): str(value)
            for key, value in reader.metadata.items()
            if value is not None
        }

    checks = {
        "one_page": check_result(
            len(reader.pages) == 1,
            expected=1,
            actual=len(reader.pages),
        ),
        "text_extractable": check_result(
            word_count >= MIN_WORD_COUNT and extraction_error is None,
            minimum_word_count=MIN_WORD_COUNT,
            actual_word_count=word_count,
            error=extraction_error,
        ),
        "expected_sections_present": check_result(
            not missing_sections,
            expected=list(EXPECTED_SECTIONS),
            found=found_sections,
            missing=missing_sections,
        ),
        "expected_section_order": check_result(
            sections_in_order,
            expected=list(EXPECTED_SECTIONS),
            positions=section_positions,
        ),
        "linkedin_and_github_clickable": check_result(
            not missing_link_types,
            required=required_link_types,
            detected=detected_link_types,
            missing=missing_link_types,
        ),
        "file_size_under_2mb": check_result(
            len(file_bytes) <= MAX_FILE_BYTES,
            maximum_bytes=MAX_FILE_BYTES,
            actual_bytes=len(file_bytes),
        ),
        "not_encrypted": check_result(
            not encrypted,
            encrypted=encrypted,
        ),
        "ashby_upload_under_50mb": check_result(
            len(file_bytes) <= ASHBY_UPLOAD_MAX_BYTES,
            maximum_bytes=ASHBY_UPLOAD_MAX_BYTES,
            actual_bytes=len(file_bytes),
            reference="https://docs.ashbyhq.com/application-forms",
        ),
        "ashby_fulltext_and_autofill_under_16mb": check_result(
            len(file_bytes) <= ASHBY_FULLTEXT_MAX_BYTES,
            maximum_bytes=ASHBY_FULLTEXT_MAX_BYTES,
            actual_bytes=len(file_bytes),
            reference="https://docs.ashbyhq.com/application-forms",
        ),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(resume_path.resolve()),
        "sha256": hashlib.sha256(file_bytes).hexdigest(),
        "parser": {"name": "pypdf", "version": pypdf.__version__},
        "document": {
            "pages": len(reader.pages),
            "encrypted": encrypted,
            "file_size_bytes": len(file_bytes),
            "page_dimensions": page_dimensions(reader),
            "metadata": metadata,
        },
        "metrics": {
            "extracted_word_count": word_count,
            "annotation_link_count": len(links),
        },
        "links": links,
        "checks": checks,
        "summary": {
            "passed": sum(1 for result in checks.values() if result["passed"]),
            "failed": sum(1 for result in checks.values() if not result["passed"]),
            "total": len(checks),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.resume.is_file():
        raise SystemExit(f"Resume PDF not found: {args.resume}")
    if args.resume.suffix.lower() != ".pdf":
        raise SystemExit(f"Expected a PDF file: {args.resume}")

    result = analyze(args.resume)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
