---
name: review-resume-evidence
description: Review a bounded candidate pool and traceable knowledge-base claims against every atomic job criterion, covering technical, delivery, ownership, product, collaboration, leadership, operations, and mixed evidence. Return criterion-linked evidence findings only; do not draft or edit a resume.
---

# Review Resume Evidence

Produce one bounded evidence packet for all supplied job criteria. Treat this
as relevance and evidence assessment, not resume writing.

## Sandbox inputs

Use only:

- `inputs/candidate-pool.json`
- `inputs/knowledge-base/generated/claims.jsonl`
- `inputs/<source_file>` for source paths advertised by ranked candidates
- `manifest.json` for immutable hashes and the declared output

Confirm that the candidate pool claim-index hash equals the copied index hash
recorded in `manifest.json`.

## Workflow

1. Review every atomic criterion, including technical, experience, and mixed
   criteria.
2. Inspect at most five ranked claim candidates per criterion. Retrieval scores
   narrow context but never establish truth.
3. Inspect each candidate's copied source, contribution boundaries, metrics,
   caveats, conflicts, evidence gaps, production status, and adoption claims.
4. Restore enough surrounding Markdown to preserve meaning. Select one or more
   substantial exact excerpts, normally a complete relevant section or a
   coherent group of adjacent paragraphs, rather than isolated sentences.
5. Give every excerpt an inclusive line range. Copy the text exactly, including
   headings and list items. Attach any claims from that same source that the
   excerpt substantiates; an excerpt may have no claim when canonical narrative
   evidence is specific enough to audit directly.
6. Emit each `(criterion_id, evidence_id)` use at most once.
7. Write exactly one schema-version 3 packet to the declared outbox path with
   `role: evidence-reviewer`.

Use this packet shape:

```json
{
  "schema_version": 3,
  "role": "evidence-reviewer",
  "findings": [
    {
      "finding_id": "finding-unique-id",
      "criterion_id": "criterion-id",
      "status": "strong|partial|missing|conflict",
      "evidence_strength": "high|medium|low|none",
      "evidence_units": [
        {
          "evidence_id": "evidence-unique-id",
          "source_file": "knowledge-base/experience/example.md",
          "line_start": 20,
          "line_end": 42,
          "excerpt": "## Complete relevant section\n\nExact source text.",
          "claim_ids": []
        }
      ],
      "reason": "Evidence assessment.",
      "caveats": [],
      "follow_up_questions": [],
      "resume_safe": false
    }
  ]
}
```

## Assessment rules

- `strong`: confirmed resume-safe claims directly demonstrate the criterion.
- `partial`: evidence is narrower, adjacent, or explicitly partial.
- `missing`: no supported source demonstrates the criterion; use no evidence units,
  `none` strength, and `resume_safe: false`.
- `conflict`: the proposed use is unsafe, contradicted, confidential,
  unverified, or broader than its source.
- Do not turn individual contribution into team ownership or management.
- Do not infer impact, adoption, scale, causality, production status, metrics,
  or technologies from activity or keyword overlap.
- Preserve unsupported portions in caveats and ask only material questions.

## Hard boundaries

- Read only the copied skill, manifest, and `inputs/` snapshot.
- Write only the declared outbox file.
- Do not read the repository, another sandbox, another task, or parent chat.
- Do not draft resume content. Narrative candidates may become evidence only as
  exact, sufficiently contextual source excerpts that the Critic can audit.

Return valid JSON only in the requested artifact.
