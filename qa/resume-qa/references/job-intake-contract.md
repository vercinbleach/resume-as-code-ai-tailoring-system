# Job URL intake contract

Use this contract only for the coordinator's browser intake. The clean evaluator must never browse.

## Safety boundary

- Inspect only the supplied job posting and the application flow reached from its real Apply control.
- Never type candidate or placeholder data, upload a file, sign in, accept consent, solve a challenge, or submit.
- Do not inspect cookies, local storage, private API responses, hidden DOM, or employer-only configuration.
- Treat auto-reject rules, ranking weights, fraud signals, and other non-visible settings as unknown.
- If a later form step requires interaction beyond harmless navigation, stop and record the blocker.

## Job-page capture

1. Record the supplied and canonical URLs, capture time, title, company, job ID, location, work model, employment type, and compensation when visible.
2. Inspect the whole posting. Expand job-specific accordions, tabs, or Read more controls needed to reveal content.
3. Capture the description, responsibilities, explicit must-haves, preferred qualifications, ambiguous requirements, technologies, languages, education, and experience thresholds.
4. Preserve exact wording in `text`. Put interpretation only in `classification_basis`.
5. Give every extracted item a source URL and a human-readable page location or heading.

## Atomic criteria compiler

For schema 1.1, compile the observed job content into `job.criteria` before scoring:

1. Split compound requirements so each criterion tests one fact only.
2. Assign a stable ID and one kind: `eligibility`, `must-have`, `preferred`, `responsibility`, or `unclear`.
3. Check that each scoreable criterion is stand-alone, singular, clear, specific, and objectively verifiable.
4. Record potential equal-opportunity or bias risk. Route an untestable criterion to `unclear`; never silently score it.
5. Add only defensible search terms and aliases. Search terms are deterministic text-query inputs, not proof that a criterion is met.

These checks adapt Ashby's published guidance for AI-assisted application-review criteria. They are a local implementation, not an Ashby configuration or official score.

## Application capture

1. Follow the visible Apply control and record redirects or a newly opened application tab.
2. Capture every visible step, field label, section, input type, required state, options, requested document, and accepted format.
3. Capture visible work-authorization, sponsorship, location, salary, start-date, education, experience, language, conflict, demographic, and consent questions.
4. Capture privacy, automated/AI review, application-limit, deadline, equal-opportunity, and other notices, including a visible action or opt-out link.
5. Record whether resume autofill is visibly offered; do not test it by uploading a file.

For every schema 1.1 field, keep these concepts separate:

- `required_question`: whether the form visibly requires an answer.
- `explicit_eligibility_gate`: whether the public wording explicitly makes the answer an eligibility condition.
- `gate_basis`: `explicit-eligibility`, `question-only`, `not-a-gate`, or `unknown`.
- `potential_auto_reject`: always `unknown`; required fields do not reveal employer auto-reject rules.

Never promote a question to `explicit-eligibility` merely because it is required. Auto-reject is configured separately in Ashby and is not observable from a public form unless the employer itself discloses the rule.

## Completeness and unknowns

- Use `complete` only when the entire visible job page and all safely accessible form content were inspected.
- Use `partial` when useful content was captured but a control, challenge, interaction, or later step blocked full inspection.
- Use `blocked` when the posting itself could not be meaningfully captured.
- Record unknowns explicitly. Do not fill missing values from general knowledge, LinkedIn, cached snippets, or another posting.
- `submission_attempted` must remain `false` in both capture and application objects.

## Output and validation

- New captures use schema 1.1. The validator continues to accept legacy 1.0 snapshots.
- Save the raw audit trail as `qa/jobs/<slug>/job-intake.json`.
- Run `scripts/validate_job_intake.py` before rendering.
- Render `job-description.md` with `scripts/render_job_description.py`; that normalized file is the only job artifact supplied to the clean evaluator.
- Keep `job-intake.json` coordinator-only because it contains navigation provenance and application metadata.

## Primary references

- Ashby application forms: https://docs.ashbyhq.com/application-forms
- Ashby auto-reject rules: https://docs.ashbyhq.com/auto-reject-applications
- Ashby AI-assisted application review: https://docs.ashbyhq.com/ai-assisted-application-review
- Ashby candidate full-text search: https://docs.ashbyhq.com/candidate-search
- Ashby bulk import and parsing notes: https://docs.ashbyhq.com/bulk-import-options
- Ashby candidate fraud detection: https://docs.ashbyhq.com/candidate-fraud-detection-overview-and-admin-settings
- Ashby application limits: https://docs.ashbyhq.com/application-limits
