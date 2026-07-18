# Isolated project Writer result

Copy the prompt's assignment hash and task ID. Write:

```json
{
  "schema_version": 1,
  "task_id": "projects",
  "assignment_sha256": "<supplied hash>",
  "status": "ready",
  "content": {
    "projects": [
      {
        "mode": "authored",
        "project_id": "project-example",
        "label": "Example Project",
        "details": "Built a supported project outcome.",
        "supporting_evidence_ids": ["evidence-example"]
      }
    ]
  },
  "blocking_reasons": [],
  "questions": []
}
```

A preserved project is exactly `{"mode":"preserve","source_index":0}`.
Respect `constraints.maximum_entries`. Every authored entry must cite include
cards whose `source_metadata.id` equals its `project_id`. Use `needs-evidence`
with null content only when no safe project selection can be produced.
