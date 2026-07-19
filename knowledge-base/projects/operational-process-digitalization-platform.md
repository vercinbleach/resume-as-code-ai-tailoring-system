---
id: project-operational-process-digitalization-platform
name: Operational Process Digitalization Platform
type: internal-program
organization: Grup Montaner
period: July 2025 - present
status: draft
deployment_status: active-production
concurrent_users_approx: 250
sources:
  - archive/previous-cvs/CV Vincenzo 2026 (1).pdf
  - github-private:Grup-Montaner/camunda-bpm-montaner
  - github-private:Grup-Montaner/operaciones_montaner
  - github-public:vercinbleach/camunda-bpm-platform
  - github-public:vercinbleach/camunda-websocket-task-events
  - user-confirmed: 2026-07-16
  - user-confirmed: 2026-07-17
  - user-confirmed: 2026-07-18
evidence_checked: 2026-07-18
power_bi_reporting_status: deprecated
current_reporting_approach: conversational-data-agent
related_projects:
  - operations-app.md
  - camunda-websocket-task-events.md
  - camunda-modeler-fork.md
  - camunda-internal-platform-engineering.md
related_experience:
  - ../experience/grup-montaner-lead-developer.md
---

# Operational Process Digitalization Platform

## Scope boundary

This file describes the broader digitalization program and the confirmed
architecture of its Camunda-based process platform. The private
`camunda-bpm-montaner` repository is the primary code source for this entry.

GitHub confirms that the [Operations App](operations-app.md) is a separate
private codebase built around Next.js and SpacetimeDB for workforce operations,
planning, shifts, attendance, absences, and project staffing. No direct runtime
dependency between that repository and the Camunda repository was found, so its
domain model and stack remain documented separately.

The CI/CD, Docker, Docker Compose, scripting, and monitoring foundation is
documented in
[Camunda Internal Platform Engineering](camunda-internal-platform-engineering.md).

The public [Camunda Modeler Fork](camunda-modeler-fork.md) is not a dependency
of the private platform repository. The production code uses Camunda Modeler as
an external BPMN authoring and deployment tool, so the fork remains a separate
experiment.

## Problem

Core operational workflows were distributed across departments and depended on
systems that did not share data reliably. A legacy ERP had no API, creating an
integration barrier and making it difficult to centralize business-critical
processes, compliance data, approvals, document workflows, and management
reporting. The platform also needed centralized identity, auditable task state,
safe production delivery, and a way to connect browser-based workflows with a
Windows-only desktop ERP.

## What the platform does

The platform provides a web task portal and BPM runtime for orchestrating
cross-department workflows, managing forms and approvals, synchronizing CRM and
HR data, integrating an API-less ERP, generating controlled business
identifiers and documents, sending certified communications, and delivering
strategic KPIs to operational and executive stakeholders.

The platform is an active production system used across the company rather
than a limited departmental proof of concept. Approximately 250 people can be
operating in it simultaneously.

## Solution

- Camunda Platform 7.23 embedded in a Java 17 and Spring Boot 3.4.4 backend,
  exposing Camunda REST APIs, custom business endpoints, webapps, and process
  engine extensions.
- A dedicated Next.js 16, React 19, TypeScript, and Bun task portal for starting
  processes, completing typed forms, viewing open and participated tasks, and
  inspecting process history.
- Python components for FastAPI-based identifier generation, SQLAlchemy and
  Alembic-managed business data, Keycloak initialization, and Windows RPA.
- A Camunda External Task worker that uses `pywinauto` and `pyautogui` to control
  the API-less desktop ERP from an interactive Windows session.
- Keycloak 26 with OAuth 2.0, OpenID Connect, JWT validation, role-based access,
  and NextAuth integration.
- MySQL 8 databases for Camunda, business data, identifiers, and identity, plus
  Microsoft SQL Server access for legacy catalog data.
- Integrations with HubSpot CRM, Sesame HR, a certified-communications provider,
  SMTP/IMAP, and the legacy ERP.
- [deprecated] Power BI dashboards for department heads and executive
  leadership. These dashboards remain part of the implementation history but
  are no longer the current reporting approach.
- [current] A conversational AI agent is connected to the operational data so
  users can ask questions and explore the data through dialogue rather than
  relying on static dashboards. The confirmed workflow reads the platform data;
  the exact model, agent framework, permissions, interfaces, and whether an MCP
  layer is now involved remain undocumented.

