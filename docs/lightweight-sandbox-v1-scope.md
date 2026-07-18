# Lightweight sandbox v1: active scope

Status: approved scope, revised for the single Resume Composer architecture on
2026-07-18.

## Goal

Use task-local same-user workspaces to reduce accidental context sharing and to
prevent unvalidated semantic output from becoming durable state. This is a
logical isolation and promotion boundary, not an operating-system security
boundary.

## Included

- One ephemeral sandbox for each advisory scout task.
- One ephemeral sandbox for the single Resume Composer task.
- One ephemeral sandbox for each selected Clean QA evaluator task.
- A copied, read-only input snapshot and the minimum task instructions required
  by each role.
- SHA-256 hashes for manifests and copied inputs.
- Private scratch space and declared output locations.
- Detection of changed inputs, changed manifests, unexpected artifacts, missing
  outputs, and source drift.
- No scout-to-scout reads. Scout reports are collected only by the coordinator.
- The Composer starts only after every advisory scout has finished and receives
  the complete pinned Composer input packet in one fresh task.
- Fail-closed coordinator validation before any Composer or Clean QA output is
  promoted.
- Cleanup of ephemeral workspaces only after their required durable handoff has
  succeeded.
- Documentation and end-to-end verification proportional to destructive or
  silent-failure risk.

## Active semantic task boundaries

- Advisory scouts run in fresh top-level Codex tasks with `gpt-5.6-terra` and
  reasoning `xhigh`.
- The Resume Composer runs in one fresh top-level Codex task with
  `gpt-5.6-sol` and reasoning `high`.
- Every Clean QA evaluator runs in its own fresh top-level Codex task under its
  clean skill boundary.
- No active semantic task runs as a subagent, fork, or reused task.
- The coordinator is the only component allowed to promote task output.

## Excluded

- Containers, virtual machines, Windows Sandbox, or separate OS identities.
- Warm or reusable sandboxes.
- JSONL lifecycle logging, telemetry, metrics dashboards, or tracing.
- Firewall rules or technically enforced network isolation.
- Schedulers, queues, circuit breakers, retries, failover, or dynamic model
  routing.
- Additional mandatory semantic gates between the scout wave and Composer.
- Multiple resume-writing tasks or deterministic assembly of section-level
  semantic results.
- Automatic QA-to-Composer repair or a second Composer pass after Clean QA.
- Changes to job-intake semantics or application behavior.
- Security claims stronger than the same-user filesystem model can provide.

Legacy implementations of excluded roles may remain as non-invoked code or
inside generated sessions. Their presence does not make them active pipeline
stages.

## Existing boundaries preserved

- Clean QA receives only the promoted final PDF and, where allowed, the
  normalized job description.
- Clean QA remains separate from scouts, Composer, knowledge base, parent chat,
  and earlier reports.
- Knowledge-base Markdown remains canonical and read-only during a tailoring
  run.
- The canonical resume baseline remains unchanged.
- Application completion and submission remain outside the system.

## Acceptance criteria

1. Every semantic task has a new top-level task identity and a private
   workspace.
2. Scout tasks cannot read one another's reports or workspaces.
3. The Composer receives exactly the pinned baseline, normalized job, completed
   advisory reports, and complete experience and project Markdown snapshots.
4. Input or manifest mutation, missing outputs, unexpected artifacts, or source
   drift blocks promotion.
5. No advisory scout writes or promotes resume content.
6. Only one Resume Composer task produces the employer-facing candidate.
7. The coordinator validates the complete Composer bundle before promotion.
8. Clean QA uses fresh isolated tasks and cannot read Composer or scout context.
9. Clean QA is terminal and triggers no automatic semantic repair.
10. Cleanup never runs before the required handoff or promotion succeeds.

## Change-control rule

Any implementation outside this document requires explicit user approval
before code is changed.
