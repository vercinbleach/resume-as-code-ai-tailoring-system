# Leadership resume rubric

## Provenance

Adapt this rubric from the public Monzo Engineering Manager Progression Framework v2.0, specifically Engineering Manager Level 50:

<https://monzo.com/documents/engineering-manager-framework-v2-0.pdf>

Monzo defines the role through `Team and execution`, `People`, and `Leadership` and describes the framework as an outcome-focused compass rather than a numeric checklist. Monzo does not publish a resume score. This harness assigns the three pillars equal influence and uses `34/33/33` only to produce a 100-point project-local coverage score. Never present it as an official Monzo score.

| Category | Maximum | Visible PDF evidence |
| --- | ---: | --- |
| Team and execution | 34 | Ownership and accountability, organizing work, milestones, removing blockers, engineering excellence, operations, incidents, shipping cadence, and delivery outcomes |
| People | 33 | Inclusive environment, feedback, development goals, coaching, hiring, retention, onboarding, delegation, and performance enablement |
| Leadership | 33 | Healthy team dynamics, conflict resolution, cross-functional relationships, strategic alignment, stakeholder communication, team visibility, and organizational influence |

## Scoring anchors

- `0%` of a category: no visible evidence.
- Approximately `25%`: title or broad claim with little supporting action.
- Approximately `50%`: one or two concrete behaviors but limited scope or outcome.
- Approximately `75%`: several concrete behaviors with clear responsibility and scope.
- `100%`: broad pillar coverage with explicit outcomes and strong evidence.

Score only behaviors visible in the PDF. Do not award points for a Lead or Manager title alone. Treat individual technical execution as leadership only when the bullet shows enablement, coordination, decision systems, or influence on others. Treat absent evidence as a resume gap, not proof the candidate lacks the ability.

## Output

Write exactly one JSON object to the output path assigned by the coordinator:

```json
{
  "evaluator": "leadership",
  "score": 0,
  "confidence": "high|medium|low",
  "summary": "Employer-view summary based only on the PDF.",
  "categories": [
    {"name": "Team and execution", "score": 0, "maximum": 34, "rationale": "Reason"},
    {"name": "People", "score": 0, "maximum": 33, "rationale": "Reason"},
    {"name": "Leadership", "score": 0, "maximum": 33, "rationale": "Reason"}
  ],
  "findings": [
    {
      "severity": "positive|high|medium|low",
      "finding": "Finding",
      "evidence": [{"source": "resume.pdf", "claim": "Visible evidence", "location": "Page 1, section or bullet"}]
    }
  ],
  "gaps": ["Evidence absent from the PDF"],
  "input_boundary": {
    "resume": "resume.pdf",
    "job_description": null,
    "external_context_used": false
  }
}
```

Category maxima must total 100. The total score must equal the category-score sum.