## Reporting evolution

- [deprecated] Power BI was the previous reporting interface for centralized
  strategic KPIs and executive or departmental dashboards.
- [current] Reporting and analysis are moving to an agent connected to the
  operational data, enabling conversational questions and follow-up exploration
  over the available information.
- The knowledge base preserves Power BI as a historical contribution. It must
  not be described as the current reporting architecture in future resume or
  application material unless its status changes again.

## Confirmed system architecture

- The Next.js portal communicates with the Java backend through REST and uses
  Server-Sent Events for live task updates.
- The Spring Boot application hosts Camunda's process engine and webapps,
  implements Java delegates and listeners, exposes domain controllers, and
  coordinates CRM, HR, document, mail, identifier, and RPA interactions.
- Business output is exchanged through BPMN variables, typed DTOs, REST calls,
  Camunda External Tasks, database records, documents, and process artifacts.
- The identifier service uses FastAPI, Pydantic, SQLAlchemy, asynchronous MySQL,
  and Alembic, with reserve, confirm, and cancel operations for controlled IDs.
- Each project receives a controlled ISO identifier. Project documentation,
  recorded effort, and related artifacts reference that identifier, making it
  straightforward to trace what each item is, which project it belongs to, and
  how much time was dedicated to it. This is an internal traceability model,
  not a claim that the identifier itself represents an ISO certification.
- The labor-incidents data component uses Python, SQLAlchemy, MySQL, and Alembic
  migrations while business endpoints and workflow logic remain in the Camunda
  backend.
- The RPA worker polls Camunda over HTTP, performs ERP GUI operations, reports
  completed or failed External Tasks, emits heartbeats, and stores diagnostic
  logs and screenshots. PyInstaller packages it for Windows machines without a
  Python installation.
- Document workflows use Apache POI, XDocReport converters, and FreeMarker
  templates to generate Office/PDF content and notifications.

## Camunda 7 engine extensions and planned open-source plugins

The platform is also being used as the proving ground for a three-plugin
Camunda 7 extension initiative. The goal is to move capabilities that are now
specific to the application into reusable engine-level components and release
them as open source. The first plugin is now public and a second is planned:

- [Camunda WebSocket Task Events](camunda-websocket-task-events.md) is the
  confirmed real-time plugin and resolves the earlier WebSocket-versus-webhook
  uncertainty. It is designed as a plug-and-play realtime collaboration layer
  for Camunda 7 Spring Boot builds, addressing stale state and collisions when
  several authorized users can work on the same task. It exposes a native
  WebSocket/STOMP endpoint, publishes a two-field task invalidation only after
  the Camunda transaction commits, inherits application authentication,
  coalesces bursts, enforces connection limits, and emits Micrometer metrics.
  It is public under Apache 2.0 with 55 passing tests and green CI.
- An S3-backed document plugin for Camunda 7 is planned to centralize document
  storage and retrieval in the process engine rather than implementing S3
  document handling separately throughout the application.
- A third planned plugin whose purpose has not yet been recalled or identified.

The WebSocket library is a public pre-release at `0.1.0-SNAPSHOT`; it has no tag,
GitHub release, Maven Central artifact, or reported users yet. Its first target
is Camunda 7.24.x with Spring Boot 3.5.x, while the internal production platform
currently uses Camunda 7.23 and Spring Boot 3.4.4. It therefore represents the
implemented extraction path but is not yet recorded as the production SSE
replacement. The S3 and unidentified third plugin remain planned work. A public
fork at `vercinbleach/camunda-bpm-platform` still tracks upstream Camunda and
does not expose those remaining plugins.

Separately, the production repository already contains a working engine
extension that may be a candidate for the forgotten third plugin, but this is
not assumed without confirmation. `ProcessTitleProcessEnginePlugin` extends
Camunda's `AbstractProcessEnginePlugin`, registers a pre-parse BPMN listener,
reads `titleTemplate` and `titleRequiredVars` extension properties, and attaches
execution listeners that keep human-readable process-instance titles updated as
variables become available. Ten of the eleven production BPMN definitions use
the title template, along with two development diagrams.

## Business workflow coverage

The current repository snapshot contains eleven non-test BPMN definitions in
the backend's main process directory. They cover:

- Commercial proposal approval and risk evaluation.
- Lead qualification and creation of leads, contacts, and opportunities.
- Closed-won processing and client-management changes.
- Document-signature workflows.
- Labor-incident and disciplinary-action handling.
- Monitoring of the Windows RPA worker.

