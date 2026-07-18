#!/usr/bin/env python3
"""Validate a combined clean PDF-only Resume QA report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_evaluator import validate as validate_evaluator


VALID_MODES = {"pdf", "technical", "leadership", "job-match", "callback"}
SEMANTIC_MODES = VALID_MODES - {"pdf"}
REQUIRED = {
    "session_id",
    "generated_at",
    "architecture",
    "resume",
    "job_description",
    "modes",
    "pdf_checks",
    "evaluators",
    "recommended_changes",
    "limitations",
    "sources",
}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Report root must be an object"]

    for field in sorted(REQUIRED - data.keys()):
        errors.append(f"Missing required field: {field}")
    if not nonempty(data.get("session_id")):
        errors.append("session_id must be a non-empty string")
    if not nonempty(data.get("generated_at")):
        errors.append("generated_at must be a non-empty ISO date-time string")
    architecture = data.get("architecture")
    if architecture not in {"clean-pdf-fanout-v3", "clean-pdf-codex-tasks-v4", "clean-pdf-codex-tasks-v5", "clean-pdf-codex-tasks-v6", "clean-pdf-codex-sandboxes-v7"}:
        errors.append("architecture must be a supported clean Resume QA architecture")
    if data.get("resume") != "inputs/resume.pdf":
        errors.append("resume must be inputs/resume.pdf")
    if data.get("job_description") not in {None, "inputs/job-description.md"}:
        errors.append("job_description must be null or inputs/job-description.md")
    if data.get("job_intake") not in {None, "inputs/job-intake.json"}:
        errors.append("job_intake must be null or inputs/job-intake.json")
    if data.get("job_intake") and data.get("job_description") is None:
        errors.append("job_intake requires inputs/job-description.md")

    modes_value = data.get("modes")
    modes: set[str] = set()
    if not isinstance(modes_value, list) or not modes_value:
        errors.append("modes must be a non-empty list")
    else:
        modes = set(modes_value)
        if len(modes) != len(modes_value):
            errors.append("modes must not contain duplicates")
        invalid = modes - VALID_MODES
        if invalid:
            errors.append(f"Invalid modes: {', '.join(sorted(invalid))}")
    if "job-match" in modes and data.get("job_description") is None:
        errors.append("job-match mode requires inputs/job-description.md")
    if "callback" in modes and data.get("job_description") is None:
        errors.append("callback mode requires inputs/job-description.md")

    if not isinstance(data.get("pdf_checks"), dict):
        errors.append("pdf_checks must be an object")

    coordinator = data.get("coordinator_artifacts")
    if architecture in {"clean-pdf-codex-tasks-v5", "clean-pdf-codex-tasks-v6", "clean-pdf-codex-sandboxes-v7"} and not isinstance(coordinator, dict):
        errors.append("coordinator_artifacts is required for architecture v5, v6, or v7")
    if isinstance(coordinator, dict):
        expected_artifacts = {"parsed_profile", "ashby_text_search", "application_readiness"}
        extra = coordinator.keys() - expected_artifacts
        if extra:
            errors.append(f"Unknown coordinator artifacts: {', '.join(sorted(extra))}")
        profile = coordinator.get("parsed_profile")
        if architecture in {"clean-pdf-codex-tasks-v5", "clean-pdf-codex-tasks-v6", "clean-pdf-codex-sandboxes-v7"} and not isinstance(profile, dict):
            errors.append("coordinator_artifacts.parsed_profile is required for architecture v5, v6, or v7")
        if isinstance(profile, dict):
            if profile.get("official_ashby_parser_result") is not False:
                errors.append("parsed profile must not claim an official Ashby parser result")
            if not isinstance(profile.get("summary"), dict):
                errors.append("parsed profile summary must be an object")
        search = coordinator.get("ashby_text_search")
        if data.get("job_description") and architecture in {"clean-pdf-codex-tasks-v5", "clean-pdf-codex-tasks-v6", "clean-pdf-codex-sandboxes-v7"} and not isinstance(search, dict):
            errors.append("coordinator_artifacts.ashby_text_search is required when a job is present")
        if isinstance(search, dict):
            if search.get("official_ashby_result") is not False:
                errors.append("text search must not claim an official Ashby result")
            if not isinstance(search.get("criteria"), list) or not isinstance(search.get("summary"), dict):
                errors.append("text search must contain criteria and summary")
        readiness = coordinator.get("application_readiness")
        if data.get("job_intake") and architecture in {"clean-pdf-codex-tasks-v5", "clean-pdf-codex-tasks-v6", "clean-pdf-codex-sandboxes-v7"} and not isinstance(readiness, dict):
            errors.append("coordinator_artifacts.application_readiness is required when raw intake is present")
        if isinstance(readiness, dict):
            if readiness.get("submission_attempted") is not False or readiness.get("answers_invented") is not False:
                errors.append("application readiness must not submit or invent answers")
            if readiness.get("ready_to_submit") is not False:
                errors.append("application readiness must remain a non-submitting checklist")
            fields = readiness.get("fields")
            if not isinstance(fields, list):
                errors.append("application readiness fields must be a list")
            else:
                for index, field in enumerate(fields):
                    if not isinstance(field, dict) or field.get("potential_auto_reject") != "unknown":
                        errors.append(f"application readiness field {index} must keep potential_auto_reject unknown")

    evaluators = data.get("evaluators")
    if not isinstance(evaluators, dict):
        errors.append("evaluators must be an object")
    else:
        expected = modes & SEMANTIC_MODES
        actual = set(evaluators)
        if actual != expected:
            errors.append(f"evaluators must match semantic modes; expected {sorted(expected)}, got {sorted(actual)}")
        for name, result in evaluators.items():
            if name not in SEMANTIC_MODES:
                continue
            for error in validate_evaluator(result, name):
                errors.append(f"evaluators.{name}: {error}")

    recommendations = data.get("recommended_changes")
    if not isinstance(recommendations, list):
        errors.append("recommended_changes must be a list")
    else:
        for index, item in enumerate(recommendations):
            path = f"recommended_changes[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path} must be an object")
                continue
            if item.get("priority") not in {"high", "medium", "low"}:
                errors.append(f"{path}.priority is invalid")
            for field in ("change", "reason"):
                if not nonempty(item.get(field)):
                    errors.append(f"{path}.{field} must be a non-empty string")
            if not isinstance(item.get("evidence"), list):
                errors.append(f"{path}.evidence must be a list")

    limitations = data.get("limitations")
    if not isinstance(limitations, list) or any(not nonempty(item) for item in limitations):
        errors.append("limitations must be a list of non-empty strings")
    sources = data.get("sources")
    if not isinstance(sources, list):
        errors.append("sources must be a list")
    else:
        for index, source in enumerate(sources):
            if not isinstance(source, dict) or not nonempty(source.get("path")) or not nonempty(source.get("purpose")):
                errors.append(f"sources[{index}] must contain non-empty path and purpose")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.report.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Valid clean Resume QA report: {args.report.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
