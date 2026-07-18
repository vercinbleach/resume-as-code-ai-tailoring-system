---
name: scout-resume-evidence
description: Rank and excerpt relevant experience or project evidence from one bounded full-Markdown assignment for a normalized job. Use only as advisory preprocessing before the Resume Composer; never gate evidence, emit include or maybe states, draft resume content, or replace the Composer's full-source reading.
---

# Advisory Resume Evidence Scout

Run this skill in a fresh top-level Terra XHigh task, meaning Terra with
`xhigh` reasoning. Accept one assignment whose `domain` is exactly
`experience` or `projects`.

## Workflow

1. Read only the copied assignment, normalized job, and complete Markdown files
   declared by the assignment.
2. Rank sources by how directly they may help the Composer address the job.
3. Copy exact, contextual excerpts with inclusive line ranges. Do not rewrite
   them as resume claims.
4. Flag source conflicts, caveats, missing evidence, and likely duplication.
5. Write only `outbox/result.json` with exactly this compact shape:

```json
{
  "schema_version": 1,
  "assignment_id": "experience",
  "domain": "experience",
  "ranked_sources": [
    {
      "rank": 1,
      "source_file": "knowledge-base/experience/example.md",
      "reason": "Direct evidence for a core responsibility.",
      "excerpts": [
        {"line_start": 10, "line_end": 18, "text": "Exact source text."}
      ],
      "caveats": []
    }
  ],
  "gaps": [],
  "conflicts": []
}
```

Keep at most eight ranked sources and three excerpts per source. Ranks are
unique consecutive integers starting at one. An empty ranking is valid.

Never emit `status`, `include`, `maybe`, `exclude`, acceptance decisions,
scores presented as truth, or instructions to suppress a full source. The
Composer receives every complete active Markdown file regardless of ranking.
Never draft or edit YAML, bullets, projects, skills, or PDF artifacts. Never
use Unicode U+2014.
