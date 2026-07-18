---
name: resume-callback-clean
description: Estimate whether a skeptical hiring manager would advance one final resume PDF to an initial interview for one normalized job description. Use in an isolated Codex evaluator when a clean callback decision is required without repository, browser, profile, prior-chat, or knowledge-base context.
---

# Clean hiring-manager callback QA

Evaluate only the resume PDF and normalized job description named in the task. Read `references/rubric.md` completely before scoring.

## Isolation boundary

- Read only the supplied PDF, supplied job description, this `SKILL.md`, and `references/rubric.md`.
- Do not read raw job-intake JSON, coordinator artifacts, browser state, resume sources, `knowledge-base/`, previous CVs, prior reports, public profiles, the web, or other project files.
- Do not use facts from the parent conversation or model memory about the candidate or company.
- Use PDF extraction or rendering only to inspect the supplied PDF.
- Write only the assigned evaluator JSON file.

## Evaluation

1. Extract all visible content from the PDF and normalized job description.
2. Apply every category and weight in `references/rubric.md`.
3. Judge only whether the visible package gives a hiring manager enough relevant, credible, and differentiated evidence to justify an initial interview.
4. Do not rescore eligibility or requirement coverage; that belongs to Job Match. Do not simulate interview performance.
5. Treat titles, keywords, and metrics as signals only when the surrounding claim demonstrates contribution, context, and a defensible outcome.
6. Ignore protected or personal characteristics. Never infer them from names, dates, locations, education, or contact details.
7. Cite the exact PDF and job-description location for every material finding.
8. Treat missing evidence as a resume gap, not proof the candidate lacks the capability.
9. Write exactly the JSON object defined in the rubric, validate it, and return only `completed` plus its path.