The workflows cross multiple business verticals, including Commercial,
Finance and Risk, Labor, Legal, Operations and Area Management, General
Management, and Shared Services. The platform is therefore processing
company-wide operations rather than one isolated workflow family.

The portal supplies process-specific React forms, Zod validation schemas,
preload logic, reusable field components, read-only historical snapshots, task
assignment, cancellation, and process-history views.

## Versioned BPMN evolution

Git provides a second source of evidence beyond the current repository
snapshot. Across the eleven production BPMN files, the history contains 141
file-level revisions between November 20, 2025 and July 15, 2026. This total
counts a commit once for each BPMN file it changed, so it describes revision
activity rather than unique repository commits.

The comparison below uses the first version of each file present in Git and
the version at the inspected repository head. Composition is shown as human
tasks / automated tasks / gateways; it deliberately ignores diagram-layout
changes.

| Process file | Git window | File revisions | First composition | Current composition |
| --- | --- | ---: | ---: | ---: |
| `aprobacion_comercial.bpmn` | 2026-01-26 to 2026-06-25 | 20 | 0 / 3 / 3 | 3 / 3 / 4 |
| `aprobacion_riesgos.bpmn` | 2026-02-19 to 2026-06-10 | 24 | 3 / 2 / 2 | 6 / 6 / 10 |
| `cierre_ganado.bpmn` | 2026-06-15 to 2026-07-15 | 8 | 1 / 4 / 1 | 1 / 5 / 1 |
| `creacion_contactos.bpmn` | 2026-01-19 to 2026-06-25 | 6 | 0 / 1 / 0 | 0 / 1 / 0 |
| `creacion_lead.bpmn` | 2026-02-18 to 2026-03-24 | 8 | 0 / 1 / 0 | 0 / 1 / 0 |
| `creacion_oportunidad.bpmn` | 2026-02-25 to 2026-06-25 | 7 | 0 / 1 / 0 | 0 / 3 / 2 |
| `firma.bpmn` | 2026-06-09 to 2026-06-27 | 8 | 5 / 2 / 6 | 5 / 0 / 5 |
| `gestion_clientes.bpmn` | 2026-06-17 to 2026-07-15 | 4 | 1 / 1 / 1 | 3 / 2 / 2 |
| `monitor_rpa_worker.bpmn` | 2026-05-05 to 2026-06-03 | 8 | 1 / 2 / 1 | 1 / 1 / 0 |
| `process.bpmn` (labor incidents) | 2025-11-20 to 2026-07-03 | 42 | 6 / 6 / 4 | 6 / 9 / 7 |
| `qualificacion_leads.bpmn` | 2026-02-18 to 2026-03-24 | 6 | 2 / 2 / 1 | 0 / 1 / 0 |
| Total current portfolio | 2025-11-20 to 2026-07-15 | 141 | 19 / 25 / 19 | 25 / 32 / 31 |

This history shows both expansion and simplification. Commercial approval,
risk, opportunity creation, client management, and labor incidents gained
decision points, human controls, or automated integrations. Lead
qualification, signature, and RPA monitoring were simplified as responsibilities
or automation moved elsewhere. The labor workflow is the longest-running and
most frequently revised BPMN in the repository, with 42 file-level revisions.

## Scale and delivery cadence

- Approximately 250 internal users can operate in the platform simultaneously.
- The platform supports multiple company verticals and is part of the ongoing
  digitalization of processes across the organization.
- It remains under active development while running in production, with code
  pushed and integrated on a daily basis.
- The Git history, current workflow definitions, production deployment files,
  and ongoing commits corroborate that this is a live and continuously evolving
  operational system.

## Productivity impact

- The work focuses on redesigning and digitizing complete end-to-end business
  processes rather than applying isolated UI or scripting improvements.
- BPMN orchestration, API integrations, document generation, notifications,
  controlled identifiers, and RPA replace or reduce manual handoffs across
  complete process chains.
- Centralized process state improves traceability, ownership, auditability, and
  access to the same operational information across business verticals.
- No accessible before-and-after cycle-time or productivity baseline is
  available, so no percentage or hours-saved claim is recorded. The defensible
  achievement is company-wide process transformation at active production
  scale.

## Authentication, reliability, and observability

- Keycloak provides centralized identity and Camunda authorization through
  OAuth 2.0/OIDC and JWT validation.
