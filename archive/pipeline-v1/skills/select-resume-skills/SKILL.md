---
name: select-resume-skills
description: Select, group, and order the most relevant evidence-backed technical skills for a target job from one isolated assignment. Use in the resume Writer fan-out for the Technical Skills section; never copy unsupported job keywords or invent proficiency.
---

# Select Resume Skills

Read `references/skills-result-contract.md` completely. Use only
`inputs/assignment.json` and the copied skill.

1. Rank skill groups, technologies, and practices by relevance to the supplied
   criteria. Put the strongest job match first.
2. Author a skill only when approved evidence demonstrates its use. A
   canonical baseline group may instead be preserved exactly. The job
   description alone is never evidence.
3. Retain every group named in `constraints.profile_anchor_groups`. A missing
   job keyword is not evidence that demonstrated profile breadth should
   disappear. For this profile, Backend and Frontend preserve the full-stack
   foundation; Tools and Languages preserve supporting capability and
   eligibility signals.
4. Reorder all groups by offer relevance. When an anchor is secondary, keep it
   concise and place it after the priority groups. Never delete it merely to
   overfit the job description.
5. Prefer three to five evidence-dense groups. Usually keep at most seven items
   per group and about 24 items total. Do not pad, repeat technologies, list
   assumed fundamentals, or turn the section into a stack inventory.
6. Preserve a baseline group only as an exact entry when useful. Author a
   shorter group when approved evidence supports the selected contents.
7. Write only `outbox/result.json`.

Never edit Markdown, invent technologies or proficiency, use Unicode U+2014,
or inspect another Writer task. Run in one fresh top-level task, never a
subagent, fork, or reused task.
