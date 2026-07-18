# Resume tailoring pipeline

The complete system diagrams are in `../docs/system-architecture-diagrams.md`.
The active implementation boundaries are in
`../docs/lightweight-sandbox-v1-scope.md` and
`../docs/writer-orchestration-v1-scope.md`.

The active design uses advisory scouts followed by one global Resume Composer.
The coordinator is the only component allowed to promote semantic output into
durable session state. Clean QA remains a separate terminal pipeline.

## Active flow

1. Job Intake captures and normalizes the visible job and Apply content without
   entering candidate data or submitting an application.
2. The coordinator snapshots the normalized job, canonical resume baseline,
   and every complete Markdown file under `knowledge-base/experience/` and
   `knowledge-base/projects/`.
3. Advisory scouts run concurrently in fresh top-level Codex tasks using
   `gpt-5.6-terra` with reasoning `xhigh`.
4. Each scout returns a bounded advisory report about relevance, evidence,
   gaps, conflicts, duplication risk, or representation risk. Scout output is
   guidance, not a mandatory approval gate and never becomes resume text by
   itself.
5. One fresh top-level Resume Composer task runs with `gpt-5.6-sol` and reasoning
   `high`. It receives the baseline, normalized job, all scout reports, and the
   complete experience and project Markdown snapshots.
6. The Composer plans the resume globally before writing. It selects and writes
   experience bullets, projects, links, and technical skills while controlling
   repetition, factual attribution, density, section balance, and one-page fit.
   It preserves at least the baseline's total Experience bullet density and at
   least two projects when the baseline has two or more, without imposing a
   fixed bullet quota per employer. It also preserves user-approved acquisition
   grouping and punctuation, plus one exact parseable title per role from the
   baseline.
7. The Composer writes the job-specific RenderCV source, renders the PDF, and
   visually inspects its own candidate. It iterates only inside that one task
   until the candidate satisfies its composition contract or reports a blocker.
8. The coordinator verifies source hashes, expected artifacts, locked factual
   metadata, PDF preflight, one-page layout, and promotion invariants. Only a
   complete valid bundle becomes durable session state.
9. Clean QA receives only the promoted PDF and, where allowed, the normalized
   job description. It never receives knowledge-base Markdown, scout reports,
   Composer context, or prior semantic reports.
10. Clean QA is terminal. Its report does not return to the Composer and no
    automatic second composition pass runs.

## Composer responsibilities

The Resume Composer owns the complete employer-facing document, not isolated
sections. It must:

- preserve truthful identity, education, employer, role, date, and chronology
  metadata;
- use the full Markdown evidence without inventing metrics, technologies,
  ownership, causality, adoption, production status, or proficiency;
- avoid repeating the same achievement across experience and projects;
- choose projects as a portfolio that adds job-relevant coverage;
- keep at least two complementary projects when the baseline offers them;
- preserve the baseline's total Experience bullet count while allocating it
  globally by relevance;
- avoid thin standalone employer blocks and visibly lopsided adjacent roles
  when supported evidence and layout space allow a balanced result;
- make system and integration bullets state a supported effect or capability,
  not only the components used;
- avoid repetitive generic openers when a more precise evidence-backed verb
  exists, without changing verbs merely for style;
- lead with the agentic system, multi-agent workflow, or harness and treat tools
  such as Codex as implementation details;
- preserve supported differentiating terms such as `Custom Agent Harnesses`;
- describe executive or Board interaction only through the exact relationship,
  action, and supported decision or outcome;
- keep coaching separate from executive prioritization when they are distinct,
  and place executive collaboration with the process or delivery it shaped;
- decide which defensible project or profile links earn space;
- keep technical skills consistent with demonstrated experience and projects;
- keep the Jake-style section order and one-page constraint;
- avoid strong emphasis inside resume bullets and never use Unicode U+2014;
- render and visually inspect the PDF before handing it to the coordinator.

## Post-pipeline review corrections

A localized user review comment is not a new tailoring run. Change only the
named content, rerender and inspect the one-page PDF, and run deterministic PDF
checks. Start fresh semantic QA only when the user explicitly requests it.

## Legacy implementation boundary

Legacy scripts, contracts, and generated sessions from earlier multi-stage or
multi-writer orchestration may remain on disk for traceability. Current runs
must not invoke them, and they are not the source of truth for the active
architecture.

## Isolation model

Every semantic task is a fresh top-level Codex task, never a subagent, fork, or
reused task. Scouts cannot read one another's outputs. The Composer receives the
complete approved input snapshot and all finished advisory reports only after
the scout wave completes.

This is lightweight same-user logical isolation. It protects against accidental
context sharing and unvalidated durable writes through copied read-only inputs,
private task workspaces, hashes, validation, atomic promotion, and cleanup after
success. It is not an OS security boundary and does not add containers, virtual
machines, separate identities, firewall enforcement, warm sandboxes, telemetry,
JSONL lifecycle logs, schedulers, or automatic retries.

## Durable versus ephemeral state

- `.sandbox/tailoring/<session-id>/scouts/<task-id>/`: private advisory scout
  workspaces, removed after their reports are captured and the Composer input is
  pinned.
- `.sandbox/tailoring/<session-id>/composer/`: private Resume Composer workspace,
  removed only after successful promotion.
- `tailoring/sessions/<session-id>/inputs/`: immutable job, baseline, and full
  Markdown snapshots.
- `tailoring/sessions/<session-id>/scouts/`: validated advisory reports.
- `tailoring/sessions/<session-id>/composer/`: promoted job-specific RenderCV
  source, PDF, checks, and receipt.
- `tailoring/sessions/<session-id>/manifest.json`: task identities, models,
  hashes, promotion state, and cleanup receipt.

Knowledge-base Markdown and scout reports never become Clean QA inputs. The
system does not fill or submit applications.
