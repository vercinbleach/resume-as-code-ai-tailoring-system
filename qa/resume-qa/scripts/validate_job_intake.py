#!/usr/bin/env python3
"""Validate an observed job and application intake before clean evaluation."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SCHEMA_VERSIONS = {"1.0", "1.1"}
CAPTURE_STATUS = {"complete", "partial", "blocked"}
APPLICATION_STATUS = {"inspected", "not-found", "blocked", "auth-required"}
WORKPLACE_TYPES = {"remote", "hybrid", "on-site", "unknown"}
REQUIRED_STATE = {"yes", "no", "unknown"}
CLASSIFICATION = {"explicit", "heading", "wording", "form-required", "inferred"}
NOTICE_TYPES = {"privacy", "ai-review", "application-limit", "deadline", "equal-opportunity", "other"}
CRITERION_KINDS = {"eligibility", "must-have", "preferred", "responsibility", "unclear"}
SCREENING_CLASSES = {"eligibility", "administrative", "demographic", "consent", "open-ended", "unknown"}
GATE_BASES = {"explicit-eligibility", "question-only", "not-a-gate", "unknown"}
QUALITY_FLAGS = {"standalone", "singular", "clear", "specific", "objectively_verifiable"}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_url(value: Any) -> bool:
    if not nonempty(value):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def exact_keys(value: Any, path: str, required: set[str], errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return False
    missing = required - value.keys()
    extra = value.keys() - required
    for key in sorted(missing):
        errors.append(f"{path}.{key} is required")
    for key in sorted(extra):
        errors.append(f"{path}.{key} is not allowed")
    return not missing


def string_list(value: Any, path: str, errors: list[str], *, nonempty_list: bool = False) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return
    if nonempty_list and not value:
        errors.append(f"{path} must contain at least one item")
    for index, item in enumerate(value):
        if not nonempty(item):
            errors.append(f"{path}[{index}] must be a non-empty string")


def source(value: Any, path: str, errors: list[str]) -> None:
    if not exact_keys(value, path, {"url", "location"}, errors):
        return
    if not valid_url(value.get("url")):
        errors.append(f"{path}.url must be an absolute HTTP(S) URL")
    if not nonempty(value.get("location")):
        errors.append(f"{path}.location must be a non-empty string")


def evidence_items(value: Any, path: str, errors: list[str], classified: bool = False) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return
    expected = {"text", "source", "classification_basis"} if classified else {"text", "source"}
    for index, item in enumerate(value):
        current = f"{path}[{index}]"
        if not exact_keys(item, current, expected, errors):
            continue
        if not nonempty(item.get("text")):
            errors.append(f"{current}.text must be a non-empty string")
        source(item.get("source"), f"{current}.source", errors)
        if classified and item.get("classification_basis") not in CLASSIFICATION:
            errors.append(f"{current}.classification_basis is invalid")


def criteria_items(value: Any, path: str, errors: list[str], *, required: bool) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return
    if required and not value:
        errors.append(f"{path} must contain atomic criteria for a complete or partial capture")
    ids: set[str] = set()
    for index, item in enumerate(value):
        current = f"{path}[{index}]"
        keys = {"id", "text", "kind", "source", "quality", "search_terms"}
        if not exact_keys(item, current, keys, errors):
            continue
        criterion_id = item.get("id")
        if not nonempty(criterion_id) or not all(char.islower() or char.isdigit() or char in "._-" for char in criterion_id):
            errors.append(f"{current}.id must contain lowercase letters, numbers, dots, underscores, or hyphens")
        elif criterion_id[0] in "._-":
            errors.append(f"{current}.id must start with a letter or number")
        elif criterion_id in ids:
            errors.append(f"{current}.id must be unique")
        else:
            ids.add(criterion_id)
        if not nonempty(item.get("text")):
            errors.append(f"{current}.text must be a non-empty string")
        kind = item.get("kind")
        if kind not in CRITERION_KINDS:
            errors.append(f"{current}.kind is invalid")
        source(item.get("source"), f"{current}.source", errors)
        string_list(item.get("search_terms"), f"{current}.search_terms", errors, nonempty_list=kind != "unclear")
        if isinstance(item.get("search_terms"), list):
            folded = [term.casefold().strip() for term in item["search_terms"] if isinstance(term, str)]
            if len(folded) != len(set(folded)):
                errors.append(f"{current}.search_terms must be unique ignoring case")

        quality = item.get("quality")
        quality_keys = QUALITY_FLAGS | {"bias_risk", "notes"}
        if not exact_keys(quality, f"{current}.quality", quality_keys, errors):
            continue
        for flag in QUALITY_FLAGS:
            if not isinstance(quality.get(flag), bool):
                errors.append(f"{current}.quality.{flag} must be boolean")
        if quality.get("bias_risk") not in {"none", "possible", "high"}:
            errors.append(f"{current}.quality.bias_risk is invalid")
        string_list(quality.get("notes"), f"{current}.quality.notes", errors)
        quality_problem = any(quality.get(flag) is False for flag in QUALITY_FLAGS)
        if kind != "unclear" and quality_problem:
            errors.append(f"{current} must be kind unclear until all five quality checks pass")
        if kind != "unclear" and quality.get("bias_risk") == "high":
            errors.append(f"{current} cannot be scoreable while bias_risk is high")
        if (quality_problem or quality.get("bias_risk") != "none") and not quality.get("notes"):
            errors.append(f"{current}.quality.notes must explain quality or bias concerns")


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    top = {"schema_version", "capture", "job", "application", "provenance"}
    if not exact_keys(data, "intake", top, errors):
        return errors
    version = data.get("schema_version")
    if version not in SCHEMA_VERSIONS:
        errors.append("intake.schema_version must be 1.0 or 1.1")
    v11 = version == "1.1"

    capture = data.get("capture")
    capture_keys = {"source_url", "canonical_url", "captured_at", "status", "pages_visited", "blockers", "submission_attempted"}
    if exact_keys(capture, "intake.capture", capture_keys, errors):
        if not valid_url(capture.get("source_url")):
            errors.append("intake.capture.source_url must be an absolute HTTP(S) URL")
        if not valid_url(capture.get("canonical_url")):
            errors.append("intake.capture.canonical_url must be an absolute HTTP(S) URL")
        captured_at = capture.get("captured_at")
        if not nonempty(captured_at):
            errors.append("intake.capture.captured_at must be an ISO date-time string")
        else:
            try:
                datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
            except ValueError:
                errors.append("intake.capture.captured_at must be an ISO date-time string")
        if capture.get("status") not in CAPTURE_STATUS:
            errors.append("intake.capture.status must be complete, partial, or blocked")
        pages = capture.get("pages_visited")
        if not isinstance(pages, list) or not pages:
            errors.append("intake.capture.pages_visited must contain at least one page")
        else:
            for index, page in enumerate(pages):
                current = f"intake.capture.pages_visited[{index}]"
                if not exact_keys(page, current, {"url", "purpose", "status"}, errors):
                    continue
                if not valid_url(page.get("url")):
                    errors.append(f"{current}.url must be an absolute HTTP(S) URL")
                if page.get("purpose") not in {"job", "application", "other"}:
                    errors.append(f"{current}.purpose is invalid")
                if page.get("status") not in {"inspected", "partial", "blocked"}:
                    errors.append(f"{current}.status is invalid")
        string_list(capture.get("blockers"), "intake.capture.blockers", errors)
        if capture.get("submission_attempted") is not False:
            errors.append("intake.capture.submission_attempted must be false")

    job = data.get("job")
    job_keys = {"company", "title", "job_id", "locations", "workplace_type", "employment_type", "compensation", "description", "responsibilities", "requirements", "technologies", "languages", "education", "experience"}
    if v11:
        job_keys.add("criteria")
    if exact_keys(job, "intake.job", job_keys, errors):
        capture_status = capture.get("status") if isinstance(capture, dict) else None
        if capture_status in {"complete", "partial"}:
            for field in ("company", "title"):
                if not nonempty(job.get(field)):
                    errors.append(f"intake.job.{field} must be present for a {capture_status} capture")
        else:
            for field in ("company", "title"):
                if job.get(field) is not None and not nonempty(job.get(field)):
                    errors.append(f"intake.job.{field} must be null or non-empty")
        for field in ("job_id", "employment_type"):
            if job.get(field) is not None and not nonempty(job.get(field)):
                errors.append(f"intake.job.{field} must be null or non-empty")
        string_list(job.get("locations"), "intake.job.locations", errors)
        if job.get("workplace_type") not in WORKPLACE_TYPES:
            errors.append("intake.job.workplace_type is invalid")
        for field in ("compensation", "description", "responsibilities", "technologies", "languages", "education", "experience"):
            evidence_items(job.get(field), f"intake.job.{field}", errors)
        requirements = job.get("requirements")
        if exact_keys(requirements, "intake.job.requirements", {"must_have", "preferred", "unclear"}, errors):
            for field in ("must_have", "preferred", "unclear"):
                evidence_items(requirements.get(field), f"intake.job.requirements.{field}", errors, classified=True)
        if v11:
            criteria_items(job.get("criteria"), "intake.job.criteria", errors, required=capture_status in {"complete", "partial"})
        if capture_status in {"complete", "partial"}:
            content_groups = [job.get("description"), job.get("responsibilities")]
            if isinstance(requirements, dict):
                content_groups.extend(requirements.get(name) for name in ("must_have", "preferred", "unclear"))
            if not any(isinstance(group, list) and group for group in content_groups):
                errors.append("intake.job must contain observed description, responsibility, or requirement content")

    application = data.get("application")
    application_keys = {"apply_url", "host", "status", "steps_visible", "fields", "documents", "notices", "blockers", "submission_attempted"}
    if v11:
        application_keys.add("autofill_from_resume_observed")
    if exact_keys(application, "intake.application", application_keys, errors):
        if application.get("apply_url") is not None and not valid_url(application.get("apply_url")):
            errors.append("intake.application.apply_url must be null or an absolute HTTP(S) URL")
        if application.get("host") is not None and not nonempty(application.get("host")):
            errors.append("intake.application.host must be null or non-empty")
        if application.get("status") not in APPLICATION_STATUS:
            errors.append("intake.application.status is invalid")
        if application.get("status") == "inspected" and not valid_url(application.get("apply_url")):
            errors.append("intake.application.apply_url is required when status is inspected")
        if v11 and application.get("autofill_from_resume_observed") not in REQUIRED_STATE:
            errors.append("intake.application.autofill_from_resume_observed is invalid")
        string_list(application.get("steps_visible"), "intake.application.steps_visible", errors)
        string_list(application.get("blockers"), "intake.application.blockers", errors)
        fields = application.get("fields")
        if not isinstance(fields, list):
            errors.append("intake.application.fields must be a list")
        else:
            for index, field in enumerate(fields):
                current = f"intake.application.fields[{index}]"
                keys = {"label", "section", "type", "required", "options", "source"}
                if v11:
                    keys |= {"required_question", "screening_classification", "explicit_eligibility_gate", "gate_basis", "potential_auto_reject", "validation_rules"}
                if not exact_keys(field, current, keys, errors):
                    continue
                for key in ("label", "section", "type"):
                    if not nonempty(field.get(key)):
                        errors.append(f"{current}.{key} must be a non-empty string")
                if field.get("required") not in REQUIRED_STATE:
                    errors.append(f"{current}.required is invalid")
                string_list(field.get("options"), f"{current}.options", errors)
                source(field.get("source"), f"{current}.source", errors)
                if v11:
                    if field.get("required_question") not in REQUIRED_STATE:
                        errors.append(f"{current}.required_question is invalid")
                    elif field.get("required_question") != field.get("required"):
                        errors.append(f"{current}.required_question must match the observed required state")
                    if field.get("screening_classification") not in SCREENING_CLASSES:
                        errors.append(f"{current}.screening_classification is invalid")
                    if field.get("explicit_eligibility_gate") not in REQUIRED_STATE:
                        errors.append(f"{current}.explicit_eligibility_gate is invalid")
                    if field.get("gate_basis") not in GATE_BASES:
                        errors.append(f"{current}.gate_basis is invalid")
                    if field.get("potential_auto_reject") != "unknown":
                        errors.append(f"{current}.potential_auto_reject must remain unknown")
                    string_list(field.get("validation_rules"), f"{current}.validation_rules", errors)
                    if field.get("gate_basis") == "explicit-eligibility" and field.get("explicit_eligibility_gate") != "yes":
                        errors.append(f"{current}.explicit_eligibility_gate must be yes for an explicit-eligibility basis")
                    if field.get("explicit_eligibility_gate") == "yes" and field.get("gate_basis") != "explicit-eligibility":
                        errors.append(f"{current}.gate_basis must be explicit-eligibility when a gate was observed")
                    if field.get("gate_basis") == "question-only" and field.get("explicit_eligibility_gate") == "yes":
                        errors.append(f"{current}.question-only cannot be an explicit eligibility gate")
        documents = application.get("documents")
        if not isinstance(documents, list):
            errors.append("intake.application.documents must be a list")
        else:
            for index, document in enumerate(documents):
                current = f"intake.application.documents[{index}]"
                if not exact_keys(document, current, {"name", "required", "formats", "source"}, errors):
                    continue
                if not nonempty(document.get("name")):
                    errors.append(f"{current}.name must be a non-empty string")
                if document.get("required") not in REQUIRED_STATE:
                    errors.append(f"{current}.required is invalid")
                string_list(document.get("formats"), f"{current}.formats", errors)
                source(document.get("source"), f"{current}.source", errors)
        notices = application.get("notices")
        if not isinstance(notices, list):
            errors.append("intake.application.notices must be a list")
        else:
            for index, notice in enumerate(notices):
                current = f"intake.application.notices[{index}]"
                keys = {"type", "text", "source"}
                if v11:
                    keys |= {"action_url", "opt_out_available"}
                if not exact_keys(notice, current, keys, errors):
                    continue
                if notice.get("type") not in NOTICE_TYPES:
                    errors.append(f"{current}.type is invalid")
                if not nonempty(notice.get("text")):
                    errors.append(f"{current}.text must be a non-empty string")
                source(notice.get("source"), f"{current}.source", errors)
                if v11:
                    if notice.get("action_url") is not None and not valid_url(notice.get("action_url")):
                        errors.append(f"{current}.action_url must be null or an absolute HTTP(S) URL")
                    if notice.get("opt_out_available") is not None and not isinstance(notice.get("opt_out_available"), bool):
                        errors.append(f"{current}.opt_out_available must be boolean or null")
        if application.get("submission_attempted") is not False:
            errors.append("intake.application.submission_attempted must be false")

    provenance = data.get("provenance")
    if exact_keys(provenance, "intake.provenance", {"observed_only", "hidden_rules_claimed", "notes"}, errors):
        if provenance.get("observed_only") is not True:
            errors.append("intake.provenance.observed_only must be true")
        if provenance.get("hidden_rules_claimed") is not False:
            errors.append("intake.provenance.hidden_rules_claimed must be false")
        string_list(provenance.get("notes"), "intake.provenance.notes", errors)

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("intake", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.intake.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Valid job intake: {args.intake.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