- SSE delivers live task changes to the frontend, while the backend maintains
  process history and task-form snapshots for auditability.
- The current SSE path connects the frontend directly to the backend after the
  earlier Bun proxy was removed. Its migration evidence covered 20 concurrent
  actors, 16 disposable tasks, and eight of eight race-condition scenarios; a
  live comparison observed 35 events on each path with no missing, duplicate,
  malformed, extra-field, or sensitive-field differences.
- The RPA layer includes worker heartbeats, session checks, structured logging,
  failure reporting, and error screenshots.
- Docker health checks coordinate service readiness across Keycloak, Camunda,
  MySQL, the identifier service, the labor data component, and the frontend.
- Backend and frontend validation includes JUnit 5, Spring Boot Test, Mockito,
  AssertJ, Bun tests, TypeScript checking, Oxlint, Knip, and BPMN linting.

## Deployment architecture

- Docker Compose defines reproducible development and production stacks.
- GitHub Actions detects affected services and builds selected container images
  with Docker Buildx.
- Amazon ECR stores versioned service images and build caches.
- AWS CodeBuild supplies ephemeral GitHub Actions runners.
- Deployment revisions are packaged in Amazon S3 and released to EC2 through
  AWS CodeDeploy using one-at-a-time deployments and post-deploy validation.
- Production delivery includes manual rollback to an existing commit image,
  concurrency controls, and a deploy guardian that distinguishes transient
  infrastructure failures from failures requiring investigation or a guarded
  rerun.
- Detailed CI/CD, scripting, container, and monitoring ownership remains in
  [Camunda Internal Platform Engineering](camunda-internal-platform-engineering.md).

## My contribution

- Architected and led full-stack development of the digitalization platform.
- Designed the Java and Python service ecosystem surrounding Camunda 7.
- Led development of the Next.js task portal, process-specific forms, Java
  delegates and listeners, API integrations, and data services.
- Implemented the Camunda External Task and Windows GUI-automation layer for the
  legacy ERP.
- Open-sourced the first reusable Camunda 7 extension as an Apache-2.0
  WebSocket/STOMP task-invalidation library with 55 passing tests, inherited
  application authentication, bounded coalescing, session limits, and
  Micrometer metrics.
- Designed the extension as a plug-and-play collaboration layer that keeps
  multiple users with access to the same task aligned with committed Camunda
  state while preserving REST and engine authority over concurrent actions.
- Initiated engine-level S3 document handling and a third reusable extension as
  the remaining planned plugins in the three-project open-source initiative.
- Built the existing process-title engine plugin and BPMN parse-listener layer
  used to derive readable instance titles from process variables across ten
  production workflows.
- Contributed across Keycloak authentication, database migrations, Docker
  environments, GitHub Actions, and AWS production delivery.
- [deprecated] Delivered centralized executive and departmental KPI dashboards
  in Power BI as the previous reporting approach.
- [current] Connected a conversational AI agent to operational data for
  question-driven analysis and follow-up exploration. Implementation details
  beyond this user-confirmed behavior are not yet recorded.

## GitHub evidence of contribution

- The private repository contains 891 commits in the inspected history. Git
  attributes 455 of them to the author names `Vincenzo` or `Vincenzo Rosciano`
  between September 3, 2025 and July 16, 2026.
- Those commits span the frontend, backend, identifier service, labor-incidents
  component, RPA worker, Keycloak initialization, Docker Compose, deployment
  workflows, operational scripts, tests, and documentation.
- The current snapshot contains 110 production Java source files, 24 Java test
  files, seven frontend test files, and 69 Python files across the supporting
  components.
- Repository structure and dependency manifests directly confirm Camunda 7.23,
  Java 17, Spring Boot 3.4.4, Next.js 16, React 19, Python, Keycloak, MySQL,
  SQL Server, Docker Compose, GitHub Actions, and AWS deployment tooling.

## Outcome

- Centralized operational data and workflows across core departments.
- Improved process reliability, data consistency, and communication according
  to the current CV.
- Established a production-oriented platform with authenticated task handling,
  resumable BPMN state, automated integrations, health checks, testing, and
  controlled AWS deployment and rollback paths.
- Supports approximately 250 simultaneous internal users across multiple
  business verticals in active production.
- Continues to receive daily code changes while processing live company
  operations.
- Extracted the first application-specific capability into a public Camunda 7
  WebSocket library with green CI; production integration and adoption remain
  future milestones.
