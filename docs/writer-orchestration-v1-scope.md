# Resume Composer: approved active scope

Status: approved simplification of Writer orchestration on 2026-07-18.

## Goal

Produce one coherent, job-specific, one-page resume through one global semantic
composition task. Preserve the canonical resume and knowledge-base Markdown,
avoid section-local optimization, and keep Clean QA isolated and terminal.

## Advisory scout wave

- Advisory scouts run concurrently in fresh top-level Codex tasks with
  `gpt-5.6-terra` and reasoning `xhigh`.
- Scouts inspect only their pinned inputs and return bounded reports about
  relevance, evidence, conflicts, gaps, duplication, or representation risk.
- Scout reports are advisory. No individual scout approves, rejects, writes, or
  edits the resume.
- Scouts never read one another's outputs, parent-chat context, prior reports,
  generated resumes, or Clean QA results.
- The coordinator waits for the complete scout wave before creating the
  Composer task.

Risk analysis may appear as advisory scout guidance, but it is never a separate
mandatory semantic gate.

## Resume Composer task

Run exactly one fresh top-level Resume Composer task with `gpt-5.6-sol` and
reasoning `high`. Never use a subagent, fork, reused task, multiple independent
resume-writing tasks, or a second semantic merge task.

The Composer receives read-only copies of:

- the canonical RenderCV baseline;
- the normalized job description and observable application requirements;
- every completed advisory scout report;
- every complete Markdown file under `knowledge-base/experience/`;
- every complete Markdown file under `knowledge-base/projects/`.

The Composer does not receive raw browser state, hidden ATS assumptions, Clean
QA reports, previous tailored resumes, historical CVs, generated claim indexes,
or another task's workspace.

## Global composition responsibilities

The Composer plans the complete document before writing and owns all semantic
tradeoffs across sections. It must:

- preserve truthful identity, contact, education, employer, position, date, and
  chronology metadata;
- choose and write experience bullets from supported evidence;
- choose a complementary portfolio of projects rather than independently
  ranking isolated project entries;
- preserve at least the baseline's total Experience bullet count while
  distributing bullets globally by relevance, with no fixed per-role quota;
- avoid visually bloated adjacent roles or thin standalone employer blocks when
  supported evidence and the one-page layout allow a balanced allocation;
- preserve user-approved acquisition grouping, punctuation, and exact role
  titles from the canonical baseline, using one parseable title per role rather
  than a compound promotion title;
- keep at least two complementary projects when the baseline contains two or
  more;
- decide which defensible links merit space and verify that displayed labels
  and targets agree;
- distinguish upstream merge status, downstream fork adoption, and verified
  production use for open-source evidence;
- select and group technical skills that are demonstrated by the resume and
  knowledge base;
- avoid repeating one accomplishment, metric, system, or claim across roles and
  projects;
- ensure system and integration bullets state the supported result or capability
  rather than ending at a component inventory;
- avoid repetitive generic openers such as `Built` when more precise supported
  verbs describe the action, without varying verbs merely for style;
- lead with the agentic system, multi-agent workflow, or harness when it is the
  accomplishment and treat tools such as Codex as implementation details;
- describe model integrations as `AI APIs` or `AI SDKs` instead of naming a
  specific foundation model or version in resume-facing wording;
- prefer capability wording over vendor names when the vendor does not add
  relevant evidence for the target role;
- preserve supported differentiating terms such as `Custom Agent Harnesses`
  when relevant to the target role;
- represent executive or Board interaction only with an exact relationship and
  a supported decision, alignment, delivery, or organizational outcome;
- prefer a verified formal collective name over a noisy list of overlapping
  executive titles when the collective body is the relevant collaborator;
- keep coaching or people development separate from executive prioritization
  when they are distinct achievements, placing executive collaboration with
  the process, program, or delivery decision it shaped;
- preserve accurate ownership and distinguish individual, team, technical-lead,
  and people-management scope;
- preserve supported management actions such as organizing, prioritizing,
  assigning, and tracking team delivery work;
- surface verified production reliability evidence, such as failures,
  incidents, recovery, latency, throughput, availability, or cost, when the
  supplied sources support it;
- never invent metrics, technologies, causality, adoption, production status,
  proficiency, or job-keyword evidence;
- preserve the Jake-style order and one-page constraint;
- never use strong emphasis inside resume bullets or Unicode U+2014.

Advisory reports may guide attention, but the Composer must verify every final
statement against the supplied baseline or complete Markdown sources.

## Render and visual inspection

The Composer writes the job-specific RenderCV source in its private workspace,
renders the PDF, and visually inspects the actual one-page candidate. It checks
at minimum:

- clipping, overflow, collisions, unreadable density, and excessive whitespace;
- header spacing, section hierarchy, alignment, dates, links, and bullet wraps;
- duplicate content across Experience and Projects;
- repetitive bullet openings, activity-only system descriptions, and lopsided
  bullet density across adjacent roles;
- whether the most relevant evidence is visible at normal reading size.
- whether later section titles have readable separation instead of remaining
  crowded while avoidable whitespace sits at the bottom of the page.

The Composer may revise and rerender inside the same task. It does not invoke
Clean QA and does not read Clean QA output.

## Coordinator validation and promotion

The coordinator does not rewrite semantic content. It:

1. Verifies the task identity, declared model and reasoning level, input hashes,
   source drift, and expected artifact inventory.
2. Confirms the canonical baseline and knowledge-base Markdown remain unchanged.
3. Runs deterministic RenderCV and PDF checks, including one-page, text
   extraction, required section order, links, file size, and encryption status.
4. Rejects incomplete, invalid, or internally inconsistent bundles without
   partial promotion.
5. Promotes the complete Composer bundle atomically into the job session.

The promoted bundle contains the job-specific RenderCV source, final PDF,
deterministic checks, and a promotion receipt. The canonical baseline is never
overwritten.

## Clean QA boundary

Clean QA receives only the promoted PDF and the normalized job description
allowed by each evaluator contract. It never receives scout reports, Composer
inputs, knowledge-base Markdown, Composer workspace, earlier CVs, or prior QA
reports.

Clean QA is terminal. No QA result returns to the Composer and no automatic
second composition pass is part of this scope.

## Legacy boundary

Legacy files from prior multi-stage or multi-writer designs may remain for
traceability but must not be invoked by an active run or described as current
architecture.

## Acceptance criteria

1. Every scout is a fresh top-level `gpt-5.6-terra` task with reasoning `xhigh`.
2. Exactly one fresh top-level Resume Composer uses `gpt-5.6-sol` with reasoning
   `high`.
3. The Composer receives the complete baseline, normalized job, scout reports,
   and complete experience and project Markdown snapshots.
4. The final resume is composed globally, with duplication checked across
   sections.
5. Global density preserves the baseline's total Experience bullet count and
   at least two projects when available.
6. The Composer renders and visually inspects its own PDF before handoff.
7. The coordinator validates and promotes only a complete bundle.
8. The canonical baseline and knowledge-base Markdown remain unchanged.
9. Clean QA remains isolated and terminal.
10. No application is filled or submitted.

Any further expansion requires explicit user approval.
