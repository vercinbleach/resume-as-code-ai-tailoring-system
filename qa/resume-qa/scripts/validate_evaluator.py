#!/usr/bin/env python3
"""Validate one isolated Resume QA evaluator result and its input boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EVALUATORS = {"technical", "leadership", "job-match", "callback"}
CONFIDENCE = {"high", "medium", "low"}
SEVERITY = {"positive", "high", "medium", "low"}
QUALITY_FLAGS = ("standalone", "singular", "clear", "specific", "objectively_verifiable")
CALLBACK_CATEGORIES = [
    ("Role-specific value", 25),
    ("Evidence and credibility", 25),
    ("Ownership and scope", 20),
    ("Differentiation and trajectory", 15),
    ("Clarity and risk", 15),
]


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def exact_keys(value: Any, path: str, expected: set[str], errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return False
    for field in sorted(expected - value.keys()):
        errors.append(f"{path}.{field} is required")
    for field in sorted(value.keys() - expected):
        errors.append(f"{path}.{field} is not allowed")
    return expected <= value.keys()


def validate_string_list(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return
    for index, item in enumerate(value):
        if not nonempty(item):
            errors.append(f"{path}[{index}] must be a non-empty string")


def validate_evidence(value: Any, path: str, allowed_sources: set[str], errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return
    for index, item in enumerate(value):
        current = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{current} must be an object")
            continue
        if item.get("source") not in allowed_sources:
            errors.append(f"{current}.source must be one of {sorted(allowed_sources)}")
        for field in ("claim", "location"):
            if not nonempty(item.get(field)):
                errors.append(f"{current}.{field} must be a non-empty string")


def validate_legacy_criteria(value: Any, path: str, statuses: set[str], errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return
    for index, item in enumerate(value):
        current = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{current} must be an object")
            continue
        for field in ("criterion", "rationale", "action"):
            if not nonempty(item.get(field)):
                errors.append(f"{current}.{field} must be a non-empty string")
        if item.get("status") not in statuses:
            errors.append(f"{current}.status is invalid")
        validate_evidence(item.get("job_evidence"), f"{current}.job_evidence", {"job-description.md"}, errors)
        validate_evidence(item.get("resume_evidence"), f"{current}.resume_evidence", {"resume.pdf"}, errors)


def validate_risk_sections(value: dict[str, Any], path: str, errors: list[str]) -> None:
    parsing_risks = value.get("parsing_risks")
    if not isinstance(parsing_risks, list) or not parsing_risks:
        errors.append(f"{path}.parsing_risks must be a non-empty list")
    else:
        for index, item in enumerate(parsing_risks):
            current = f"{path}.parsing_risks[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{current} must be an object")
                continue
            for field in ("check", "action"):
                if not nonempty(item.get(field)):
                    errors.append(f"{current}.{field} must be a non-empty string")
            if item.get("status") not in {"pass", "risk", "unknown"}:
                errors.append(f"{current}.status is invalid")
            validate_evidence(item.get("evidence"), f"{current}.evidence", {"resume.pdf"}, errors)

    consistency_risks = value.get("consistency_risks")
    if not isinstance(consistency_risks, list) or not consistency_risks:
        errors.append(f"{path}.consistency_risks must be a non-empty list")
    else:
        for index, item in enumerate(consistency_risks):
            current = f"{path}.consistency_risks[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{current} must be an object")
                continue
            for field in ("field", "action"):
                if not nonempty(item.get(field)):
                    errors.append(f"{current}.{field} must be a non-empty string")
            if item.get("status") not in {"consistent", "conflict", "unknown"}:
                errors.append(f"{current}.status is invalid")
            validate_evidence(item.get("resume_evidence"), f"{current}.resume_evidence", {"resume.pdf"}, errors)
            validate_evidence(item.get("job_evidence"), f"{current}.job_evidence", {"job-description.md"}, errors)


def validate_legacy_matrix(value: Any, errors: list[str]) -> None:
    path = "job_match_matrix"
    expected = {"hard_gates", "must_have", "preferred", "boolean_coverage", "parsing_risks", "consistency_risks", "questions_needed"}
    if not exact_keys(value, path, expected, errors):
        return
    validate_legacy_criteria(value.get("hard_gates"), f"{path}.hard_gates", {"meets", "does-not-meet", "needs-answer", "uncertain"}, errors)
    validate_legacy_criteria(value.get("must_have"), f"{path}.must_have", {"meets", "missing", "uncertain"}, errors)
    validate_legacy_criteria(value.get("preferred"), f"{path}.preferred", {"meets", "missing", "uncertain"}, errors)

    coverage = value.get("boolean_coverage")
    if not isinstance(coverage, list):
        errors.append(f"{path}.boolean_coverage must be a list")
    else:
        for index, item in enumerate(coverage):
            current = f"{path}.boolean_coverage[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{current} must be an object")
                continue
            if not nonempty(item.get("term")):
                errors.append(f"{current}.term must be a non-empty string")
            validate_string_list(item.get("aliases"), f"{current}.aliases", errors)
            if item.get("status") not in {"present", "missing", "uncertain"}:
                errors.append(f"{current}.status is invalid")
            validate_evidence(item.get("resume_evidence"), f"{current}.resume_evidence", {"resume.pdf"}, errors)
            if not nonempty(item.get("notes")):
                errors.append(f"{current}.notes must be a non-empty string")
    validate_risk_sections(value, path, errors)

    questions = value.get("questions_needed")
    if not isinstance(questions, list):
        errors.append(f"{path}.questions_needed must be a list")
    else:
        for index, item in enumerate(questions):
            current = f"{path}.questions_needed[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{current} must be an object")
                continue
            for field in ("question", "reason", "source"):
                if not nonempty(item.get(field)):
                    errors.append(f"{current}.{field} must be a non-empty string")
            if not isinstance(item.get("blocks_application"), bool):
                errors.append(f"{current}.blocks_application must be boolean")


def validate_quality(value: Any, path: str, errors: list[str]) -> None:
    keys = set(QUALITY_FLAGS) | {"bias_risk", "notes"}
    if not exact_keys(value, path, keys, errors):
        return
    for flag in QUALITY_FLAGS:
        if not isinstance(value.get(flag), bool):
            errors.append(f"{path}.{flag} must be boolean")
    if value.get("bias_risk") not in {"none", "possible", "high"}:
        errors.append(f"{path}.bias_risk is invalid")
    validate_string_list(value.get("notes"), f"{path}.notes", errors)


def validate_v2_matrix(value: Any, errors: list[str]) -> None:
    path = "job_match_matrix"
    expected = {"hard_gates", "criteria", "ashby_style_proxy", "parsing_risks", "consistency_risks", "questions_needed"}
    if not exact_keys(value, path, expected, errors):
        return

    gates = value.get("hard_gates")
    if not isinstance(gates, list):
        errors.append(f"{path}.hard_gates must be a list")
    else:
        for index, item in enumerate(gates):
            current = f"{path}.hard_gates[{index}]"
            keys = {"criterion", "gate_type", "status", "job_evidence", "resume_evidence", "rationale", "action"}
            if not exact_keys(item, current, keys, errors):
                continue
            for field in ("criterion", "rationale", "action"):
                if not nonempty(item.get(field)):
                    errors.append(f"{current}.{field} must be a non-empty string")
            if item.get("gate_type") != "explicit-eligibility":
                errors.append(f"{current}.gate_type must be explicit-eligibility")
            if item.get("status") not in {"meets", "does-not-meet", "needs-answer", "uncertain"}:
                errors.append(f"{current}.status is invalid")
            validate_evidence(item.get("job_evidence"), f"{current}.job_evidence", {"job-description.md"}, errors)
            validate_evidence(item.get("resume_evidence"), f"{current}.resume_evidence", {"resume.pdf"}, errors)

    criteria = value.get("criteria")
    proxy_counts = {"meets": 0, "does-not-meet": 0, "undecided": 0}
    ids: set[str] = set()
    if not isinstance(criteria, list) or not criteria:
        errors.append(f"{path}.criteria must be a non-empty list")
    else:
        for index, item in enumerate(criteria):
            current = f"{path}.criteria[{index}]"
            keys = {"id", "kind", "criterion", "quality", "included_in_proxy", "status", "job_evidence", "resume_evidence", "rationale", "action"}
            if not exact_keys(item, current, keys, errors):
                continue
            criterion_id = item.get("id")
            if not nonempty(criterion_id):
                errors.append(f"{current}.id must be a non-empty string")
            elif criterion_id in ids:
                errors.append(f"{current}.id must be unique")
            else:
                ids.add(criterion_id)
            if item.get("kind") not in {"eligibility", "must-have", "preferred", "responsibility", "unclear"}:
                errors.append(f"{current}.kind is invalid")
            for field in ("criterion", "rationale", "action"):
                if not nonempty(item.get(field)):
                    errors.append(f"{current}.{field} must be a non-empty string")
            validate_quality(item.get("quality"), f"{current}.quality", errors)
            included = item.get("included_in_proxy")
            if not isinstance(included, bool):
                errors.append(f"{current}.included_in_proxy must be boolean")
            if item.get("kind") == "unclear" and included is True:
                errors.append(f"{current}.included_in_proxy must be false for unclear criteria")
            quality = item.get("quality") if isinstance(item.get("quality"), dict) else {}
            if included is True and any(quality.get(flag) is not True for flag in QUALITY_FLAGS):
                errors.append(f"{current}.included_in_proxy requires all five quality checks to pass")
            if included is True and quality.get("bias_risk") == "high":
                errors.append(f"{current}.included_in_proxy must be false when bias_risk is high")
            status = item.get("status")
            if status not in proxy_counts:
                errors.append(f"{current}.status is invalid")
            elif included is True:
                proxy_counts[status] += 1
            validate_evidence(item.get("job_evidence"), f"{current}.job_evidence", {"job-description.md"}, errors)
            validate_evidence(item.get("resume_evidence"), f"{current}.resume_evidence", {"resume.pdf"}, errors)

    proxy = value.get("ashby_style_proxy")
    proxy_keys = {"label", "official_ashby_score", "formula", "counts", "criteria_met_percentage"}
    if exact_keys(proxy, f"{path}.ashby_style_proxy", proxy_keys, errors):
        if proxy.get("label") != "Ashby-style observable proxy":
            errors.append(f"{path}.ashby_style_proxy.label is invalid")
        if proxy.get("official_ashby_score") is not False:
            errors.append(f"{path}.ashby_style_proxy.official_ashby_score must be false")
        if proxy.get("formula") != "meets / total observable atomic criteria":
            errors.append(f"{path}.ashby_style_proxy.formula is invalid")
        counts = proxy.get("counts")
        if exact_keys(counts, f"{path}.ashby_style_proxy.counts", {"meets", "does_not_meet", "undecided", "total"}, errors):
            observed = {
                "meets": proxy_counts["meets"],
                "does_not_meet": proxy_counts["does-not-meet"],
                "undecided": proxy_counts["undecided"],
            }
            observed["total"] = sum(observed.values())
            for key, expected_value in observed.items():
                if counts.get(key) != expected_value:
                    errors.append(f"{path}.ashby_style_proxy.counts.{key} must equal {expected_value}")
            percentage = proxy.get("criteria_met_percentage")
            expected_percentage = None if observed["total"] == 0 else round(100 * observed["meets"] / observed["total"], 1)
            if percentage != expected_percentage:
                errors.append(f"{path}.ashby_style_proxy.criteria_met_percentage must equal {expected_percentage!r}")

    validate_risk_sections(value, path, errors)
    questions = value.get("questions_needed")
    if not isinstance(questions, list):
        errors.append(f"{path}.questions_needed must be a list")
    else:
        for index, item in enumerate(questions):
            current = f"{path}.questions_needed[{index}]"
            keys = {"question", "reason", "source", "blocks_application", "explicit_eligibility_gate", "potential_auto_reject"}
            if not exact_keys(item, current, keys, errors):
                continue
            for field in ("question", "reason", "source"):
                if not nonempty(item.get(field)):
                    errors.append(f"{current}.{field} must be a non-empty string")
            if not isinstance(item.get("blocks_application"), bool):
                errors.append(f"{current}.blocks_application must be boolean")
            if not isinstance(item.get("explicit_eligibility_gate"), bool):
                errors.append(f"{current}.explicit_eligibility_gate must be boolean")
            if item.get("potential_auto_reject") != "unknown":
                errors.append(f"{current}.potential_auto_reject must remain unknown")


def validate(data: Any, expected: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Evaluator result must be an object"]

    required = {"evaluator", "score", "confidence", "summary", "categories", "findings", "gaps", "input_boundary"}
    if expected == "job-match":
        required.add("job_match_matrix")
    if expected == "callback":
        required.add("decision")
    elif "decision" in data:
        errors.append("decision is allowed only for callback")
    for field in sorted(required - data.keys()):
        errors.append(f"Missing required field: {field}")

    if data.get("evaluator") != expected:
        errors.append(f"evaluator must be {expected}")
    score = data.get("score")
    if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 100:
        errors.append("score must be a number from 0 to 100")
    if data.get("confidence") not in CONFIDENCE:
        errors.append("confidence must be high, medium, or low")
    if not nonempty(data.get("summary")):
        errors.append("summary must be a non-empty string")

    categories = data.get("categories")
    category_total = 0.0
    maximum_total = 0.0
    if not isinstance(categories, list) or not categories:
        errors.append("categories must be a non-empty list")
    else:
        for index, category in enumerate(categories):
            current = f"categories[{index}]"
            if not isinstance(category, dict):
                errors.append(f"{current} must be an object")
                continue
            if not nonempty(category.get("name")):
                errors.append(f"{current}.name must be a non-empty string")
            category_score = category.get("score")
            maximum = category.get("maximum")
            if not isinstance(maximum, (int, float)) or isinstance(maximum, bool) or maximum <= 0:
                errors.append(f"{current}.maximum must be greater than zero")
                continue
            if not isinstance(category_score, (int, float)) or isinstance(category_score, bool) or not 0 <= category_score <= maximum:
                errors.append(f"{current}.score must be between zero and maximum")
                continue
            if not nonempty(category.get("rationale")):
                errors.append(f"{current}.rationale must be a non-empty string")
            category_total += float(category_score)
            maximum_total += float(maximum)
    if maximum_total and abs(maximum_total - 100) > 0.001:
        errors.append("category maximum values must total 100")
    if maximum_total and isinstance(score, (int, float)) and abs(category_total - float(score)) > 0.001:
        errors.append("score must equal the category-score sum")
    if expected == "callback" and isinstance(categories, list):
        observed = [
            (category.get("name"), category.get("maximum"))
            for category in categories
            if isinstance(category, dict)
        ]
        if observed != CALLBACK_CATEGORIES:
            errors.append("callback categories and maxima must match the rubric order")

    boundary = data.get("input_boundary")
    expected_job = "job-description.md" if expected in {"job-match", "callback"} else None
    if not isinstance(boundary, dict):
        errors.append("input_boundary must be an object")
    else:
        if boundary.get("resume") != "resume.pdf":
            errors.append("input_boundary.resume must be resume.pdf")
        if boundary.get("job_description") != expected_job:
            errors.append(f"input_boundary.job_description must be {expected_job!r}")
        if boundary.get("external_context_used") is not False:
            errors.append("input_boundary.external_context_used must be false")

    allowed_sources = {"resume.pdf"}
    if expected in {"job-match", "callback"}:
        allowed_sources.add("job-description.md")
    findings = data.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a list")
    else:
        for index, finding in enumerate(findings):
            current = f"findings[{index}]"
            if not isinstance(finding, dict):
                errors.append(f"{current} must be an object")
                continue
            if finding.get("severity") not in SEVERITY:
                errors.append(f"{current}.severity is invalid")
            if not nonempty(finding.get("finding")):
                errors.append(f"{current}.finding must be a non-empty string")
            validate_evidence(finding.get("evidence"), f"{current}.evidence", allowed_sources, errors)

    gaps = data.get("gaps")
    if not isinstance(gaps, list) or any(not nonempty(item) for item in gaps):
        errors.append("gaps must be a list of non-empty strings")

    if expected == "job-match":
        if data.get("schema_version") == "2.0":
            validate_v2_matrix(data.get("job_match_matrix"), errors)
        elif "schema_version" in data:
            errors.append("job-match schema_version must be 2.0 when present")
        else:
            validate_legacy_matrix(data.get("job_match_matrix"), errors)

    if expected == "callback":
        if "job_match_matrix" in data:
            errors.append("callback must not contain job_match_matrix")
        if data.get("schema_version") != "1.0":
            errors.append("callback schema_version must be 1.0")
        decision = data.get("decision")
        if decision not in {"strong-callback", "callback", "borderline", "no-callback"}:
            errors.append("callback decision is invalid")
        elif isinstance(score, (int, float)) and not isinstance(score, bool):
            expected_decision = (
                "strong-callback" if score >= 80 else
                "callback" if score >= 65 else
                "borderline" if score >= 50 else
                "no-callback"
            )
            if decision != expected_decision:
                errors.append(f"callback decision must be {expected_decision} for score {score}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--expected", required=True, choices=sorted(EVALUATORS))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.result.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    errors = validate(data, args.expected)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Valid isolated {args.expected} evaluator result: {args.result.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
