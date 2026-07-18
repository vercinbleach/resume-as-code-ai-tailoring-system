---
id: project-operations-app
name: Operations Outsourcing App
aliases:
  - Operations App
  - App de Operaciones
  - Operaciones outsourcing
type: internal-application
organization: Grup Montaner
period: March 2026 - present
status: draft
deployment_status: limited-production
business_scope: core-outsourcing-operations
product_category: custom-workforce-management-time-attendance-payroll-operations
market_fit: no off-the-shelf product matched the confirmed outsourcing workflow
rollout_scope: small-clients
target_employees_approx: 3000
client_portfolio_approx: 10-15
large_clients_approx: 3
very_large_clients_approx: 2
spreadsheets_per_client_min: 7
estimated_spreadsheets_in_scope: 70-105
delivery_ownership: solo
sources:
  - archive/previous-cvs/CV Vincenzo 2026 (1).pdf
  - github-private:Grup-Montaner/operaciones_montaner
  - user-confirmed: 2026-07-17
  - user-confirmed: 2026-07-18
  - user-confirmed: 2026-07-19
evidence_checked: 2026-07-19
related_projects:
  - operational-process-digitalization-platform.md
related_experience:
  - ../experience/grup-montaner-lead-developer.md
---

# Operations Outsourcing App

## Scope boundary

This is an independent workforce-operations application in the private
`Grup-Montaner/operaciones_montaner` repository. Its product metadata names it
`Operaciones outsourcing` and describes it as an application for managing
services delivered at client sites.

Its strategic scope is the outsourcing division, described by the project
owner as the largest part of Grup Montaner's business. The product is intended
to become the operational control plane for that division rather than a narrow
scheduling utility.

The application is already being used with smaller clients and is planned to
expand across the full outsourcing operation. Its target scope is approximately
3,000 employees across a portfolio of roughly 10 to 15 clients, including two
very large clients and three additional large clients.

The previous knowledge-base draft incorrectly treated it as the frontend of
the Camunda process platform and attributed Java, Python microservices, BPMN,
CRM synchronization, legal-sanction tracking, controlled identifiers, and RPA
to it. GitHub does not support those claims for this repository. The Operations
Outsourcing App uses a separate Next.js and SpacetimeDB architecture and has no
confirmed runtime dependency on the Camunda codebase.

## Problem

The most painful operational problem was not spreadsheet volume by itself. It
was the dependency between attendance records, error correction, and payroll.
Workers clock in at client sites, and missing, inconsistent, or incorrect clock
records must be resolved before payroll can be prepared correctly across an
outsourcing operation of approximately 3,000 workers.

Before the application, clocking errors and the fragmented information needed
to resolve them created risk and manual effort late in the payroll workflow.
Schedules, clock records, absences, corrections, payroll inputs, worker
coverage, and other operational data also lived across disconnected Excel
workbooks, making it difficult to maintain one current operational state.

Each client requires at least seven operational Excel workbooks. Across the
current portfolio of approximately 10 to 15 clients, this represents an
estimated 70 to 105 spreadsheets in scope before accounting for additional
office-specific copies or manual derivatives.

Outsourcing operations need to model recurring client demand separately from
the people who cover it. A single project can span several client sites,
operational areas, schedules, staffing requirements, and rotating patterns.
The system must preserve historical assignments while allowing future plans to
change, expose uncovered demand, handle replacements and absences, and reconcile
planned time with attendance and internal project effort.

Generic employee scheduling alone does not cover this operating model. The
application therefore combines workforce planning and attendance capabilities
with an outsourcing-specific hierarchy rooted in the client project.

## What the application does

- Receives worker clock-ins from tablet-based time clocks deployed at client
  sites.
- Validates the connected attendance data and identifies errors that need
  review before payroll.
- Gives service managers an operational view where they can inspect and correct
  the detected errors.
- Synchronizes the corrected information automatically with the connected
  payroll system. Vincenzo also implemented this payroll integration.
- Replaces fragmented operational spreadsheets with a shared, real-time working
  environment for the outsourcing division.
- Models clients, projects, centers, areas, services, agreements, workers,
  contracts, skills, and project assignments.
- Defines recurring demand through project operational lines with location,
  area, schedule, operating days, required headcount, validity, and optional
  shift-pattern rules.
