---
id: project-adversarial-rpa-refactor-loop
name: Adversarial RPA Refactor Loop
status: implemented-internal
type: agentic-engineering-workflow
company: Grup Montaner
resume_safe: true
sources:
  - user-confirmed: 2026-07-18
  - github-pr:Grup-Montaner/camunda-bpm-montaner#218
  - github-pr:Grup-Montaner/camunda-bpm-montaner#219
  - github-pr:Grup-Montaner/camunda-bpm-montaner#222
  - github-pr:Grup-Montaner/camunda-bpm-montaner#223
  - article:https://bun.com/blog/bun-in-rust
evidence_checked: 2026-07-18
---

# Adversarial RPA Refactor Loop

## Purpose

Designed a bounded agentic workflow with Codex for refactoring production RPA code without
silently changing its Camunda contracts or observable NET4 behavior. The design
adapts the implement-review loop and isolated adversarial-review pattern
described in Bun's `Rewriting Bun in Rust` article.

## Workflow

- Freeze one explicit scope, non-goals, write set, changed-file budget, baseline
  commands, and acceptance evidence before implementation.
- Assign exactly one implementation writer.
- Validate the candidate diff and exact commit SHA deterministically.
- Send the same candidate SHA independently to a functional reviewer and a
  structural reviewer without sharing their outputs or the implementer's
  private reasoning.
- Route accepted findings through a checker and allow only bounded correction
  rounds.
- Treat tests as a regression oracle and preserve frozen behavior, including
  selectors, values, call order, waits, cleanup, Camunda topics, variables,
  errors, and retry semantics.

## Demonstrated use

- The bootstrap PR #218 introduced the governance, role contracts, scope
  validation, and diff-scope tooling with 11 passing tests.
- The loop was applied to RPA client-boundary refactors across PRs #219 and
  #222.
- PR #223 consolidated the reviewed code while preserving the approved blobs
  and an explicit no-regression contract for the NET4 trace.
- The bootstrap infrastructure itself was later excluded from the consolidated
  PR, so it must not be described as merged into the main repository.

## Reliability and evaluation evidence

- Repeatable baseline and acceptance commands.
- Tests used as the behavior and regression oracle.
- Independent functional and structural review contexts.
- Exact-SHA review identity and changed-file budget enforcement.
- Bounded review rounds with fail-closed scope checks.

The workflow does not currently measure model cost or latency and does not
maintain a longitudinal AI-evaluation dashboard. Those must not be claimed.

## Reusable resume bullet

- Designed and ran a bounded agentic refactor workflow with Codex using frozen
  scopes, baseline tests, and isolated functional and structural reviewers
  against exact commit SHAs, preserving the RPA's Camunda and NET4 behavior
  through regression gates.

## Evidence

- [Bootstrap PR #218](https://github.com/Grup-Montaner/camunda-bpm-montaner/pull/218)
- [Client-boundary PR #219](https://github.com/Grup-Montaner/camunda-bpm-montaner/pull/219)
- [Worker-adapter PR #222](https://github.com/Grup-Montaner/camunda-bpm-montaner/pull/222)
- [Consolidated PR #223](https://github.com/Grup-Montaner/camunda-bpm-montaner/pull/223)
- [Bun article](https://bun.com/blog/bun-in-rust)

## Evidence gaps

- Record the number of review rounds and accepted findings from a completed
  refactor when available.
- Add cost, latency, and longitudinal regression metrics only if the loop later
  captures them explicitly.
