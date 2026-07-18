# Documentation index

## Canonical current documentation

- `system-architecture-diagrams.md`: complete active architecture and access
  boundaries. This is the canonical architecture document.
- `lightweight-sandbox-v1-scope.md`: binding isolation, promotion, cleanup, and
  change-control boundaries for same-user task workspaces.
- `writer-orchestration-v1-scope.md`: binding scope for advisory scouts and the
  single global Resume Composer.
- `../tailoring/README.md`: active tailoring flow, model assignments, Composer
  responsibilities, durable state, and inactive legacy roles.
- `../qa/README.md`: Clean QA v7, private evaluator sandboxes, batch promotion,
  deterministic checks, and reporting limits.
- `../knowledge-base/README.md`: canonical full Markdown and optional structured
  claim support.
- `../knowledge-base/contracts/claim-contract.md`: atomic claim and evidence
  rules for knowledge maintenance.

## Decisions and research

- `research/resume-as-code.md`: accepted renderer decision and current Composer
  boundary.
- `research/resume-bullet-writer-skill.md`: external writing guidance retained
  inside the global Composer.

## Historical material

Historical CVs and external-score snapshots belong under `../archive/`. They
may explain an earlier decision but are never current architecture or evidence
for a clean evaluator. Legacy scripts and generated sessions may document prior
orchestration, but active behavior is defined only by the canonical files above.

## Maintenance rule

Update the canonical document that owns a behavior. Do not create a second
architecture overview, duplicate commands, or present generated session output
as current project documentation. When a decision changes, update every active
Markdown that describes it and state any historical, generated, or session
exclusions used during the audit.
