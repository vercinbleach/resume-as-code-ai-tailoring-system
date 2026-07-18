---
name: resume-qa
description: Orchestrate black-box resume QA from the final PDF with isolated Codex evaluators. Also use when given a job-posting URL to inspect the complete posting and visible application form, create an auditable job snapshot, and produce technical, leadership, job-match, or hiring-manager callback reports under qa/sessions.
---

# Resume QA orchestrator

Evaluate the employer-facing PDF without modifying it. Keep browser intake separate from clean scoring.

## URL intake

When the user supplies a job URL:

1. Read `references/job-intake-contract.md` and `references/job-intake.schema.json` completely.
2. Run `scripts/new-job-intake.ps1 -Url <url> [-Slug <slug>]` and use its output path.
3. Use the Codex Browser skill to inspect the complete job page and the visible application flow.
4. Expand relevant job-content controls and follow the real Apply control. Never enter candidate data, upload a document, authenticate, accept consent, or submit an application. Stop when another step requires any of those actions.
5. Populate schema 1.1 `job-intake.json` only with observed facts. Compile compound requirements into atomic criteria and record every criterion-quality flag required by the contract.
6. For each form field, keep `required_question`, `explicit_eligibility_gate`, and `potential_auto_reject` separate. A required answer is not automatically a hard gate; hidden auto-reject behavior remains unknown.
7. Validate with `scripts/validate_job_intake.py`, then render the normalized evaluator input with `scripts/render_job_description.py`.
8. Start the clean QA session with `scripts/start-session.ps1 -JobIntake <path>`. The session copies both the raw intake and normalized description, but job-match and callback receive only `job-description.md`.

## Clean evaluation

1. Run `scripts/setup.ps1` if `qa/.venv` is missing.
2. Start a session with `scripts/start-session.ps1`. This creates the deterministic coordinator artifacts and one ephemeral sandbox per selected evaluator. Each sandbox contains a copied clean skill, only its allowed inputs, private `work/`, and `outbox/result.json`. The durable session has no `evaluators/` directory yet.
3. Read `references/report-contract.md`.
4. Resolve the current saved project, then create every selected semantic evaluator concurrently as a new top-level Codex project task using the local environment. Never spawn a subagent, fork this conversation, or reuse an evaluator task from an earlier session.
5. Open the generated `task-prompts.md`. Paste each evaluator section as the complete initial prompt for its fresh top-level task. Every referenced path must remain inside that evaluator's sandbox.
6. Never pass summaries, expected scores, profile data, earlier CVs, job-intake JSON, browser state, or earlier reports to an evaluator.
7. Require each task to write only `outbox/result.json` in its own sandbox. It must not write to `qa/sessions/` or another sandbox.
8. Wait until all selected top-level tasks complete before opening any result. Inspect task status only; do not read one evaluator's response or output while another is running.
9. Invoke `scripts/finalize-session.ps1 -Session <session-directory>`. It verifies every sandbox manifest and input hash, freezes all outputs in coordinator staging, validates the full batch, promotes the directory atomically, assembles and validates the report, records hashes, and removes the sandbox root only after success.
10. If the user requests a cross-version comparison, build it only after the
    current session finalizes. Label every score set with its exact QA session
    or PDF identity; never transfer a prior score to a modified PDF.

Job match requires a normalized job description. Without one, do not fabricate a match score.

## Commands

```powershell
.\qa\resume-qa\scripts\setup.ps1

.\qa\resume-qa\scripts\new-job-intake.ps1 `
  -Url https://jobs.example.com/backend-engineer

.\qa\.venv\Scripts\python.exe .\qa\resume-qa\scripts\validate_job_intake.py `
  qa/jobs/example-backend-engineer/job-intake.json

.\qa\resume-qa\scripts\start-session.ps1 `
  -Resume output/pdf/vincenzo-rosciano-one-page.pdf `
  -Modes technical,leadership,job-match,callback `
  -JobIntake qa/jobs/example-backend-engineer/job-intake.json

.\qa\resume-qa\scripts\finalize-session.ps1 `
  -Session qa/sessions/<session-id>
```

## Integrity rules

- Use Codex only for semantic evaluation.
- Browser intake may inspect public job and application pages; clean evaluators must not access the web. Sandbox network denial is declarative in v1, not technically enforced.
- Treat the final PDF as the only candidate evidence and the normalized job description as the only job evidence.
- Treat missing PDF evidence as a resume gap, not a claim about the candidate.
- Preserve independent scores; never average them.
- Keep prior scores out of evaluator prompts. Cross-session comparisons are a
  coordinator-only presentation step after the current clean batch completes.
- Use a new top-level Codex task for every evaluator and every run. Each evaluator reads only copied sandbox inputs and writes only its private sandbox outbox.
- Treat v1 as same-user logical filesystem isolation, not an OS security boundary.
- Label the technical score HackerRank-inspired, never official.
- Label the leadership score Monzo Level 50-adapted, never official.
- Label the callback score a project-local observable proxy, never an employer decision or callback probability.
- Label deterministic search and parsed-profile artifacts as local proxies, never official Ashby results.
- Treat fraud detection, hidden auto-reject rules, ranking weights, and employer-only ATS settings as unobservable and out of scope.
- Never submit an application.
