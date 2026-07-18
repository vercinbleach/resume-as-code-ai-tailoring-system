#!/usr/bin/env python3
"""Render a validated job intake as the only job evidence for clean matching."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

from validate_job_intake import validate


def clean(value: Any) -> str:
    if value is None:
        return "Not observed"
    return re.sub(r"\s+", " ", str(value)).strip()


def source_suffix(item: dict[str, Any]) -> str:
    source = item["source"]
    return f"source: {clean(source['location'])}; {source['url']}"


def render_items(lines: list[str], heading: str, items: list[dict[str, Any]], classified: bool = False) -> None:
    lines.extend([f"## {heading}", ""])
    if not items:
        lines.extend(["- None observed.", ""])
        return
    for item in items:
        basis = f"; classification: {item['classification_basis']}" if classified else ""
        lines.append(f"- {clean(item['text'])} ({source_suffix(item)}{basis})")
    lines.append("")


def render_criteria(lines: list[str], criteria: list[dict[str, Any]]) -> None:
    lines.extend([
        "## Atomic evaluation criteria",
        "",
        "> Each row is one independently testable criterion. Quality flags describe the criterion, not the candidate.",
        "",
    ])
    if not criteria:
        lines.extend(["- None compiled in this legacy snapshot.", ""])
        return
    for item in criteria:
        quality = item["quality"]
        flags = ", ".join(
            f"{name}={'yes' if quality[name] else 'no'}"
            for name in ("standalone", "singular", "clear", "specific", "objectively_verifiable")
        )
        notes = "; ".join(clean(note) for note in quality["notes"]) or "none"
        terms = " | ".join(clean(term) for term in item["search_terms"]) or "none"
        lines.extend([
            f"### {clean(item['id'])}",
            "",
            f"- Kind: {item['kind']}",
            f"- Criterion: {clean(item['text'])}",
            f"- Search terms: {terms}",
            f"- Quality: {flags}; bias_risk={quality['bias_risk']}; notes={notes}",
            f"- Evidence: {source_suffix(item)}",
            "",
        ])


def render(data: dict[str, Any]) -> str:
    version = data["schema_version"]
    capture = data["capture"]
    job = data["job"]
    application = data["application"]
    provenance = data["provenance"]

    lines = [
        "# Normalized job and application snapshot",
        "",
        "> Captured by Codex from visible pages only. No application was submitted, no candidate data was entered, and hidden employer rules were not accessible.",
        "",
        "## Capture metadata",
        "",
        f"- Intake schema: {version}",
        f"- Supplied URL: {capture['source_url']}",
        f"- Canonical URL: {capture['canonical_url']}",
        f"- Captured at: {capture['captured_at']}",
        f"- Capture status: {capture['status']}",
        "- Submission attempted: no",
        "",
        "## Position",
        "",
        f"- Company: {clean(job['company'])}",
        f"- Title: {clean(job['title'])}",
        f"- Job ID: {clean(job['job_id'])}",
        f"- Locations: {', '.join(clean(item) for item in job['locations']) or 'Not observed'}",
        f"- Workplace type: {job['workplace_type']}",
        f"- Employment type: {clean(job['employment_type'])}",
        "",
    ]

    render_items(lines, "Compensation", job["compensation"])
    render_items(lines, "Description", job["description"])
    render_items(lines, "Responsibilities", job["responsibilities"])
    render_items(lines, "Must-have requirements", job["requirements"]["must_have"], classified=True)
    render_items(lines, "Preferred qualifications", job["requirements"]["preferred"], classified=True)
    render_items(lines, "Unclear requirements", job["requirements"]["unclear"], classified=True)
    render_items(lines, "Technologies and methods", job["technologies"])
    render_items(lines, "Language requirements", job["languages"])
    render_items(lines, "Education requirements", job["education"])
    render_items(lines, "Experience thresholds", job["experience"])
    render_criteria(lines, job.get("criteria", []))

    lines.extend([
        "## Observed application flow",
        "",
        f"- Application status: {application['status']}",
        f"- Apply URL: {clean(application['apply_url'])}",
        f"- Host: {clean(application['host'])}",
        f"- Resume autofill observed: {application.get('autofill_from_resume_observed', 'unknown')}",
        "- Submission attempted: no",
        "",
        "### Visible steps",
        "",
    ])
    lines.extend([f"- {clean(step)}" for step in application["steps_visible"]] or ["- None observed."])
    lines.extend(["", "### Form fields and questions", ""])
    if application["fields"]:
        for field in application["fields"]:
            options = f"; options: {', '.join(clean(item) for item in field['options'])}" if field["options"] else ""
            if version == "1.1":
                gate = (
                    f"; required_question={field['required_question']}"
                    f"; screening={field['screening_classification']}"
                    f"; explicit_eligibility_gate={field['explicit_eligibility_gate']}"
                    f"; gate_basis={field['gate_basis']}"
                    "; potential_auto_reject=unknown"
                )
                validation = (
                    f"; visible_validation: {', '.join(clean(rule) for rule in field['validation_rules'])}"
                    if field["validation_rules"] else ""
                )
            else:
                gate = "; required_question mirrors required state; explicit_eligibility_gate=unknown; potential_auto_reject=unknown"
                validation = ""
            lines.append(
                f"- [{field['required']}] {clean(field['label'])} - section: {clean(field['section'])}; "
                f"type: {clean(field['type'])}{options}{gate}{validation} ({source_suffix(field)})"
            )
    else:
        lines.append("- None observed.")

    lines.extend(["", "### Requested documents", ""])
    if application["documents"]:
        for document in application["documents"]:
            formats = ", ".join(clean(item) for item in document["formats"]) or "not stated"
            lines.append(f"- [{document['required']}] {clean(document['name'])}; formats: {formats} ({source_suffix(document)})")
    else:
        lines.append("- None observed.")

    lines.extend(["", "### Notices", ""])
    if application["notices"]:
        for notice in application["notices"]:
            if version == "1.1":
                details = f"; opt_out_available={clean(notice['opt_out_available'])}; action_url={clean(notice['action_url'])}"
            else:
                details = ""
            lines.append(f"- [{notice['type']}] {clean(notice['text'])}{details} ({source_suffix(notice)})")
    else:
        lines.append("- None observed.")

    lines.extend(["", "## Capture blockers and limitations", ""])
    blockers = [*capture["blockers"], *application["blockers"]]
    lines.extend([f"- {clean(item)}" for item in blockers] or ["- No blocker recorded."])
    for note in provenance["notes"]:
        lines.append(f"- Note: {clean(note)}")
    lines.extend([
        "- A required question means only that the form requires an answer; it is not automatically a hard gate.",
        "- Only a visibly stated eligibility condition is labeled as an explicit eligibility gate.",
        "- Hidden ranking, AI criteria, auto-reject rules, fraud signals, and employer-only ATS settings remain unknown.",
        "",
        "## Pages inspected",
        "",
    ])
    for page in capture["pages_visited"]:
        lines.append(f"- [{page['purpose']}; {page['status']}] {page['url']}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(data), encoding="utf-8")
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
