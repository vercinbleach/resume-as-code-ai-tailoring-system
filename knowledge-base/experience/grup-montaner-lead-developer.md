---
id: exp-grup-montaner-lead-developer
company: Grup Montaner
role: Lead Software Engineer
location: Barcelona, ES
start_date: 2026-01
end_date: present
team_size: 3
direct_reports: 2
status: draft
sources:
  - user-confirmed: 2026-07-16
  - user-confirmed: 2026-07-18
  - user-confirmed: 2026-07-19
  - github:vercinbleach/camunda-modeler-interno
  - github:vercinbleach/camunda-websocket-task-events
  - linkedin-profile-checked: 2026-07-17
linkedin_title_conflict: Profile still lists Software Engineer from 2025-07 to present
previous_role: grup-montaner-software-engineer.md
related_projects:
  - ../projects/operational-process-digitalization-platform.md
  - ../projects/operations-app.md
  - ../projects/adversarial-rpa-refactor-loop.md
  - ../projects/camunda-internal-platform-engineering.md
  - ../projects/camunda-websocket-task-events.md
  - ../projects/camunda-modeler-fork.md
---

# Grup Montaner - Lead Software Engineer

## Promotion context

Promoted from Software Engineer to Lead Software Engineer in January 2026 as the current
development team expanded to three people. The team consists of Vincenzo and
two developers under his technical and delivery leadership.

The promotion is user-confirmed but is not yet reflected on LinkedIn, which
still shows `Software Engineer` at Grup Montaner from July 2025 to the present.
This is a profile-maintenance gap, not evidence against the internal promotion.

## Team leadership

- Lead a three-person development team and directly manage two developers.
- Coach both developers on programming, decomposing work into implementable
  tasks, and applying consistent engineering practices and coding style.
- Coordinate technical priorities and ownership across the Operations App,
  internal Camunda platform, infrastructure, and supporting services.
- Guide the team through implementation decisions and delivery dependencies.

## Executive collaboration and prioritization

- Work directly with the Board of Directors in weekly or biweekly sessions.
- The Board participants include the CEO, the CFO who also serves as
  Controller, and the COO.
- Translate process needs and executive priorities from those sessions into
  scoped and prioritized delivery work for the development team.
- This is recurring direct collaboration with the Board, not a claim of a
  formal reporting line.
- Resume presentation should keep this process-prioritization evidence with the
  internal process-digitalization work, not combine it with the coaching bullet.

## GitHub Projects and delivery management

- Use GitHub Projects to organize, prioritize, assign, and track work across the
  team.
- Maintain visibility of current work and delivery status through a shared
  project board.
- Connect project planning with repository branches and pull requests.

GitHub Projects is recorded as user-confirmed evidence because the board is not
publicly visible from the authenticated repository connector or public profile.

## Git workflow

- Coordinate a GitFlow-based process using stable `main` and integration
  `develop` branches together with work branches and pull requests.
- Integrate completed work into `develop` through pull requests before it
  advances toward a stable release branch.
- Use branch separation to support parallel development while protecting the
  stable code line.

## Technical leadership scope

- Set technical direction across the Operations App and internal Camunda
  platform.
- Coordinate delivery involving Next.js, React, Java, Python microservices,
  Docker, Docker Compose, CI/CD, scripting, and monitoring.
- Align application development, BPM workflows, platform engineering, and
  operational requirements.
- Extract reusable platform capabilities into public Camunda 7 components,
  beginning with the WebSocket task-invalidation library.

## GitHub evidence

The public `camunda-modeler-interno` repository contains `main` and `develop`
branches plus multiple work branches. Seven visible pull requests were merged
into `develop` on June 23, 2026, demonstrating a branch-and-PR integration
workflow.

The public repository does not prove the private GitHub Projects board or team
size. Those facts are recorded from the user's confirmation.

## Outcome

- Established a visible planning and delivery process for a three-person team.
- Created clearer ownership and coordination across parallel application and
  platform workstreams.
- Standardized integration around GitFlow, branches, and pull requests.
- No verified delivery-frequency, lead-time, review-time, or throughput metric
  is documented yet.

## Technologies and practices

- GitHub Projects
- Git and GitFlow
- Pull requests
- Camunda
- Next.js and React
- Java and Python microservices
- Docker and Docker Compose
- CI/CD
- Monitoring and scripting

## Related project network

- [Operational Process Digitalization Platform](../projects/operational-process-digitalization-platform.md)
- [Operations App](../projects/operations-app.md)
- [Adversarial RPA Refactor Loop](../projects/adversarial-rpa-refactor-loop.md)
- [Camunda Internal Platform Engineering](../projects/camunda-internal-platform-engineering.md)
- [Camunda WebSocket Task Events](../projects/camunda-websocket-task-events.md)
- [Collaborative Camunda Modeler Fork](../projects/camunda-modeler-fork.md)
- [Previous Software Engineer role](grup-montaner-software-engineer.md)

## Reusable resume bullets

- Lead a three-person development team, directly managing and coaching two
  developers while using GitHub Projects to organize and assign work and
  reinforce programming, task decomposition, and consistent engineering
  practices.
- Designed and ran a bounded agentic refactor workflow with Codex using frozen
  scopes, baseline tests, and isolated functional and structural reviewers
  against exact commit SHAs.
- Coordinate a GitFlow-based delivery model with `main`, `develop`, work
  branches, and pull requests, aligning parallel development with controlled
  integration.
- Set technical direction across Next.js, React, Java, Python, Docker Compose,
  CI/CD, scripting, and monitoring for the company's internal process platform.
- Open-sourced a Camunda 7 WebSocket/STOMP integration verified by 55 passing
  tests, extracting realtime task invalidation into a reusable library with
  inherited application authentication and Micrometer metrics.

## Evidence gaps

- Add delivery cadence, number of GitHub Project items, completed work per
  iteration, and average lead time.
- Add a concrete before-and-after outcome from coaching or mentoring.
- Add further review responsibilities and concrete technical decisions made
  for the team.
- Confirm the exact terminology used internally for work branches and releases.