- Supported a company described in the CV as having EUR 90M in annual revenue;
  this is organizational context, not a measured project outcome.
- No measured before-and-after productivity percentage or cycle-time metric is
  recorded yet.

## Technologies

- Backend and workflow: Java 17, Spring Boot 3.4.4, Maven, Camunda Platform
  7.23, BPMN, `AbstractProcessEnginePlugin`, BPMN parse listeners, execution
  listeners, Java delegates, REST, and Server-Sent Events
- Open-source realtime plugin: Spring WebSocket, STOMP, Camunda Spring Boot
  eventing, transactional after-commit listeners, Spring Security, JWT, opaque
  tokens, Camunda REST authentication, Micrometer, JUnit 5, and Maven
- Planned plugin technologies: Amazon S3-backed engine document storage and a
  third Camunda 7 extension whose scope remains to be identified
- Frontend: Next.js 16, React 19, TypeScript, Bun, Tailwind CSS 4, Radix UI,
  React Hook Form, Zod, Zustand, SWR, and NextAuth
- Python services: Python 3, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic,
  PyMySQL, and `aiomysql`
- Identity and security: Keycloak 26, OAuth 2.0, OpenID Connect, JWT, and
  role-based authorization
- Data: MySQL 8, Microsoft SQL Server, JDBC, and database migrations
- RPA: Camunda External Tasks, `pywinauto`, `pyautogui`, PyInstaller, and
  Windows desktop automation
- Integrations: HubSpot CRM, Sesame HR, certified communications, SMTP/IMAP,
  legacy ERP, and third-party REST APIs
- Documents and templates: Apache POI, XDocReport, FreeMarker, DOCX, and PDF
- Delivery: Docker, Docker Compose, GitHub Actions, Docker Buildx, AWS
  CodeBuild, Amazon ECR, Amazon S3, AWS CodeDeploy, and EC2
- Quality: JUnit 5, Spring Boot Test, Mockito, AssertJ, Bun Test, TypeScript
  type checking, Oxlint, Knip, and BPMN linting
- Historical reporting: Power BI [deprecated]
- Current reporting and analysis: conversational AI agent connected to
  operational data [current]
- Agent implementation details: model, framework, interfaces, permissions, MCP
  usage, and production safeguards remain to be documented

## Reusable resume bullet

- Architected and led a Camunda 7 process-digitalization platform for a EUR
  90M-revenue organization, combining Java 17 and Spring Boot, a Next.js and
  React task portal, Python services, authentication, Windows RPA, and
  controlled AWS delivery.
- Partnered weekly or biweekly with the Board of Directors to
  prioritize cross-department process digitalization, centralizing data,
  approvals, and documents through integrations with HubSpot, HR, certified
  communications, and an API-less legacy ERP.
- Initiated a three-plugin Camunda 7 extension program and open-sourced its
  first component, a WebSocket/STOMP task-invalidation library verified by 55
  tests, while S3-backed document handling remains planned.

## Related project network

- [Operations App](operations-app.md) covers the separate Next.js and
  SpacetimeDB workforce-operations application. GitHub shows no direct runtime
  dependency between it and the Camunda repository.
- [Camunda WebSocket Task Events](camunda-websocket-task-events.md) is the public
  pre-release extracted from the platform's planned SSE replacement.
- [Camunda Internal Platform Engineering](camunda-internal-platform-engineering.md)
  covers CI/CD, Docker, Docker Compose, scripting, and monitoring.
- [Collaborative Camunda Modeler Fork](camunda-modeler-fork.md) covers the
  separate public modeler experiment.
- [Lead Software Engineer role](../experience/grup-montaner-lead-developer.md) covers
  team leadership, GitHub Projects, and the GitFlow delivery process.

## Evidence gaps

- Confirm the organizational and data-sharing relationship between the wider
  program, the Camunda platform, and the separate Operations App; no code-level
  dependency was found.
- Identify the third planned Camunda 7 plugin and confirm whether it is the
  existing dynamic process-title extension or a separate initiative.
- Validate the WebSocket library against the internal Camunda 7.23 and Spring
  Boot 3.4.4 stack or document the production upgrade to its 7.24 and 3.5
  compatibility target.
- Record the WebSocket plugin's first Maven Central release and adoption, plus
  repository URLs, licenses, compatibility, tests, and releases for the S3 and
  third plugins when they are published.
