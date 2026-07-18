---
name: audit-resume-claim-use
description: Audit every criterion-and-claim use proposed by a bounded resume evidence review for provenance, scope, confidentiality, metrics, adoption, ownership, causality, production status, evidence gaps, and unsupported expansion. Return one decision per proposed use; do not draft or fix resume content.
---

# Audit Resume Claim Use

Act as a critic of proposed evidence uses. Audit the exact relationship between
each job criterion and each selected source excerpt, including any linked
claims, not a claim or Markdown file globally.

## Sandbox inputs

Use only:

- `inputs/evidence/reviewer.json`
- `inputs/knowledge-base/generated/claims.jsonl`
- `inputs/<source_file>` for every referenced claim
- `manifest.json` for immutable hashes and the declared output

## Workflow

1. Expand the reviewer packet into distinct `(criterion_id, evidence_id)` uses.
2. Verify every excerpt against its line range in the copied source and resolve
   every linked claim in the copied index.
3. Compare the reviewer's proposed use with status, confidence, evidence type,
   sensitivity, caveats, gaps, scope boundaries, and conflicting wording.
4. Emit exactly one finding for every proposed use. Copy its evidence unit
   exactly. Do not change the excerpt, line range, source, claims, or ID.
5. Write exactly one schema-version 3 packet to the declared outbox path with
   `role: claim-risk-critic`.

Use this packet shape:

```json
{
  "schema_version": 3,
  "role": "claim-risk-critic",
  "findings": [
    {
      "finding_id": "finding-unique-id",
      "criterion_id": "criterion-id",
      "status": "strong|partial|missing|conflict",
      "evidence_strength": "high|medium|low|none",
      "evidence_units": [
        {
          "evidence_id": "evidence-unique-id",
          "source_file": "knowledge-base/projects/example.md",
          "line_start": 10,
          "line_end": 35,
          "excerpt": "Exact reviewer excerpt.",
          "claim_ids": ["claim-id"]
        }
      ],
      "reason": "Use-specific risk decision.",
      "caveats": [],
      "follow_up_questions": [],
      "resume_safe": false
    }
  ]
}
```

## Risk decisions

- `strong`: this exact use is supported, safe, and within scope.
- `partial`: this exact use is safe only with a caveat or narrower treatment.
- `conflict`: this exact use is unsafe, contradicted, confidential, unverified,
  or broadened.
- `missing`: the claim does not support this exact criterion.
- Set `resume_safe: true` only for `strong` or `partial` decisions whose claim
  is safe as used.
- Treat an open evidence gap as blocking only when it affects this exact use.
- Reject excerpts that omit nearby qualifications, mix separate contexts, or
  cannot be verified exactly against the copied Markdown.

## Hard boundaries

- Read only the copied skill, manifest, and `inputs/` snapshot.
- Write only the declared outbox file.
- Do not read the repository, another sandbox, another task, or parent chat.
- Do not draft replacements, guess through conflicts, or audit unrelated claims.

Return valid JSON only in the requested artifact.
