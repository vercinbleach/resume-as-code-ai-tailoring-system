# Clean report contract

Create `report.md` and `report.json` only after all isolated evaluator outputs are complete and the full batch has passed sandbox validation.

## Input boundary

- Candidate evidence: `inputs/resume.pdf` only.
- Job-match and callback evidence: `inputs/resume.pdf` plus `inputs/job-description.md` only.
- `inputs/job-intake.json` is an audit trail for the coordinator and must not be passed to an evaluator.
- Deterministic PDF checks, parsed-profile projection, local text-search harness, and application-readiness checklist are coordinator artifacts. They never become semantic evidence for evaluators.
- Browser intake may create the normalized job description before evaluation. Evaluators must not consult source YAML, `knowledge-base/`, previous CVs, public profiles, the web, browser state, earlier sessions, or the coordinator's conversation.

## Evaluator isolation

- Technical, leadership, job match, and callback run in separate new top-level Codex tasks created for that session. Subagents, forks, and reused evaluator tasks are forbidden.
- Each task starts from its generated section in `task-prompts.md` and loads only its copied clean evaluator skill and copied input files inside its private sandbox.
- Pass raw input paths, never a summary or expected conclusion.
- Launch all applicable evaluators before reading any of their results.
- Each task writes only its private `outbox/result.json` and returns no report body through chat.
- Evaluators never read each other's files.
- No task writes directly to the durable session or `evaluators/`.
- After every task completes, invoke `scripts/finalize-session.ps1`. It verifies every manifest, skill snapshot, input hash, and outbox before freezing and validating all outputs in coordinator staging.
- Promote the staged evaluator directory only when the complete batch is valid. One invalid result leaves no durable `evaluators/` directory.
- Preserve every score and confidence exactly.

The v1 sandbox reduces accidental same-user filesystem contamination. It is not a container, separate OS identity, firewall, or security boundary. Its network policy is declarative only.

## Combined report

Include session metadata, deterministic PDF checks, coordinator artifacts, one independent section per completed evaluator, evidence, gaps, prioritized recommendations, limitations, and source paths. Do not calculate an overall score.

For job match schema 2.0, render explicit eligibility gates, atomic criteria, the separate Ashby-style observable proxy, exact evidence, parsing risks, consistency risks, and questions needed. Keep legacy matrices readable. Render deterministic Matches/Contains/Equals/Similar results from `ashby-text-search.json`, not from the semantic evaluator.

The weighted Job Match score and Ashby-style observable proxy are separate. Neither is an official Ashby score. A required form question is not a hard gate unless visible wording explicitly defines eligibility. Hidden auto-reject behavior and fraud detection remain unknown and out of scope.

Every semantic evidence object must name `resume.pdf`; job match and callback may also name `job-description.md`. Locations must use a PDF page and visible section or a job-description heading.

Use `scripts/finalize-session.ps1` as the promotion gate. It runs `scripts/validate_evaluator.py`, `scripts/assemble_report.py`, and `scripts/validate_report.py` in the required order and removes ephemeral sandboxes only after successful finalization.

## Cross-session comparisons

Cross-session score tables belong to the coordinator handoff, not evaluator
inputs. Create them only after the current report is valid, label each row with
the exact session or PDF identity, and never describe a changed PDF using an
older session's scores.
