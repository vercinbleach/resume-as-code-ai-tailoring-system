# Technical resume rubric

This is HackerRank-inspired, not an official HackerRank score.

## Provenance

The four categories and their weights are adapted from HackerRank/InterviewStreet's public `hiring-agent` prompt:

<https://github.com/interviewstreet/hiring-agent/blob/main/prompts/templates/resume_evaluation_criteria.jinja>

This project removes the original prompt's GitHub/blog enrichment, bonus points, deductions, and intern-specific framing. The evaluator uses only the final PDF, so its result is not directly comparable to the upstream agent.

| Category | Maximum | Visible PDF evidence |
| --- | ---: | --- |
| Open-source contribution | 35 | Named upstream work, substantive contribution, merge/review/adoption, or community impact |
| Self-directed projects | 30 | Original projects with architecture, implementation depth, validation, users, or outcomes |
| Production engineering | 25 | Shipped systems, integrations, operations, scale, reliability, or business impact |
| Technical skills | 10 | Skills demonstrated inside experience or projects, not merely listed |

## Anchors

- `0`: no visible PDF evidence.
- Approximately one-third: named activity with limited depth or proof.
- Approximately two-thirds: multiple concrete examples with implementation evidence.
- Full credit: sustained high-impact evidence with clear ownership and validation.

Do not award open-source points for a GitHub profile link alone. Do not treat tutorials, school exercises, hackathon prototypes, or skill lists as production. Do not browse public profiles.

## Output

Write exactly one JSON object to the output path assigned by the coordinator:

```json
{
  "evaluator": "technical",
  "score": 0,
  "confidence": "high|medium|low",
  "summary": "Employer-view summary based only on the PDF.",
  "categories": [
    {"name": "Category", "score": 0, "maximum": 0, "rationale": "Reason"}
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
