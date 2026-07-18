---
name: resume-context-builder
description: Coordinate deterministic resume evidence retrieval, up to two advisory Terra XHigh scouts, and one fresh top-level gpt-5.6-sol/high Resume Composer using complete active experience and project Markdown. Use to build one tailored resume from a normalized job and baseline YAML while keeping Clean QA separate.
---

# Resume Context Builder

Prepare one bounded Composer sandbox without turning retrieval or scout output
into an evidence gate.

## Required inputs

Require:

- one normalized job description;
- one pinned baseline RenderCV YAML;
- every active Markdown file under `knowledge-base/experience/` and
  `knowledge-base/projects/`.

Copy complete Markdown files, not selected excerpts. Record all input hashes in
one immutable knowledge manifest.

## Active workflow

1. Run deterministic retrieval across the normalized job and active knowledge
   files. Use lexical, technology, alias, and source signals only to prioritize
   reading; retrieval never decides whether evidence is usable.
2. Create at most two advisory assignments: one for `experience` and one for
   `projects`.
3. Run each assignment in a fresh top-level Terra XHigh task, meaning Terra
   with `xhigh` reasoning, and the copied `scout-resume-evidence` skill. Scouts
   return rankings, exact excerpts, gaps, and conflicts only.
4. Validate scout output shape. Missing, empty, or low-ranked scout output does
   not remove a source or block composition.
5. Create one fresh top-level Resume Composer task configured as
   `gpt-5.6-sol/high`. Give it the copied
   `compose-tailored-resume` skill, normalized job, baseline YAML, complete
   active experience and project Markdown, knowledge manifest, and all valid
   advisory scout outputs.
6. Let that single Composer plan, write every mutable section, render the PDF,
   view the rendered page, and revise inside its sandbox before finalizing.
7. Verify the Composer result contract, artifact hashes, provenance coverage,
   and visual-inspection confirmation before promotion.
8. Send only the promoted resume PDF and allowed normalized job description to
   the separate Clean QA pipeline.

## Inactive legacy flow

Do not require an Evidence Reviewer, Claim Risk Critic, include or maybe state,
context-pack approval gate, or per-section Writer fan-out. Those roles may
remain in the repository for history or experiments but are not part of this
active workflow.

Advisory scouts never establish truth. The Composer receives their outputs and
every full source, verifies evidence itself, and owns the complete resume
candidate. Clean QA never receives the knowledge base, retrieval results,
scout output, Composer provenance, or Composer chat context.

## Isolation boundary

Use fresh top-level tasks and copied same-user sandboxes. Never use a subagent,
fork, reused task, parent-chat conclusions, or paths outside declared inputs.
This is logical filesystem isolation, not an OS security boundary.

The Composer never receives QA reports. Clean QA remains a later independent
judgment of the promoted PDF and does not trigger an automated repair pass.
