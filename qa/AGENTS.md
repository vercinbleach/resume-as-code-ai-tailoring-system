# QA rules

- Use Codex as the only semantic evaluator. Do not call external LLMs or resume-scoring services.
- URL intake may inspect public job and application pages, but must never enter candidate data, upload files, authenticate, accept consent, or submit.
- Record only visible job and form evidence. Never claim hidden ranking, auto-reject, or employer configuration.
- A required question is not a hard gate unless visible wording explicitly defines eligibility.
- Keep the weighted Job Match score separate from the Ashby-style observable proxy; neither is official.
- Keep fraud detection and hidden ATS behavior out of scope.
- Treat the final PDF as the only candidate evidence. Job match and callback may additionally read the normalized job description.
- Never read resume YAML, `knowledge-base/`, previous CVs, public profiles, prior reports, browser state, or parent-chat conclusions while scoring.
- Never invent metrics, scope, technologies, employers, dates, outcomes, or application answers.
- Attach file-based evidence to every scored claim and mark unsupported claims as gaps.
- Run technical, leadership, job-match, and callback in separate new top-level Codex tasks; never use subagents, forks, or previously used evaluator tasks, and never average their scores.
- Launch applicable evaluator tasks concurrently. Each writes only its private sandbox `outbox/result.json`; read them only after all evaluators finish.
- Promote evaluator outputs only through `resume-qa/scripts/finalize-session.ps1`; evaluators never write directly to durable `qa/sessions/` results.
- Require a normalized job description for `job-match` and `callback`.
- Keep ephemeral task state under `.sandbox/`; only validated coordinator outputs become durable under `qa/sessions/`.
- Never pass prior scores to an evaluator. Compare sessions only after current finalization, label the exact session or PDF for every score set, and treat any modified PDF as unscored.
