#!/usr/bin/env python3
"""Project a resume PDF into a local ATS-like structured profile."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from pypdf import PdfReader


SECTION_NAMES = ("Education", "Experience", "Projects", "Technical Skills")
DATE_RE = re.compile(
    r"(?i)(expected graduation\s*:\s*\d{4}|graduated\s*:\s*\d{4}|"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{4}\s*-\s*"
    r"(?:present|(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{4}))"
)


def clean_line(value: str) -> str:
    value = value.replace("\uf3c5", "").replace("\uf0e0", "").replace("\uf095", "").replace("\uf08c", "").replace("\uf09b", "")
    return re.sub(r"\s+", " ", value).strip()


def extract_lines(reader: PdfReader) -> list[str]:
    lines: list[str] = []
    for page in reader.pages:
        lines.extend(clean_line(line) for line in (page.extract_text() or "").splitlines())
    return [line for line in lines if line]


def section_slice(lines: list[str], start: str, end: str | None) -> list[str]:
    try:
        begin = lines.index(start) + 1
    except ValueError:
        return []
    if end is None:
        return lines[begin:]
    try:
        finish = lines.index(end, begin)
    except ValueError:
        finish = len(lines)
    return lines[begin:finish]


def extract_links(reader: PdfReader) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        for annotation_ref in page.get("/Annots") or []:
            try:
                annotation = annotation_ref.get_object()
                action = annotation.get("/A")
                uri = str(action.get("/URI")) if action and action.get("/URI") else None
            except (AttributeError, TypeError):
                uri = None
            if not uri:
                continue
            lowered = uri.casefold()
            link_type = "linkedin" if "linkedin.com" in lowered else "github" if "github.com" in lowered else "email" if lowered.startswith("mailto:") else "phone" if lowered.startswith("tel:") else "other"
            links.append({"type": link_type, "uri": uri, "page": page_number})
    return links


def project_contact(lines: list[str], links: list[dict[str, Any]]) -> dict[str, Any]:
    header = lines[: lines.index("Education")] if "Education" in lines else lines[:3]
    text = " | ".join(header)
    email_match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, flags=re.I)
    phone_match = re.search(r"\+\d[\d\s().-]{7,}\d", text)
    location = None
    if len(header) > 1:
        first_part = header[1].split("|")[0].strip()
        if re.search(r"[A-Za-zÀ-ÿ].*,\s*[A-Z]{2}\b", first_part):
            location = first_part
    return {
        "name": header[0] if header else None,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "location": location,
        "links": links,
    }


def project_experience(lines: list[str]) -> list[dict[str, Any]]:
    dates = [index for index, line in enumerate(lines) if DATE_RE.fullmatch(line)]
    entries: list[dict[str, Any]] = []
    for position, date_index in enumerate(dates):
        headers = lines[max(0, date_index - 3):date_index]
        if len(headers) < 3:
            continue
        next_date = dates[position + 1] if position + 1 < len(dates) else len(lines) + 3
        bullet_lines = lines[date_index + 1:max(date_index + 1, next_date - 3)]
        bullets: list[str] = []
        for line in bullet_lines:
            if line.startswith(("◦", "•", "-")):
                bullets.append(line.lstrip("◦•- "))
            elif bullets:
                bullets[-1] = f"{bullets[-1]} {line}"
        entries.append(
            {
                "company": headers[0],
                "title": headers[1],
                "location": headers[2],
                "dates": lines[date_index],
                "highlights": bullets,
            }
        )
    return entries


def project_education(lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    buffer: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        match = DATE_RE.search(line)
        if not match:
            buffer.append(line)
            index += 1
            continue
        prefix = line[: match.start()].strip()
        date_text = match.group(0)
        if prefix:
            degree = lines[index + 1] if index + 1 < len(lines) and not DATE_RE.search(lines[index + 1]) else None
            entries.append({"institution": prefix, "credential": degree, "location": None, "dates": date_text})
            buffer = []
            index += 2 if degree else 1
            continue
        if buffer:
            entries.append(
                {
                    "institution": buffer[0],
                    "credential": buffer[1] if len(buffer) > 1 else None,
                    "location": " ".join(buffer[2:]) or None,
                    "dates": date_text,
                }
            )
        buffer = []
        index += 1
    return entries


def project_skills(lines: list[str]) -> dict[str, list[str]]:
    skills: dict[str, list[str]] = {}
    for line in lines:
        if ":" not in line:
            continue
        category, values = line.split(":", 1)
        items = [item.strip() for item in values.split(",") if item.strip()]
        if category.strip() and items:
            skills[category.strip()] = items
    return skills


def analyze(resume: Path) -> dict[str, Any]:
    reader = PdfReader(str(resume))
    lines = extract_lines(reader)
    links = extract_links(reader)
    contact = project_contact(lines, links)
    experience = project_experience(section_slice(lines, "Experience", "Projects"))
    education = project_education(section_slice(lines, "Education", "Experience"))
    skills = project_skills(section_slice(lines, "Technical Skills", None))

    issues: list[str] = []
    for field in ("name", "email", "phone", "location"):
        if not contact[field]:
            issues.append(f"Contact field not projected: {field}")
    if not experience:
        issues.append("No experience entries were projected.")
    if not education:
        issues.append("No education entries were projected.")
    if not skills:
        issues.append("No skill groups were projected.")
    missing_sections = [section for section in SECTION_NAMES if section not in lines]
    issues.extend(f"Expected section not found: {section}" for section in missing_sections)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(resume.resolve()),
        "artifact_type": "local-parsed-profile-projection",
        "official_ashby_parser_result": False,
        "disclaimer": "Deterministic local projection from pypdf text; it does not reproduce or claim Ashby's private parser output.",
        "contact": contact,
        "experience": experience,
        "education": education,
        "skills": skills,
        "issues": issues,
        "summary": {
            "contact_fields_projected": sum(1 for field in ("name", "email", "phone", "location") if contact[field]),
            "experience_entries": len(experience),
            "education_entries": len(education),
            "skill_groups": len(skills),
            "issues": len(issues),
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
    result = analyze(args.resume)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
