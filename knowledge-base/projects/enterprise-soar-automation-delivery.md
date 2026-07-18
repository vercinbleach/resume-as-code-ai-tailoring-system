---
id: project-enterprise-soar-automation-delivery
name: Enterprise SOAR Automation Delivery
aliases:
  - Splunk SOAR Playbooks
type: client-project
organizations:
  - Innovery
  - Neverhack
period: needs-confirmation
status: draft
client_reference: major telecommunications and ISP provider
sources:
  - archive/previous-cvs/CV Vincenzo 2025.pdf
  - archive/previous-cvs/CV Vincenzo 2026 (1).pdf
  - archive/previous-cvs/CV Vincenzo Actualizado - Copy.pdf
  - archive/previous-cvs/CV Vincenzo Actualizado ENG.pdf
  - archive/previous-cvs/vin cv.pdf
  - user-confirmed: 2026-07-17
evidence_checked: 2026-07-17
---

# Enterprise SOAR Automation Delivery

## Deduplication decision

The SOAR work appears under both Innovery and Neverhack because Neverhack
acquired Innovery Group. The repeated descriptions are treated as one continuous
project line until the exact employer and project dates are confirmed.

The end client is intentionally described externally as a major
telecommunications and ISP provider.

## Problem

The client's cyber operations depended on an enterprise, self-hosted Splunk
service for security diagnostics and alerting. The underlying infrastructure
therefore needed to remain healthy and available, but recurring monitoring,
machine recovery, capacity decisions, and remediation steps still required
manual intervention.

This created two connected risks: repetitive operational work consumed analyst
and engineering time, and degradation of the monitored Splunk service could
affect the wider cyber-detection and diagnostic capability that relied on it.

## What the application does

Custom Splunk SOAR playbooks automate both security-response tasks and operation
of the infrastructure supporting the Splunk service itself. They monitor
platform health, execute scripted recovery and machine-restart actions, perform
business and operational calculations, and activate capacity according to
defined conditions.

The engagement worked from a documented roadmap containing more than 40
identified automation use cases with different levels of complexity. More than
10 custom playbooks were implemented during the documented delivery period.

## Solution

- Enterprise, self-hosted Splunk SOAR deployment.
- Event-driven operational runbooks implemented as Python and Bash code.
- Monitoring and diagnostic automation for the Splunk service and its
  supporting infrastructure.
- Automated machine and service restarts, infrastructure remediation, IP
  blocking, and alert enrichment.
- Policy-driven capacity calculations and machine activation, providing
  autoscaling-style behavior through coded business and operational rules.
- Third-party API, security-tool, and infrastructure integrations.
- Iterative client delivery supported by weekly meetings and Agile practices.

## My contribution

- Translated high-level automation requirements into functional SOAR workflows.
- Contributed to the implementation of a roadmap with more than 40 identified
  use cases and developed and maintained more than 10 custom playbooks.
- Implemented Python and Bash orchestration logic for platform monitoring,
  diagnostics, machine restarts, capacity activation, response, enrichment,
  blocking, and remediation.
- Applied software-engineering practices to operational and DevOps-style
  automation instead of relying on manual runbooks alone.
- Participated in weekly client meetings and iterated on workflows based on
  client needs.

## Outcome

- Saved more than 20 hours of manual work per week.
- Generated approximately EUR 50K in annual operational savings based on the
  operational-cost calculations available through Splunk.
- Automated recurring alert-response activities that previously required manual
  intervention.
- Improved the operational resilience of a self-hosted Splunk service that
  supported the client's wider cyber-alerting and diagnostic capability.
- Converted recurring infrastructure operations into repeatable, coded,
  event-driven runbooks with policy-based execution.

## Technologies

- Splunk SOAR Enterprise, self-hosted
- Splunk
- Python
- Bash
- REST APIs
- Third-party security integrations
- Event-driven orchestration
- Infrastructure monitoring and remediation
- Policy-driven capacity management
- Self-healing operational runbooks

## Reusable resume bullets

- Delivered 10+ Python and Bash Splunk SOAR playbooks for a major
  telecommunications and ISP provider, saving 20+ hours weekly and approximately
  EUR 50K annually by automating platform monitoring, machine recovery,
  capacity activation, IP blocking, enrichment, and remediation.
- Engineered coded infrastructure runbooks from a roadmap of 40+ identified
  SOAR use cases, improving the resilience of a self-hosted Splunk service that
  underpinned cyber alerting and diagnostics.

## Evidence gaps

- Resolve the date discrepancy: the CVs variously place the work from October
  2024, September 2024, or January 2025 through July 2025.
- Record the exact formula and reporting period behind the approximately EUR
  50K annual operational-cost saving calculated through Splunk.
- Confirm the exact number of the 40+ identified use cases that reached
  production beyond the 10+ playbooks already documented.
- Add alert volume, number of machines or environments, execution success rate,
  mean-time-to-detect or recover improvement, exact weekly hours saved, and the
  most important integrations.
- Document the approval, retry, rollback, and failure-handling controls used for
  machine restarts, remediation, and capacity activation.
