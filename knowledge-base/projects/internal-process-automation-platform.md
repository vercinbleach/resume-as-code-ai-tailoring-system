---
id: project-internal-process-automation-platform
name: Internal Process Automation Platform
aliases:
  - Legacy No-Code Workflow Platform
  - ProcessMaker BPM Middleware
type: internal-platform
organization: Innovery
period: May 2023 - September 2024
status: draft
deployment_model: self-hosted
business_scale: approximately EUR 200M annual regional revenue
github_match_status: related-public-contribution-only
sources:
  - archive/previous-cvs/CV Vincenzo 2025.pdf
  - archive/previous-cvs/CV Vincenzo 2026 (1).pdf
  - archive/previous-cvs/CV Vincenzo Actualizado - Copy.pdf
  - archive/previous-cvs/CV Vincenzo Actualizado ENG.pdf
  - archive/previous-cvs/vin cv.pdf
  - github:SuiteCRM/SuiteCRM#10766
  - github:SuiteCRM/SuiteCRM-Core#457
  - user-confirmed: 2026-07-17
  - user-confirmed: 2026-07-19
evidence_checked: 2026-07-19
related_contributions:
  - opensource-contributions.md#suitecrm-documentrevision-api-fix
---

# Internal Process Automation Platform

## Deduplication decision

The CVs describe a legacy no-code platform, a ProcessMaker BPM, PHP and jQuery
forms, workflow playbooks, middleware, and CRM-to-ERP synchronization. These are
treated as descriptions of the same long-running internal automation platform.

## Role progression and internship evidence

Three historical CVs confirm that this work began as an Innovery internship from
May to August 2023 under the titles `Intern Software Engineer`, `Trainee Software
Engineer`, and `Desarrollador (Becario)`. The normalized title is Intern Software
Engineer.

During the internship, the documented scope already included PHP and jQuery
forms and pipelines in ProcessMaker, REST and SOAP integrations with CRM, ERP,
and internal systems, and independent Tier 1 and Tier 2 ticket resolution with
SLA adherence. The older CVs attribute a 25% operational-productivity
improvement to this work and the resulting real-time synchronization, but they
do not provide the calculation method.

The CV chronology then shows a transition to Junior Software Engineer in August
2023, with continued ownership and expansion of the same platform. The exact
Innovery-to-Neverhack transition remains inconsistent across sources: the latest
detailed CV uses September 2024, while earlier versions use January 2025.

## Problem

The company relied on a self-hosted workflow system originally assembled through
operator-authored no-code and low-code scripts. The platform had grown into a
dependency for core business operations, but its logic was fragile, generated
10-25 incoming bug reports per month, and connected poorly with business
systems, leading to manual imports and data silos.

The engineering challenge was to evolve that collection of scripts into a
reliable business-process backbone for a Spanish regional operation generating
approximately EUR 200M in annual revenue. Failures could affect sales,
operational delivery, employee services, and other processes used across the
business.

## What the application does

The platform became the orchestration layer for processes across the company:

- Sales and commercial workflows.
- Operational execution and delivery of contracted services.
- Internal ticketing and service requests.
- HR onboarding and employee leave requests.
- CEO signature requests and other internal approval flows.
- Technical evaluation of commercial proposals.
- Invoicing, internal ISO processes, and supporting documentation flows.

It also acts as middleware between the self-hosted SuiteCRM instance, ERP,
LinkedIn, Microsoft 365, KPI reporting, ticketing, project-management, calendar,
and process-specific microservices.

## Solution

- Self-hosted ProcessMaker and SuiteCRM environments.
- ProcessMaker workflows, PHP and jQuery forms, scripts, and playbooks.
- REST and SOAP integrations between internal and external platforms.
- CRM-to-ERP synchronization replacing manual data imports.
- Custom SuiteCRM module adaptation for company-specific processes and data.
- Supporting microservices serving invoicing, internal ISO, and other workflow
  capabilities.
- A transition from operator-maintained no-code and low-code scripting toward
  software-engineered workflow logic, integrations, and operational ownership.
- Refactoring of legacy workflow logic and direct Tier 1 and Tier 2 support.

## My contribution

- Re-engineered 90% of the logic across approximately 25 processes,
  stabilizing a platform used as a company-wide operational backbone.
- Designed and delivered new end-to-end processes, including CEO signature
  requests, technical evaluation of commercial proposals, onboarding, employee
  leave, internal ticketing, and operational-delivery workflows.
