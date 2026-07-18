---
id: project-resume-as-code-ai-tailoring-system
name: Resume as Code and AI Tailoring System
aliases:
  - Verifiable Resume Knowledge Base
  - AI Resume Composer and Clean QA
type: personal-developer-tool
team_size: 1
status: active-development
repository_status: public open-source repository
repository_url: https://github.com/vercinbleach/resume-as-code-ai-tailoring-system
evidence_checked: 2026-07-19
sources:
  - ../../README.md
  - ../../docs/system-architecture-diagrams.md
  - ../../docs/lightweight-sandbox-v1-scope.md
  - ../../docs/writer-orchestration-v1-scope.md
  - ../../tailoring/README.md
  - ../../qa/README.md
  - ../../tests/test_resume_composer_pipeline.py
  - ../../tests/test_sandbox_workspace.py
---

# Resume as Code and AI Tailoring System

## Problem

Traditional resumes compress years of work into a manually edited document,
making it difficult to preserve evidence, tailor content consistently, prevent
unsupported claims, and evaluate the exact PDF seen by an employer.

## What the system does

This personal developer tool maintains a canonical Markdown knowledge base of
experience and projects, captures observable job requirements, and composes a
job-specific one-page resume from verified evidence.

The active workflow uses advisory AI scouts to identify relevant evidence and
risks, followed by one global Resume Composer that plans the complete document,
writes a RenderCV YAML source, renders the PDF, and visually inspects the actual
one-page result. A deterministic coordinator gate verifies hashes, inventory,
source drift, document structure, links, and PDF preflight before promotion.

Clean QA then evaluates only the promoted PDF in isolated top-level tasks. Each
evaluator receives the minimum allowed inputs and cannot see the knowledge base,
Composer context, prior reports, browser state, or parent conversation.

## Architecture

1. Job Intake inspects the visible job and application form without submitting
   personal data or completing the application.
2. The Markdown knowledge base stores full experience and project narratives,
   optional atomic claims, evidence sources, conflicts, and resume-safety notes.
3. Independent advisory scouts analyze relevance, gaps, and contradictions.
4. A single global Resume Composer receives the baseline, normalized job,
   complete Markdown snapshot, and scout reports.
5. RenderCV and Typst generate a one-page PDF that the Composer must inspect
   visually before handoff.
6. The coordinator verifies SHA-256 manifests, source drift, expected outputs,
   factual metadata, PDF structure, and one-page constraints before atomic
   promotion.
7. Clean QA runs isolated technical, leadership, job-match, and callback
   evaluators against the final employer-visible artifact.

## Reliability and evidence controls

- Full Markdown snapshots prevent retrieval summaries from silently dropping
  relevant evidence.
- Optional structured claims link statements to sources, confidence, caveats,
  sensitivity, and resume-safety decisions.
- Task workspaces use read-only input copies, SHA-256 manifests, declared output
  inventories, source-drift checks, and all-or-nothing promotion.
- The lightweight sandbox is explicitly documented as logical same-user
  isolation, not an operating-system security boundary.
- Clean evaluators run in fresh top-level tasks and cannot contaminate one
  another with previous judge output.
- Generated sessions, PDFs, and historical CVs are not treated as canonical
  knowledge.

## Verified implementation scope

- 31 Python files across orchestration, contracts, validation, PDF inspection,
  evidence handling, and tests.
- 14 PowerShell scripts across resume generation, tailoring sessions, task
  workspaces, promotion, and QA.
- 23 Python unit and end-to-end tests passing on July 18, 2026.
- Successful end-to-end test of Composer bundle creation, RenderCV rendering,
  PDF checks, manifest validation, and atomic promotion.
- Canonical architecture and access boundaries documented with Mermaid diagrams.

These counts describe the local workspace at the evidence-check date and may
change as development continues.

## Technologies and practices

- Python
- PowerShell
- RenderCV 2.8
- Typst
- YAML and JSON
- JSON Schema
- pypdf
- SHA-256 manifests
- Git
- Codex task orchestration
- LLM advisory scouts and global composition
- LLM-as-judge evaluation
- Context management through complete source snapshots
- Custom agent harnesses and scaffolding
- Deterministic validation and PDF preflight
- Logical task sandboxing
- Test-driven contract validation
- Mermaid architecture documentation

## My contribution

- Designed and iteratively developed the personal resume-as-code workflow with
  AI-assisted implementation and review.
- Defined the knowledge-base structure and continuously supplied, corrected,
  and reconciled the underlying professional evidence.
- Shaped the orchestration boundaries between advisory scouts, the global
  Composer, coordinator gates, and clean evaluators.
- Established conservative evidence rules that preserve uncertainty, ownership
  limits, source conflicts, and unsupported historical claims.
- Drove repeated architecture and QA iterations using real job-tailoring runs.

## Outcome

- Created a reproducible workflow that turns a verified professional history
  and one job description into a rendered one-page resume candidate.
- Separated generation from terminal evaluation so judges score only the PDF an
  employer would receive.
- Added deterministic gates that block incomplete bundles, source drift,
  unexpected outputs, tampered inputs, and invalid PDF structure.
- Replaced ad hoc resume editing with a documented, test-backed engineering
  system that retains full evidence and explicit uncertainty.

## Reusable resume bullets

- Created a resume-as-code and AI tailoring system with 31 Python files, 14
  PowerShell scripts, and 23 passing tests, generating one-page RenderCV PDFs
  from a versioned Markdown knowledge base.
- Designed a multi-agent resume workflow with Codex, specialized scouts,
  deterministic coordinator gates, and isolated LLM evaluators to separate
  evidence discovery, document generation, and employer-view QA.
- Implemented SHA-256 manifests, read-only task inputs, source-drift detection,
  PDF preflight, and atomic promotion to prevent unsupported or incomplete
  resume artifacts from becoming final outputs.

## Repository and publication status

The project is published under the MIT license at
[vercinbleach/resume-as-code-ai-tailoring-system](https://github.com/vercinbleach/resume-as-code-ai-tailoring-system).
The public repository contains the reusable engine, tests, architecture
documentation, resume sources, and canonical Markdown knowledge base.

Generated sessions, output PDFs, historical resume PDFs, and job-specific
browser captures remain excluded because they are derived artifacts rather than
project source.

## Evidence gaps and next steps

- Add synthetic experience, project, job, and resume fixtures for a public demo.
- Configure CI for the test suite and resume-build smoke test.
- Add a concise public architecture image or demo recording.
