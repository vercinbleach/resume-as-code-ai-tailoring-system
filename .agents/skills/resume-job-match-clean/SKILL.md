---
name: resume-job-match-clean
description: Compare one final resume PDF with one normalized job-and-application snapshot. Use in an isolated Codex evaluator to score visible fit and produce explicit eligibility gates, atomic criteria, exact evidence, parsing risk, consistency risk, unanswered questions, and a separate Ashby-style observable proxy without repository, browser, prior-chat, profile, or knowledge-base context.
---

# Clean job-match resume QA

Evaluate only the resume PDF and normalized job description named in the task. Read `references/rubric.md` completely before scoring.

## Isolation boundary

- Read only the supplied PDF, supplied job description, this `SKILL.md`, and `references/rubric.md`.
- Do not read raw job-intake JSON, deterministic coordinator artifacts, browser state, YAML, `knowledge-base/`, previous CVs, prior reports, public profiles, the web, or other project files.
- Do not use facts from the parent conversation or model memory about the candidate or company.
- Use PDF extraction or rendering only to inspect the supplied PDF.
- Write only the assigned evaluator JSON file.

## Evaluation

1. Extract all visible content from the PDF and normalized job description.
2. Use the compiled atomic criteria when present. For a legacy snapshot, split compound job requirements into independent criteria before evaluating them.
3. Keep explicit eligibility gates separate from required application questions. A required question is not a hard gate unless the visible wording explicitly makes it an eligibility condition.
4. Apply every category and weight in `references/rubric.md` to produce the local weighted Job Match score.
5. Evaluate every atomic criterion as `meets`, `does-not-meet`, or `undecided`, citing exact PDF and job-description locations.
6. Calculate the separate Ashby-style observable proxy exactly as defined in the rubric. Never label either metric an official Ashby score.
7. Use only technically defensible synonyms. Never reward keyword stuffing or text presence without evidence.
8. Put unresolved required form questions in `questions_needed`; mark `blocks_application` from the visible required state, not from a guessed rejection rule.
9. Mark LinkedIn, application-answer, or other external consistency checks `unknown`; do not browse to resolve them.
10. Treat capture blockers, hidden ATS settings, auto-reject configuration, fraud detection, and ranking rules as limitations, never as inferred behavior.
11. Validate the JSON shape mentally, write only the assigned file, and return only `completed` plus its path.