- Materializes publishable shifts independently from worker assignment, making
  vacancies, partial coverage, replacements, and last-minute changes explicit.
- Supports saved shifts, rotating patterns, annual calendars, labor calendars,
  holidays, rest days, blocked periods, and planning incidents.
- Handles clock records, breaks, attendance incidents, corrections, timesheet
  review, edit requests, and overtime requests.
- Consolidates schedule, clocking, absence, and payroll-preparation information
  in the same operational model.
- Connects the interdependent clocking, correction, attendance, and payroll
  preparation stages needed to pay workers correctly. Broader payroll
  calculation capabilities remain under development.
- Manages leave types, policies, balances, adjustments, absence requests, and
  company-schedule assignments.
- Separates fixed operational hours from internal project tasks and time entries
  so both kinds of effort can be reported under one project.
- Provides administrator, client, project, and worker-facing routes, including
  project dimensioning, shift planning, annual calendars, organization views,
  attendance, absences, contracts, documents, and timesheets.
- Includes import and synchronization tooling for Net4 data and operational
  datasets associated with Avico, Volpak, and Bureba, plus CSV/XLSX reporting
  utilities.

## Business role

The intended role is comparable to an internal, company-specific Factorial for
Grup Montaner's outsourcing operation. Unlike a generic HR product, its domain
starts from the client project and the service demand that must be covered. HR,
attendance, planning, and payroll-preparation capabilities are adapted around
that operating model.

The important transformation is not simply replacing Excel files with web
forms. It closes the operational path from a worker clocking in at a client
site to corrected attendance data reaching payroll. Service managers work from
one current state, review the errors detected by the application, correct them,
and allow the connected payroll workflow to continue with cleaner inputs.

The product is therefore closer to a company-specific Factorial for outsourcing
operations than to a scheduling dashboard. Its primary business value is
reducing payroll risk created by attendance errors across an operation of
approximately 3,000 workers.

## Product category and market gap

The application is a custom workforce-management, time-and-attendance, and
payroll-operations platform for outsourced service delivery. It was designed ad
hoc around Grup Montaner's project-centered operating model, where client sites,
service demand, staffing coverage, replacements, attendance correction, and
payroll preparation depend on one another.

Factorial remains a useful product analogy because it combines HR, time
tracking, attendance, and payroll capabilities. The Operations App is not a
generic Factorial clone: its core domain starts from outsourced client projects
and the services and shifts that must be covered.

Vincenzo confirmed that the company found no off-the-shelf product covering this
complete operating model and dependent workflow. This is a user-confirmed
internal market assessment, not an independently verified claim that no product
anywhere offers overlapping features.

The rollout currently covers smaller clients. The common model is intended to
extend the same controls and process to every outsourcing client, reducing
client-by-client operational variation and giving all offices a standardized
way of working.

## Domain design

The current domain model uses `Project` as the business and operational root:

```text
Client
  -> Project
       -> Project operational line
            -> Shift
                 -> Shift assignment
       -> Internal task
            -> Internal time entry
```

Important modeling decisions include:

- Operational demand belongs to a project line, not to a worker. A vacancy
  remains visible when no person is assigned.
- `Shift` represents published operational coverage, not the universal working
  schedule of every employee.
- Worker-to-project assignment records the base relationship, while individual
  shift assignments represent actual coverage and replacements.
- Operational planning and corporate attendance are separate. Internal workers
  can use company schedules or contract hours without artificial project shifts.
- Historical shifts and assignments are preserved while future planning can be
  changed through validity periods, overrides, or amendments.

## Confirmed architecture

- Next.js 16.2 App Router, React 19.2, and TypeScript provide the application
  shell, 57 page routes, forms, dashboards, calendars, planning views, and role
  surfaces.
- SpacetimeDB 2.6 is both the transactional backend module and real-time data
  layer. The module is written in TypeScript and exposes generated bindings to
  the frontend over WebSockets.
- The inspected schema contains 66 domain tables and 148 reducers covering
  planning, attendance, leave, contracts, calendars, imports, and administrative
  operations.
- Business invariants and authorization are enforced in server-side reducers,
  keeping state changes close to the data model rather than distributing them
  across conventional REST controllers.