- Developed forms, scripts, pipelines, and integrations with PHP and jQuery.
- Architected an integration ecosystem spanning more than 10 platforms.
- Automated end-to-end data flow between the CRM and ERP.
- Customized SuiteCRM modules around company-specific workflows and data needs.
- Maintained and integrated microservices supporting invoicing, internal ISO,
  and other automated business processes.
- Eliminated recurring incoming bug reports after the platform rewrite.
- Trained a colleague for three months to transfer ownership and preserve
  project continuity.

## Outcome

- Reduced incoming bug reports from 10-25 per month to zero.
- Shifted incoming work from defect reports to enhancement requests and new
  process development.
- Progressed from an internship focused on workflow development and SLA-backed
  support into broader Junior Software Engineer ownership of the platform.
- Established a more reliable process backbone for sales, operations, service
  delivery, HR, approvals, and internal support within a regional business
  generating approximately EUR 200M in annual revenue.
- An older CV reports a 25% operational-productivity improvement; the
  measurement method needs confirmation before reuse.

## Technologies

- ProcessMaker, self-hosted
- SuiteCRM, self-hosted
- PHP and custom SuiteCRM modules
- jQuery
- REST APIs
- SOAP APIs
- CRM and ERP integrations
- Microsoft 365
- Microservices
- Business process management and workflow orchestration
- Low-code and no-code platform modernization
- SLA-based Tier 1 and Tier 2 support

## Related open-source contribution

The SuiteCRM API limitation encountered during this project led to a public
upstream contribution. The problem, patch, and pull-request history are
documented separately in
[Open Source Contributions](opensource-contributions.md#suitecrm-documentrevision-api-fix).

## GitHub evidence and boundary

No matching ProcessMaker, Innovery, middleware, or internal-platform repository
was found among the repositories available through the connected GitHub
account. GitHub therefore does not independently prove the workflow counts,
integration scope, support metrics, or productivity outcomes described in the
source CVs.

It does directly confirm one production-originated integration problem and its
technical solution:

- The original 2024 `SuiteCRM-Core` PR #457 states that Innovery's installed
  `set_document_revision` SOAP v4.1 endpoint did not work reliably.
- The patch added `DocumentRevision` file uploads to the V8 JSON API through
  two PHP changes: module-service handling and a virtual `filecontents` field.
- The implementation accepts base64 file content, validates extensions against
  SuiteCRM's blocked-extension configuration, writes the upload, and persists
  filename and detected MIME-type metadata.
- The contribution was reopened against the correct SuiteCRM 7 repository in
  2026 as PR #10766. GitHub currently reports it as open and mergeable, with two
  commits, two changed files, 57 additions, and one deletion.
- A separate community user later reported needing the same missing API
  capability, supporting that the integration limitation was not unique to the
  original installation.
- User-confirmed on 2026-07-19: the patch runs in production in Innovery's
  internal SuiteCRM deployment and in downstream user forks, while the upstream
  PR remains unmerged.

This public contribution demonstrates PHP backend development, legacy-to-modern
API migration, REST and SOAP integration work, file-transfer handling, and the
ability to turn an internal systems problem into an upstream open-source patch.

## Reusable resume bullets

- Stabilized the operational backbone of a regional business generating
  approximately EUR 200M annually by re-engineering 90% of the logic across
  approximately 25 ProcessMaker processes, reducing incoming bug reports from
  10-25 per month to zero and shifting demand to enhancements and new processes.
- Connected 10+ business platforms and eliminated manual CRM-to-ERP imports by
  building PHP, REST, and SOAP integrations, customized SuiteCRM modules, and
  process-specific microservices.
- Expanded a self-hosted workflow platform across sales, operations, delivery,
  HR, approvals, ticketing, invoicing, and ISO processes by developing new
  ProcessMaker workflows and supporting services.
- Progressed from intern to Junior Software Engineer after developing PHP and
  jQuery ProcessMaker workflows, REST and SOAP integrations, and SLA-backed
  support for a company-wide automation platform.

## Evidence gaps

- Resolve whether the project ended in September 2024 or January 2025.
- Recover the calculation method for the 25% productivity claim. Multiple CVs
  associate it with workflow automation and real-time systems synchronization,
  but none defines the baseline or measurement period.
- Identify the ERP, ticketing, project-management, and calendar platforms that
  can be named publicly.
- Recover the exact process count and complete list; current user recollection
  places the platform at approximately 25 processes.
- Document the architecture and technology of the invoicing, ISO, and other
  process-supporting microservices.
- Locate any export, source snapshot, architecture diagram, sanitized playbook,
  or ticket history that can corroborate the private ProcessMaker platform.
