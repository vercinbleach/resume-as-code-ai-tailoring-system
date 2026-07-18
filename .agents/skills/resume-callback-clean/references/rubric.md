# Hiring-manager callback rubric

## Provenance and scope

This is a project-local observable proxy, not an employer decision, callback probability, or official hiring framework.

The rubric distills the skeptical hiring-manager stage from the local `The Callback System` guide: test whether claims are relevant, specific, credible, attributable, and worth probing in an interview. The clean evaluator does not read that guide at runtime and uses only the supplied final PDF and normalized job description.

Job Match asks whether visible requirements are met. Callback asks a different question: assuming the package reached a hiring manager, does it create enough confidence and interest to spend interview time?

| Category | Maximum | Visible evidence |
| --- | ---: | --- |
| Role-specific value | 25 | Recent experience and accomplishments make the likely contribution to this role immediately clear |
| Evidence and credibility | 25 | Claims include defensible outcomes, methods, context, and plausible metrics instead of unsupported assertion |
| Ownership and scope | 20 | The candidate's contribution, autonomy, complexity, scale, decisions, and boundaries are understandable |
| Differentiation and trajectory | 15 | Memorable strengths, progression, unusual depth, or repeated high-value patterns distinguish the candidate |
| Clarity and risk | 15 | The narrative is concise and internally coherent, with limited ambiguity, jargon, chronology risk, or credibility friction |

Category maxima total 100. The score must equal the category-score sum.

## Scoring anchors

- `0%`: no visible evidence or directly counterproductive evidence.
- Approximately `25%`: generic or title-led signal with little proof.
- Approximately `50%`: some relevant evidence, but important claims remain weak, ambiguous, or undifferentiated.
- Approximately `75%`: clear and credible evidence with only limited hiring-manager friction.
- `100%`: unusually strong, role-specific, attributable, and defensible evidence throughout the PDF.

Do not award points merely because a keyword appears. Do not require a metric in every bullet; qualitative outcomes may score when they are specific and defensible. Do not assume an impressive metric is attributable when the bullet does not establish the candidate's contribution.

## Decision thresholds

The decision is determined by the final score:

- `strong-callback`: 80 through 100.
- `callback`: 65 through 79.999.
- `borderline`: 50 through 64.999.
- `no-callback`: below 50.

This label is a local decision proxy, not a prediction that an employer will call.

## Output

Write exactly one JSON object:

```json
{
  "schema_version": "1.0",
  "evaluator": "callback",
  "decision": "strong-callback|callback|borderline|no-callback",
  "score": 0,
  "confidence": "high|medium|low",
  "summary": "Skeptical hiring-manager decision based only on the supplied PDF and job description.",
  "categories": [
    {"name": "Role-specific value", "score": 0, "maximum": 25, "rationale": "Reason"},
    {"name": "Evidence and credibility", "score": 0, "maximum": 25, "rationale": "Reason"},
    {"name": "Ownership and scope", "score": 0, "maximum": 20, "rationale": "Reason"},
    {"name": "Differentiation and trajectory", "score": 0, "maximum": 15, "rationale": "Reason"},
    {"name": "Clarity and risk", "score": 0, "maximum": 15, "rationale": "Reason"}
  ],
  "findings": [
    {
      "severity": "positive|high|medium|low",
      "finding": "Reason to call or pass",
      "evidence": [
        {"source": "resume.pdf|job-description.md", "claim": "Visible evidence", "location": "Page or heading"}
      ]
    }
  ],
  "gaps": ["Visible evidence whose absence creates callback friction"],
  "input_boundary": {
    "resume": "resume.pdf",
    "job_description": "job-description.md",
    "external_context_used": false
  }
}
```
