# Isolated technical-skills Writer result

Copy the prompt's assignment hash and task ID. Write:

```json
{
  "schema_version": 1,
  "task_id": "technical-skills",
  "assignment_sha256": "<supplied hash>",
  "status": "ready",
  "content": {
    "technical_skills": [
      {
        "mode": "authored",
        "skill_group_id": "backend",
        "label": "Backend",
        "details": "Python, FastAPI, PostgreSQL",
        "supporting_evidence_ids": ["evidence-example"]
      }
    ]
  },
  "blocking_reasons": [],
  "questions": []
}
```

A preserved group is exactly `{"mode":"preserve","source_index":0}`. Respect
`constraints.maximum_entries` and retain every label listed in
`constraints.profile_anchor_groups`, either preserved or authored. The array
order is the resume order: lead with the groups most relevant to the offer and
place secondary anchors later, compacted rather than removed.

For the current full-stack profile, the assignment anchors Backend, Frontend,
Tools, and Languages. This does not fix their order or require preserving every
baseline item inside an authored group.

Treat `constraints.density_guidance` as a brevity target, not a reason to pad
the section. Every authored group must cite include evidence cards. Use
`needs-evidence` with null content only when no safe skills section can be
produced.