- SpacetimeAuth provides OIDC Authorization Code with PKCE. The frontend checks
  authenticated access and the SpacetimeDB module enforces active accounts and
  `ADMIN` or `WORKER` authorization in reducer guards.
- Zustand manages selected client-side state, while generated SpacetimeDB
  bindings drive real-time subscriptions and mutations.
- SQL Server connectivity through the `mssql` package supports controlled Net4
  synchronization and data-exploration utilities.
- Docker Compose supplies local SpacetimeDB, module publication, and Next.js
  development or demo environments.

## Product and engineering scope in GitHub

- The `operaciones/` application tree contains 708 files at the inspected head,
  including 373 TypeScript files, 214 TSX files, 57 page routes, and 96 React
  component files.
- The SpacetimeDB module defines 66 tables and 148 transactional reducers.
- The repository contains 13 TypeScript test files for timesheets, attendance,
  calendars, imports, worker-hour summaries, and project fixtures.
- Git attributes all 95 commits in the repository history to `Vincenzo` or
  `Vincenzo Rosciano` between March 25 and June 25, 2026.
- Development accelerated from three commits in March and eight in April to 12
  in May and 72 in June, showing sustained implementation through the
  production-delivery phase.

These are repository-scope measurements, not claims about production adoption
or business volume.

## Authentication and safety

- SpacetimeAuth uses OIDC Authorization Code with PKCE and automatic token
  renewal.
- The web application gates private routes and verifies administrator access.
- The backend module maps authenticated identities to active user accounts and
  applies explicit administrator or worker guards to reducers.
- CI materializes public authentication configuration in an ephemeral checkout
  and fails if placeholders remain before publication.
- Production publication uses a non-destructive SpacetimeDB mode and includes a
  scanner that rejects destructive deployment commands.

## Quality and delivery

- Bun 1.3 manages dependencies, development, builds, and tests.
- Quality checks include TypeScript compilation, ESLint, Bun Test, SonarQube,
  production Next.js builds, SpacetimeDB version alignment, and determinism
  checks.
- Playwright and Selenium utilities support automated navigation screenshots and
  product review.
- GitHub Actions runs quality checks for pull requests and `main`.
- The production workflow publishes the SpacetimeDB module to Maincloud without
  deleting data, builds an immutable Next.js Docker image, pushes it to Amazon
  ECR, packages a deployment revision in Amazon S3, and releases it to EC2 with
  AWS CodeDeploy.
- AWS access uses GitHub OIDC rather than long-lived access keys. The deployed
  Next.js service is designed to run behind Apache HTTPS while clients connect
  directly to SpacetimeDB Maincloud over WSS.
- The repository provides production configuration and deployment automation.
  The project owner confirms that the application is already used with smaller
  clients and is being prepared for wider operational rollout.

## My contribution

- Independently architected, designed, and implemented the full-stack
  application around a real-time, TypeScript-only Next.js and SpacetimeDB
  architecture.
- Designed the outsourcing domain model for projects, multi-site demand,
  recurring operational lines, shifts, coverage, replacements, attendance,
  leave, and internal time allocation.
- Built administrative, project, client, and worker interfaces for planning,
  calendars, clocking, absences, contracts, and timesheet review.
- Implemented the SpacetimeDB schema, transactional reducers, generated client
  bindings, real-time subscriptions, and authorization guards.
- Added controlled import and synchronization paths for legacy operational data.
- Implemented the automatic integration between corrected attendance data and
  the connected payroll system.
- Built local Docker environments and the GitHub Actions and AWS production
  delivery path.
- Git attributes all 95 commits in the current repository history to my author
  identities.
- Delivered the application solo, using established workforce-management and
  business-software products as design references while adapting the experience
  to Grup Montaner's outsourcing model.

## Outcome

- Nearly eliminated the attendance-data errors that previously propagated into
  payroll preparation; the remaining errors are identified by the application
  for service managers to correct. This is a user-confirmed qualitative result,
  not a measured error-rate reduction.
- Connected tablet-based clock-ins at client sites, automated error detection,
  manager correction, and payroll synchronization as one dependent operational
  workflow.
- Began replacing fragmented operational Excel workbooks with a collaborative,
  real-time application that is already used with smaller outsourcing clients.
