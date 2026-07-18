#!/usr/bin/env python3
"""Assemble isolated evaluator outputs and deterministic artifacts into reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_evaluator import validate as validate_evaluator
from validate_report import validate as validate_report


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def markdown_cell(value: Any) -> str:
    text = str(value).replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")
    return text.strip() or "N/A"


def evidence_cell(items: list[dict[str, Any]]) -> str:
    if not items:
        return "N/A"
    return "<br>".join(markdown_cell(f"{item['claim']} [{item['location']}]") for item in items)


def render_criteria_table(lines: list[str], title: str, rows: list[dict[str, Any]]) -> None:
    lines.extend([
        "",
        f"#### {title}",
        "",
        "| Criterion | Status | Exact job evidence | Exact resume evidence | Rationale / action |",
        "| --- | --- | --- | --- | --- |",
    ])
    if not rows:
        lines.append("| None observed | N/A | N/A | N/A | N/A |")
        return
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row["criterion"]),
                    markdown_cell(row["status"]),
                    evidence_cell(row["job_evidence"]),
                    evidence_cell(row["resume_evidence"]),
                    markdown_cell(f"{row['rationale']} Action: {row['action']}"),
                ]
            )
            + " |"
        )


def render_risks_and_questions(lines: list[str], matrix: dict[str, Any], v2: bool) -> None:
    lines.extend(["", "#### Parsing risks", "", "| Check | Status | Evidence | Action |", "| --- | --- | --- | --- |"])
    for row in matrix["parsing_risks"]:
        lines.append(
            f"| {markdown_cell(row['check'])} | {markdown_cell(row['status'])} | "
            f"{evidence_cell(row['evidence'])} | {markdown_cell(row['action'])} |"
        )

    lines.extend(["", "#### Consistency risks", "", "| Field | Status | Resume evidence | Job/form evidence | Action |", "| --- | --- | --- | --- | --- |"])
    for row in matrix["consistency_risks"]:
        lines.append(
            f"| {markdown_cell(row['field'])} | {markdown_cell(row['status'])} | "
            f"{evidence_cell(row['resume_evidence'])} | {evidence_cell(row['job_evidence'])} | {markdown_cell(row['action'])} |"
        )

    lines.extend(["", "#### Questions needed before applying", "", "| Question | Why needed | Source | Blocks form | Explicit gate | Auto-reject |", "| --- | --- | --- | --- | --- | --- |"])
    if not matrix["questions_needed"]:
        lines.append("| None | N/A | N/A | No | No | Unknown |")
    for row in matrix["questions_needed"]:
        explicit = row.get("explicit_eligibility_gate", False) if v2 else "unknown"
        auto_reject = row.get("potential_auto_reject", "unknown")
        lines.append(
            f"| {markdown_cell(row['question'])} | {markdown_cell(row['reason'])} | {markdown_cell(row['source'])} | "
            f"{'Yes' if row['blocks_application'] else 'No'} | {markdown_cell(explicit)} | {markdown_cell(auto_reject)} |"
        )


def render_job_match_matrix(lines: list[str], evaluator: dict[str, Any]) -> None:
    matrix = evaluator["job_match_matrix"]
    v2 = evaluator.get("schema_version") == "2.0"
    lines.extend(["", "### Job-match decision matrix"])
    render_criteria_table(lines, "Explicit eligibility gates", matrix["hard_gates"])
    if v2:
        proxy = matrix["ashby_style_proxy"]
        counts = proxy["counts"]
        percentage = "n/a" if proxy["criteria_met_percentage"] is None else f"{proxy['criteria_met_percentage']}%"
        lines.extend([
            "",
            "#### Ashby-style observable proxy",
            "",
            f"- Criteria met: {percentage}",
            f"- Counts: {counts['meets']} meets / {counts['does_not_meet']} does not meet / {counts['undecided']} undecided / {counts['total']} total",
            "- This is a local observable proxy, not an official Ashby score.",
            "",
            "| ID | Kind | Atomic criterion | Status | Included | Exact resume evidence | Action |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ])
        for row in matrix["criteria"]:
            lines.append(
                f"| {markdown_cell(row['id'])} | {markdown_cell(row['kind'])} | {markdown_cell(row['criterion'])} | "
                f"{markdown_cell(row['status'])} | {'Yes' if row['included_in_proxy'] else 'No'} | "
                f"{evidence_cell(row['resume_evidence'])} | {markdown_cell(row['action'])} |"
            )
    else:
        render_criteria_table(lines, "Must-have criteria", matrix["must_have"])
        render_criteria_table(lines, "Preferred criteria", matrix["preferred"])
        lines.extend(["", "#### Legacy Boolean coverage", "", "| Term | Defensible aliases | Status | Resume evidence | Notes |", "| --- | --- | --- | --- | --- |"])
        if not matrix["boolean_coverage"]:
            lines.append("| None extracted | N/A | N/A | N/A | N/A |")
        for row in matrix["boolean_coverage"]:
            lines.append(
                "| " + " | ".join(
                    [
                        markdown_cell(row["term"]),
                        markdown_cell(", ".join(row["aliases"]) or "N/A"),
                        markdown_cell(row["status"]),
                        evidence_cell(row["resume_evidence"]),
                        markdown_cell(row["notes"]),
                    ]
                ) + " |"
            )
    render_risks_and_questions(lines, matrix, v2)


def render_coordinator_artifacts(lines: list[str], artifacts: dict[str, Any]) -> None:
    profile = artifacts.get("parsed_profile")
    search = artifacts.get("ashby_text_search")
    readiness = artifacts.get("application_readiness")
    if not any((profile, search, readiness)):
        return
    lines.extend(["", "## Deterministic ATS-style checks"])
    if profile:
        summary = profile["summary"]
        lines.extend([
            "",
            "### Parsed-profile projection",
            "",
            f"- Contact fields: {summary['contact_fields_projected']}/4",
            f"- Experience entries: {summary['experience_entries']}",
            f"- Education entries: {summary['education_entries']}",
            f"- Skill groups: {summary['skill_groups']}",
            f"- Projection issues: {summary['issues']}",
            "- Local pypdf projection; not an official Ashby parser result.",
        ])
    if search:
        summary = search["summary"]
        lines.extend([
            "",
            "### Ashby-like full-text search proxy",
            "",
            "| Criteria queried | Matches | Contains | Equals | Similar |",
            "| ---: | ---: | ---: | ---: | ---: |",
            f"| {summary['criteria']} | {summary['matches']} | {summary['contains']} | {summary['equals']} | {summary['similar']} |",
            "",
            "These are deterministic local approximations, not results from Ashby or an employer ATS.",
        ])
    if readiness:
        lines.extend([
            "",
            "### Application readiness",
            "",
            "| Field | Required question | Explicit eligibility gate | Answer status | Needs user | Potential auto-reject | Risk |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ])
        for row in readiness["fields"]:
            lines.append(
                f"| {markdown_cell(row['label'])} | {markdown_cell(row['required_question'])} | "
                f"{markdown_cell(row['explicit_eligibility_gate'])} | {markdown_cell(row['answer_status'])} | "
                f"{'Yes' if row['needs_user'] else 'No'} | unknown | {markdown_cell(row['risk'])} |"
            )
        lines.extend(["", "No answer was invented, entered, uploaded, or submitted."])


def build_recommendations(evaluators: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    seen: set[str] = set()
    for evaluator_name, evaluator in evaluators.items():
        for finding in evaluator.get("findings", []):
            severity = finding.get("severity")
            finding_text = finding.get("finding", "").strip()
            if severity == "positive" or not finding_text or finding_text in seen:
                continue
            seen.add(finding_text)
            recommendations.append(
                {
                    "priority": severity if severity in {"high", "medium", "low"} else "medium",
                    "change": f"Address the visible resume gap: {finding_text}",
                    "reason": f"Identified independently by the {evaluator_name} PDF-only evaluator.",
                    "evidence": finding.get("evidence", []),
                }
            )
    priority_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(recommendations, key=lambda item: priority_order[item["priority"]])


def evaluator_label(name: str, heading: bool = False) -> str:
    if name == "technical":
        return "Technical - HackerRank-inspired" if heading else "Technical (HackerRank-inspired)"
    if name == "leadership":
        return "Leadership - Monzo Level 50-adapted" if heading else "Leadership (Monzo Level 50-adapted)"
    if name == "callback":
        return "Hiring Manager Callback - local proxy" if heading else "Hiring Manager Callback (local proxy)"
    return name.replace("-", " ").title()


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Clean Resume QA - {report['session_id']}",
        "",
        "## Session",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Final PDF: `{report['resume']}`",
        f"- Job description: `{report['job_description']}`" if report["job_description"] else "- Job description: Not provided",
        f"- Job intake: `{report['job_intake']}`" if report.get("job_intake") else "- Job intake: Not provided",
        f"- Architecture: `{report['architecture']}`",
        "- Candidate evidence: final PDF only",
        "",
        "## Deterministic PDF checks",
        "",
        f"- Passed: {report['pdf_checks']['passed']}/{report['pdf_checks']['total']}",
        f"- Extracted word-like tokens: {report['pdf_checks']['extracted_word_count']}",
        "",
        "## Independent evaluator scores",
        "",
        "| Evaluator | Score | Confidence |",
        "| --- | ---: | --- |",
    ]
    for name, evaluator in report["evaluators"].items():
        label = evaluator_label(name)
        lines.append(f"| {label} | {evaluator['score']}/100 | {evaluator['confidence'].title()} |")

    for name, evaluator in report["evaluators"].items():
        label = evaluator_label(name, heading=True)
        lines.extend(["", f"## {label}", "", evaluator["summary"], "", "| Category | Score |", "| --- | ---: |"])
        for category in evaluator["categories"]:
            lines.append(f"| {category['name']} | {category['score']}/{category['maximum']} |")
        if name == "job-match":
            render_job_match_matrix(lines, evaluator)
        if name == "callback":
            lines.extend(["", f"- Decision: `{evaluator['decision']}`"])
        lines.extend(["", "### Findings", ""])
        lines.extend(f"- [{finding['severity']}] {finding['finding']}" for finding in evaluator["findings"])
        lines.extend(["", "### Evidence gaps", ""])
        lines.extend(f"- {gap}" for gap in evaluator["gaps"])

    render_coordinator_artifacts(lines, report.get("coordinator_artifacts", {}))
    lines.extend(["", "## Prioritized recommendations", ""])
    if report["recommended_changes"]:
        lines.extend(f"- [{item['priority']}] {item['change']}" for item in report["recommended_changes"])
    else:
        lines.append("- No semantic recommendation was emitted.")

    lines.extend(["", "## Isolation and limitations", ""])
    lines.extend(f"- {limitation}" for limitation in report["limitations"])
    lines.extend(["", "## Sources", ""])
    lines.extend(f"- `{source['path']}` - {source['purpose']}" for source in report["sources"])
    return "\n".join(lines) + "\n"


def optional_artifact(session: Path, manifest: dict[str, Any], name: str) -> dict[str, Any] | None:
    relative = manifest.get("artifacts", {}).get(name)
    if not relative:
        return None
    path = session / relative
    return load_json(path) if path.is_file() else None


def assemble(session: Path) -> dict[str, Any]:
    manifest = load_json(session / "manifest.json")
    pdf_checks = load_json(session / "pdf-checks.json")
    selected = [mode for mode in manifest["modes"] if mode != "pdf"]
    evaluators: dict[str, dict[str, Any]] = {}
    for name in selected:
        result_path = session / "evaluators" / f"{name}.json"
        if not result_path.is_file():
            raise ValueError(f"Missing evaluator result: {result_path}")
        result = load_json(result_path)
        errors = validate_evaluator(result, name)
        if errors:
            raise ValueError(f"Invalid {name} evaluator result: {'; '.join(errors)}")
        evaluators[name] = result

    parsed_profile = optional_artifact(session, manifest, "parsed_profile")
    text_search = optional_artifact(session, manifest, "ashby_text_search")
    readiness = optional_artifact(session, manifest, "application_readiness")
    limitations = [
        "Semantic evaluators used only their declared clean inputs; missing evidence is a resume gap, not a claim about the candidate's real ability.",
        "Each semantic score came from a new top-level Codex task created for this session and was not adjusted by the coordinator.",
    ]
    if "technical" in evaluators:
        limitations.append("The technical score is HackerRank-inspired, not an official HackerRank result.")
    if "leadership" in evaluators:
        limitations.append("The leadership score adapts Monzo Engineering Manager Level 50 with local 34/33/33 normalization; it is not an official Monzo result.")
    if "job-match" in evaluators and evaluators["job-match"].get("schema_version") == "2.0":
        limitations.append("The Ashby-style observable proxy is local and separate from the weighted Job Match score; neither is an official Ashby result.")
    if "callback" in evaluators:
        limitations.append("The callback score is a project-local observable proxy, not an employer decision or callback probability.")
    limitations.extend([
        "Independent evaluator scores were not combined into an overall score.",
        "Fraud detection, hidden auto-reject rules, ranking weights, and employer-only ATS settings were not observable and were not simulated.",
    ])

    report = {
        "session_id": manifest["session_id"],
        "generated_at": manifest["generated_at"],
        "architecture": manifest["architecture"],
        "resume": manifest["resume"],
        "job_description": manifest["job_description"],
        "job_intake": manifest.get("job_intake"),
        "modes": manifest["modes"],
        "pdf_checks": {
            "source": "pdf-checks.json",
            "passed": pdf_checks["summary"]["passed"],
            "failed": pdf_checks["summary"]["failed"],
            "total": pdf_checks["summary"]["total"],
            "page_count": pdf_checks["document"]["pages"],
            "extracted_word_count": pdf_checks["metrics"]["extracted_word_count"],
            "linkedin_and_github_clickable": pdf_checks["checks"]["linkedin_and_github_clickable"]["passed"],
            "ashby_upload_under_50mb": pdf_checks["checks"].get("ashby_upload_under_50mb", {}).get("passed"),
            "ashby_fulltext_and_autofill_under_16mb": pdf_checks["checks"].get("ashby_fulltext_and_autofill_under_16mb", {}).get("passed"),
        },
        "coordinator_artifacts": {
            "parsed_profile": parsed_profile,
            "ashby_text_search": text_search,
            "application_readiness": readiness,
        },
        "evaluators": evaluators,
        "recommended_changes": build_recommendations(evaluators),
        "limitations": limitations,
        "sources": [
            {"path": "inputs/resume.pdf", "purpose": "Only candidate evidence supplied to semantic evaluators"},
            {"path": "pdf-checks.json", "purpose": "Deterministic PDF preflight"},
        ],
    }
    if parsed_profile:
        report["sources"].append({"path": "parsed-profile.json", "purpose": "Local ATS-like structured projection"})
    if text_search:
        report["sources"].append({"path": "ashby-text-search.json", "purpose": "Deterministic full-text query proxies"})
    if readiness:
        report["sources"].append({"path": "application-readiness.json", "purpose": "Coordinator-only application checklist"})
    if manifest["job_description"]:
        report["sources"].append({"path": "inputs/job-description.md", "purpose": "Job-specific evaluator comparison input"})
        if manifest.get("job_intake"):
            report["sources"].append({"path": "inputs/job-intake.json", "purpose": "Coordinator-only audit trail for visible browser intake"})
            report["limitations"].append("The coordinator inspected only visible job and application pages and did not submit an application.")
    else:
        report["limitations"].append("Job match was not run because no job description was supplied.")

    errors = validate_report(report)
    if errors:
        raise ValueError(f"Combined report is invalid: {'; '.join(errors)}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session = args.session.resolve()
    try:
        report = assemble(session)
    except (OSError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    (session / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (session / "report.md").write_text(render_markdown(report), encoding="utf-8")
    print(session / "report.md")
    print(session / "report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
