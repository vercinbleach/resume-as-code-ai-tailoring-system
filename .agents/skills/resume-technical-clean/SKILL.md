---
name: resume-technical-clean
description: Score demonstrated technical strength using only a final resume PDF. Use in an isolated Codex evaluator when a clean employer-view technical score is required without repository, profile, prior-chat, or knowledge-base context.
---

# Clean technical resume QA

Evaluate only the resume PDF named in the task. Read `references/rubric.md` completely before scoring.

## Isolation boundary

- Read the supplied PDF, this `SKILL.md`, and `references/rubric.md` only.
- Do not read YAML sources, `knowledge-base/`, previous CVs, prior reports, GitHub, the web, or other project files.
- Do not use facts from the parent conversation or model memory about the candidate.
- Use a PDF extraction or rendering tool only to inspect the supplied PDF.
- Write only the exact evaluator output file assigned in the task. Do not modify any other file.

## Evaluation

1. Extract the visible content from every PDF page.
2. Apply every category and weight in `references/rubric.md`.
3. Award points only for evidence visible in the PDF.
4. Treat missing evidence as absent from the resume, not absent from the candidate's real profile.
5. Cite the page and section or bullet for every material finding.
6. Write only the JSON object defined in the rubric to the assigned output path.
7. Validate that the file contains valid JSON, then return only `completed` and the output path. Do not expose the report content in chat.