- Defined a rollout path for approximately 3,000 employees across roughly 10 to
  15 clients, including two very large and three large client operations.
- Brought an estimated 70 to 105 client spreadsheets into the standardization
  scope, based on at least seven operational workbooks per client.
- Established a unified operational model connecting client projects, recurring
  staffing demand, published shifts, actual coverage, attendance, and internal
  effort.
- Made vacancies and replacements first-class operational concepts instead of
  rewriting a worker's base assignment.
- Created a real-time product architecture with one TypeScript domain across the
  frontend and transactional backend.
- Added a guarded production-delivery path for both the web application and its
  SpacetimeDB module.
- Centralized schedules, clock records, absences, and payroll-preparation data
  that had previously been managed across separate spreadsheets.
- Established one common operational process and control model for every client,
  replacing client-specific ways of working with a standardized approach.
- No verified active-user, process-volume, time-saving, or productivity metric is
  available, so no business-impact percentage is claimed.

## Technologies

- Application: Next.js 16.2, React 19.2, TypeScript 5.6, Bun 1.3, App Router
- Real-time backend: SpacetimeDB 2.6, TypeScript modules, tables, reducers,
  generated bindings, WebSockets, Maincloud
- UI and state: Tailwind CSS, Radix UI, Lucide React, Zustand, React Flow,
  Sonner, Temporal polyfill
- Identity: SpacetimeAuth, OpenID Connect, OAuth 2.0 Authorization Code with
  PKCE, JWT, role-based authorization
- Data and integration: Microsoft SQL Server, `mssql`, Net4 synchronization,
  XLSX and CSV processing
- Quality: Bun Test, TypeScript type checking, ESLint, SonarQube, Playwright,
  Selenium, SpacetimeDB determinism and version guards
- Delivery: Docker, Docker Compose, GitHub Actions, Docker Buildx, GitHub OIDC,
  Amazon ECR, Amazon S3, AWS CodeDeploy, EC2, Apache HTTPS

## Reusable resume bullets

- Independently built a custom workforce-management and payroll-operations
  platform for an outsourcing model not covered by off-the-shelf HR software,
  connecting tablet clock-ins, attendance validation, manager corrections, and
  automatic payroll synchronization for approximately 3,000 workers.
- Nearly eliminated payroll-impacting attendance errors and surfaced remaining
  inconsistencies for service managers to correct, with no measured reduction
  percentage currently available.
- Replaced fragmented spreadsheet workflows with one operational path for
  schedules, clock records, absences, corrections, and payroll preparation.
- Built the platform across 57 application routes, 66 domain tables, and 148
  transactional reducers using Next.js 16, React 19, TypeScript, and
  SpacetimeDB 2.6.
- Unified multi-site workforce planning, shift coverage, replacements,
  attendance, leave, and timesheets in a project-centered domain model, backed
  by real-time subscriptions and server-side authorization guards.
- Built a guarded production-delivery path for a Next.js web application and
  SpacetimeDB module using Docker, GitHub Actions, AWS OIDC, ECR, S3,
  CodeDeploy, and EC2.

## Related project network

- [Operational Process Digitalization Platform](operational-process-digitalization-platform.md)
  is the separate Camunda-based process platform. GitHub shows no direct runtime
  dependency between the two applications.
- [Lead Software Engineer role](../experience/grup-montaner-lead-developer.md) contains
  the broader role and team context.

## Evidence gaps

- Add the number of active tablet clock-in sites and devices.
- Add the current number of service managers using the correction interface.
- Confirm how many of the approximately 3,000 workers are currently processed
  through the application rather than only included in the wider business
  scope.
- Confirm which additional user surfaces are active beyond tablet clock-ins and
  the service-manager correction workflow.
- Add a rollout date for the three large and two very large clients.
- Add verified counts for managed projects, workers, shifts, clock records, or
  monthly planning activity if they become available.
- Clarify which Net4, Avico, Volpak, and Bureba paths are scheduled production
  integrations versus controlled imports, migrations, or demos.
- Clarify which calculations and fields are produced internally before corrected
  attendance data is synchronized with payroll.
- Add a measured operational result such as planning time reduced, payroll
  corrections avoided, uncovered shifts detected, or attendance incidents
  resolved after the larger rollout.
