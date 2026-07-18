---
name: select-resume-projects
description: Select and write the most job-relevant evidence-backed resume projects from one isolated assignment containing baseline projects and approved source excerpts. Use in the resume Writer fan-out for the Projects section; never edit the knowledge base or invent facts.
---

# Select Resume Projects

Read `references/project-result-contract.md` completely. Use only
`inputs/assignment.json` and the copied skill.

1. Compare approved project evidence with the supplied job criteria.
2. Select projects that best demonstrate the requirements and are defensible.
3. Author concise labels and details only from cards belonging to that same
   `project_id`; several substantial excerpts may support one entry.
4. Preserve a baseline project only as an exact entry when rewriting lacks
   approved evidence.
5. Write only `outbox/result.json`.

Never edit Markdown, add requested technology without evidence, turn a
prototype into production, inflate ownership, invent adoption or metrics, use
Unicode U+2014, or inspect another Writer task. Run in one fresh top-level task,
never a subagent, fork, or reused task.
