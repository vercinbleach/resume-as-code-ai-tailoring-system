#!/usr/bin/env python3
"""Build an application-readiness checklist without inventing candidate answers."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def profile_source(label: str, profile: dict[str, Any]) -> str | None:
    folded = re.sub(r"[^a-z0-9]+", " ", label.casefold()).strip()
    contact = profile.get("contact", {})
    mappings = (
        (("full name", "name", "first name", "last name"), "name"),
        (("email", "e mail"), "email"),
        (("phone", "mobile", "telephone"), "phone"),
        (("linkedin",), "linkedin"),
        (("github",), "github"),
    )
    for needles, field in mappings:
        if not any(needle in folded for needle in needles):
            continue
        if field in {"linkedin", "github"}:
            if any(link.get("type") == field for link in contact.get("links", [])):
                return f"parsed-profile.json contact.links[{field}]"
        elif contact.get(field):
            return f"parsed-profile.json contact.{field}"
    return None


def classify_legacy_field(field: dict[str, Any]) -> tuple[str, str, str]:
    label = field.get("label", "").casefold()
    if any(term in label for term in ("authorize", "sponsor", "visa", "work permit", "office", "relocat")):
        screening = "eligibility"
    elif any(term in label for term in ("gender", "race", "ethnic", "veteran", "disability")):
        screening = "demographic"
    elif any(term in label for term in ("consent", "privacy", "recording")):
        screening = "consent"
    elif any(term in label for term in ("name", "email", "phone", "address", "linkedin", "github", "resume")):
        screening = "administrative"
    elif field.get("type") in {"textarea", "text-area"}:
        screening = "open-ended"
    else:
        screening = "unknown"
    return screening, "unknown", "unknown"


def analyze(intake: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    version = intake.get("schema_version")
    application = intake["application"]
    rows: list[dict[str, Any]] = []
    for index, field in enumerate(application.get("fields", []), start=1):
        if version == "1.1":
            required = field["required_question"]
            screening = field["screening_classification"]
            explicit_gate = field["explicit_eligibility_gate"]
            gate_basis = field["gate_basis"]
        else:
            required = field.get("required", "unknown")
            screening, explicit_gate, gate_basis = classify_legacy_field(field)

        known_source = profile_source(field.get("label", ""), profile)
        answer_known = known_source is not None
        needs_user = not answer_known and required != "no"
        if answer_known:
            answer_status = "known-from-resume-projection"
        elif required == "yes":
            answer_status = "needs-candidate"
        elif required == "unknown":
            answer_status = "verify-required-state"
        else:
            answer_status = "optional-unanswered"

        if explicit_gate == "yes":
            risk = "Explicit eligibility condition requires a truthful candidate answer."
        elif required == "yes":
            risk = "Required for form completion; no rejection behavior is inferred."
        elif required == "unknown":
            risk = "Required state is unknown and must be verified."
        else:
            risk = "No blocking completion risk observed."

        rows.append(
            {
                "id": f"field-{index}",
                "label": field.get("label"),
                "section": field.get("section"),
                "required_question": required,
                "screening_classification": screening,
                "explicit_eligibility_gate": explicit_gate,
                "gate_basis": gate_basis,
                "potential_auto_reject": "unknown",
                "answer_status": answer_status,
                "answer_known": answer_known,
                "needs_user": needs_user,
                "answer_source": known_source,
                "risk": risk,
                "field_source": field.get("source"),
            }
        )

    documents = [
        {
            "name": item.get("name"),
            "required": item.get("required"),
            "available": "resume" in item.get("name", "").casefold(),
            "source": "inputs/resume.pdf" if "resume" in item.get("name", "").casefold() else None,
            "formats": item.get("formats", []),
        }
        for item in application.get("documents", [])
    ]
    notices = [
        {
            "type": item.get("type"),
            "text": item.get("text"),
            "action_url": item.get("action_url") if version == "1.1" else None,
            "opt_out_available": item.get("opt_out_available") if version == "1.1" else None,
            "source": item.get("source"),
        }
        for item in application.get("notices", [])
    ]
    required_rows = [row for row in rows if row["required_question"] == "yes"]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "application-readiness-checklist",
        "intake_schema_version": version,
        "submission_attempted": False,
        "ready_to_submit": False,
        "answers_invented": False,
        "fields": rows,
        "documents": documents,
        "notices": notices,
        "summary": {
            "fields": len(rows),
            "required_questions": len(required_rows),
            "required_answers_known_from_resume": sum(1 for row in required_rows if row["answer_known"]),
            "required_answers_needing_user": sum(1 for row in required_rows if row["needs_user"]),
            "explicit_eligibility_gates": sum(1 for row in rows if row["explicit_eligibility_gate"] == "yes"),
            "hidden_auto_reject_rules": "unknown",
        },
        "out_of_scope": [
            "Hidden auto-reject configuration",
            "Employer ranking weights or private AI criteria",
            "Fraud detection signals such as device, IP, email, or phone telemetry",
            "Submitting or pre-filling the application",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-intake", required=True, type=Path)
    parser.add_argument("--parsed-profile", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = analyze(load_json(args.job_intake), load_json(args.parsed_profile))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
