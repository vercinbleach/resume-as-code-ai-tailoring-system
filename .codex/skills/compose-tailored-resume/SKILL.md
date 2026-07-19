---
name: compose-tailored-resume
description: Compose, render, and visually inspect one job-tailored RenderCV resume from a normalized job, a baseline YAML, complete active experience and project Markdown snapshots, and optional advisory scout outputs. Use for the single top-level gpt-5.6-sol/high Resume Composer task after retrieval and scouting, before separate Clean QA.
---

# Tailored Resume Composer

Read `references/result-contract.md` completely before writing an artifact.

Run this skill in exactly one fresh top-level Codex task configured as
`gpt-5.6-sol/high`, meaning `gpt-5.6-sol` with `high` reasoning. Never use a
subagent, fork, reused task, or section-level Writer fan-out.

## Input boundary

Read only the copied sandbox inputs:

- one normalized job description;
- one pinned baseline RenderCV YAML;
- every complete active Markdown file copied from
  `knowledge-base/experience/` and `knowledge-base/projects/`;
- zero, one, or two advisory `scout-resume-evidence` results;
- the sandbox manifest and this copied skill.

Do not read the raw job intake, browser, parent chat, prior CVs, QA reports,
generated claim indexes, or any repository path outside the sandbox.

Scout rankings and excerpts are navigation hints only. They are never evidence
gates and never replace reading every supplied Markdown file in full. Verify
each fact against the complete source before using it.

## Mutable and locked content

Write all mutable resume content in one pass:

- Experience highlights;
- Projects & Open Source selection, order, labels, and details;
- Technical Skills selection, grouping, order, and details.

Keep identity, contact data, Education, experience employers, titles, dates,
locations, chronology, design, locale, and RenderCV settings equal to the
baseline. Never modify the canonical source outside the sandbox.

Treat a user-approved acquisition grouping, its punctuation, and each exact
role title in the baseline as locked. Keep one ATS-parseable title per role;
do not encode progression by joining titles with `to`, a slash, or an arrow.
Do not split a consolidated employment line into a thin standalone employer
block merely to preserve one less-relevant project.

Keep Backend and Frontend as core skill groups. Keep Tools and Languages as
secondary groups that may be compacted and reordered. For an AI role, lead
with `AI & Agents` when evidence supports it; keep Data & Automation separate
and optional. Prefer three to five dense groups without padding.
Preserve supported, role-relevant technical terms that distinguish the profile,
including `Custom Agent Harnesses`; do not replace them with generic labels.

## Workflow

1. Verify the input inventory and hashes from the manifest.
2. Read the normalized job and baseline, then use scout outputs to orient the
   search without accepting their conclusions.
3. Read every supplied experience and project Markdown file completely.
4. Plan the strongest truthful one-page narrative in private `work/` state.
5. Edit a sandbox copy of the baseline. Use only source-supported facts,
   metrics, ownership, technologies, and outcomes.
   Keep at least two complementary projects when the baseline offers two or
   more, and do not reduce the total Experience bullet count below the baseline.
   Allocate those bullets globally by relevance instead of applying a fixed
   per-employer range. Avoid visibly bloated adjacent roles or thin employer
   blocks when the evidence and one-page space support a more balanced result.
6. Maintain provenance while drafting. Every final experience bullet, project,
   and listed skill needs one contract entry.
7. Render the candidate PDF inside the sandbox. Render its latest page to an
   image and actually inspect it before finalizing.
8. Iterate within this same task until the PDF is one page, legible, balanced,
   unclipped, and free of overlaps. Re-render and re-inspect after every change.
   Do not crowd later section titles against the preceding content while unused
   space remains at the bottom; preserve the baseline section-title spacing.
9. Write only the three declared outbox files when ready. If truthful content
   cannot be completed, return `needs-evidence` without YAML or PDF artifacts.

## Content rules

- Prefer evidence density and role relevance over keyword coverage.
- Never invent, estimate, combine, or strengthen unsupported facts.
- Make each system or integration bullet state a supported result, capability,
  or operational change rather than stopping at a list of components.
- Avoid repetitive generic openers such as `Built` across nearby bullets when
  more precise evidence-backed verbs describe the work. Never vary verbs merely
  for style or use them to overstate ownership.
- Name an agentic system, multi-agent workflow, or harness before the vendor or
  coding tool when the system is the accomplishment; describe tools such as
  Codex as implementation details.
- For production systems, surface verified reliability evidence when available,
  such as failures, incidents, recovery, latency, throughput, availability, or
  cost. When the sources do not provide it, preserve the evidence gap instead
  of manufacturing a reliability claim or metric.
- Preserve ambiguity and caveats when the sources conflict; ask a blocking
  question instead of guessing.
- Do not use job text as evidence about the candidate.
- Distinguish individual contribution, collaboration, technical leadership,
  and people management.
- Keep one achievement per bullet. Do not combine coaching or people
  development with executive prioritization when they describe separate work;
  attach executive collaboration to the process or delivery decision it shaped.
- State executive or Board interaction only when the sources distinguish formal
  reporting, direct collaboration, or presentation audience and connect it to a
  supported decision, alignment, delivery, or organizational outcome.
- Do not repeat the same accomplishment or evidence across Experience and
  Projects. Allocate it to the section where it adds the most value.
- Use a public repository, project, event, or contribution link when the
  copied source provides one; never invent or expose an internal URL.
- Use `AI APIs` or `AI SDKs` instead of specific foundation-model names or
  versions in resume-facing wording unless the user explicitly requires one.
- Prefer capability wording over vendor names when the vendor is not relevant
  to the target role, while preserving the exact vendor in source evidence.
- For open-source evidence, distinguish upstream merge status, downstream fork
  adoption, and verified production use; do not weaken production deployment
  into generic adoption or imply an upstream merge that did not occur.
- Never use bold markup inside an experience bullet.
- Never use Unicode U+2014.
- Do not fill or submit an application.

## Final boundary

The Composer may inspect and revise its own rendered PDF before finalization.
It never receives Clean QA output. Clean QA starts later in separate fresh
tasks and receives only the promoted PDF plus its allowed normalized job input.
