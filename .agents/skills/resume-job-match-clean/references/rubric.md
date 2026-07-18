# Job-match resume rubric

## Provenance and metrics

This is a project-local rubric designed by Codex. It is not an official ATS, Ashby, or employer score.

The report contains two independent metrics:

1. **Local weighted Job Match score**: the 0-100 category score below.
2. **Ashby-style observable proxy**: the percentage of scoreable atomic criteria visibly met by the PDF. It mimics the public `meets / does not meet / undecided` review model only; it does not reproduce an employer's hidden criteria, weights, ranking, auto-reject configuration, or AI behavior.

Never average or substitute these metrics.

| Category | Maximum | Comparison |
| --- | ---: | --- |
| Mandatory requirements | 30 | Explicit must-have qualifications supported by the PDF |
| Core responsibilities | 25 | Evidence of performing the primary work |
| Technology and domain | 20 | Required stack, methods, platforms, and domain experience |
| Seniority and scope | 15 | Years, autonomy, complexity, ownership, and team expectations |
| Evidence quality | 10 | Specific proof instead of unsupported keywords |

Category maxima must total 100. The total weighted score must equal the category-score sum. Do not penalize a preferred criterion as if it were mandatory.

## Decision rules

- Hard gate: include only a visible, explicit eligibility condition. A required field or unanswered question alone is not a hard gate. Use `does-not-meet` only for a visible contradiction, `needs-answer` when the PDF cannot supply the eligibility fact, and `uncertain` when the public wording is incomplete.
- Atomic criteria: one fact per criterion. Use the supplied compiler quality flags; if a legacy criterion is compound, split it. Use `meets` for explicit or technically equivalent evidence, `does-not-meet` for absent or contradictory visible evidence, and `undecided` for partial or ambiguous evidence.
- Proxy inclusion: exclude `unclear` or untestable criteria by setting `included_in_proxy` to false. Include eligibility, must-have, preferred, and responsibility criteria when objectively testable.
- Exact evidence: quote or tightly paraphrase the visible claim and cite its location. Empty resume evidence is valid for gaps.
- Search coverage: the clean evaluator does not simulate ATS full-text search. A deterministic coordinator artifact handles local Matches/Contains/Equals/Similar proxies separately.
- Parsing risk: inspect visible text extraction, section clarity, chronology, and links. Do not claim an employer-specific parser result.
- Consistency risk: inspect internal PDF consistency. Mark comparisons with LinkedIn or unfilled application answers `unknown`.
- Questions needed: include required fields, facts needed to resolve an explicit gate, material undecided criteria, and external consistency rows. `blocks_application` means the visible form requires an answer, not that a hidden reject rule exists.
- Out of scope: hidden ATS configuration, fraud detection, ranking weights, internal AI prompts, and employer decisions.

## Ashby-style observable proxy formula

Count only rows where `included_in_proxy` is true:

```text
criteria_met_percentage = round(100 * meets / total, 1)
total = meets + does_not_meet + undecided
```

Use `null` when `total` is zero. `official_ashby_score` must be false.

## Output

Write exactly one JSON object:

```json
{
  "schema_version": "2.0",
  "evaluator": "job-match",
  "score": 0,
  "confidence": "high|medium|low",
  "summary": "Employer-view fit summary based only on the two supplied artifacts.",
  "categories": [
    {"name": "Mandatory requirements", "score": 0, "maximum": 30, "rationale": "Reason"},
    {"name": "Core responsibilities", "score": 0, "maximum": 25, "rationale": "Reason"},
    {"name": "Technology and domain", "score": 0, "maximum": 20, "rationale": "Reason"},
    {"name": "Seniority and scope", "score": 0, "maximum": 15, "rationale": "Reason"},
    {"name": "Evidence quality", "score": 0, "maximum": 10, "rationale": "Reason"}
  ],
  "job_match_matrix": {
    "hard_gates": [
      {
        "criterion": "Visible eligibility condition",
        "gate_type": "explicit-eligibility",
        "status": "meets|does-not-meet|needs-answer|uncertain",
        "job_evidence": [{"source": "job-description.md", "claim": "Visible wording", "location": "Heading or form field"}],
        "resume_evidence": [{"source": "resume.pdf", "claim": "Visible evidence", "location": "Page 1, section"}],
        "rationale": "Decision reason",
        "action": "Next action"
      }
    ],
    "criteria": [
      {
        "id": "must-have-1",
        "kind": "eligibility|must-have|preferred|responsibility|unclear",
        "criterion": "One independently testable criterion",
        "quality": {
          "standalone": true,
          "singular": true,
          "clear": true,
          "specific": true,
          "objectively_verifiable": true,
          "bias_risk": "none|possible|high",
          "notes": []
        },
        "included_in_proxy": true,
        "status": "meets|does-not-meet|undecided",
        "job_evidence": [{"source": "job-description.md", "claim": "Visible wording", "location": "Atomic evaluation criteria"}],
        "resume_evidence": [],
        "rationale": "Decision reason",
        "action": "Truthful resume or application action"
      }
    ],
    "ashby_style_proxy": {
      "label": "Ashby-style observable proxy",
      "official_ashby_score": false,
      "formula": "meets / total observable atomic criteria",
      "counts": {"meets": 0, "does_not_meet": 0, "undecided": 0, "total": 0},
      "criteria_met_percentage": null
    },
    "parsing_risks": [
      {
        "check": "Parsing check",
        "status": "pass|risk|unknown",
        "evidence": [{"source": "resume.pdf", "claim": "Observed result", "location": "Page 1"}],
        "action": "Mitigation or none"
      }
    ],
    "consistency_risks": [
      {
        "field": "Dates, titles, education, LinkedIn, or application answer",
        "status": "consistent|conflict|unknown",
        "resume_evidence": [],
        "job_evidence": [],
        "action": "Verification or correction"
      }
    ],
    "questions_needed": [
      {
        "question": "Candidate or application question",
        "reason": "Why the artifacts cannot answer it",
        "source": "Form field or unresolved criterion",
        "blocks_application": true,
        "explicit_eligibility_gate": false,
        "potential_auto_reject": "unknown"
      }
    ]
  },
  "findings": [
    {
      "severity": "positive|high|medium|low",
      "finding": "Material finding",
      "evidence": [{"source": "resume.pdf|job-description.md", "claim": "Visible evidence", "location": "Page or section"}]
    }
  ],
  "gaps": ["Evidence absent from the PDF"],
  "input_boundary": {
    "resume": "resume.pdf",
    "job_description": "job-description.md",
    "external_context_used": false
  }
}
```
