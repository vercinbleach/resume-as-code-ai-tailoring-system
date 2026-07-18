---
id: project-camunda-internal-platform-engineering
name: Camunda Internal Platform Engineering
aliases:
  - Camunda Internal Infrastructure
  - Camunda CI/CD and Observability
type: internal-platform-engineering
organization: Grup Montaner
period: July 2025 - present
status: draft
deployment_status: active-production
sources:
  - github-private:Grup-Montaner/camunda-bpm-montaner
  - archive/previous-cvs/CV Vincenzo 2026 (1).pdf
  - user-confirmed: 2026-07-16
  - user-confirmed: 2026-07-17
evidence_checked: 2026-07-17
related_projects:
  - operational-process-digitalization-platform.md
  - operations-app.md
  - camunda-modeler-fork.md
related_experience:
  - ../experience/grup-montaner-lead-developer.md
---

# Camunda Internal Platform Engineering

## Scope boundary

This file describes the delivery, infrastructure, operational automation, and
observability foundation of Montaner's private Camunda platform. The primary
source is the private `camunda-bpm-montaner` repository.

The business processes and application architecture are documented in
[Operational Process Digitalization Platform](operational-process-digitalization-platform.md).
The separate [Operations App](operations-app.md) has its own Next.js and
SpacetimeDB runtime and production pipeline. The public
[Camunda Modeler Fork](camunda-modeler-fork.md) is also a separate experiment.

## Problem

A production process platform spanning identity, workflow, databases, web
interfaces, supporting Python services, and a Windows RPA worker needed
repeatable environments and controlled delivery. Manual builds and broad cloud
credentials would increase configuration drift and production risk, while
container or workflow failures needed enough evidence for safe diagnosis and
recovery.

## Platform engineering solution

- Reproducible development and production environments based on Docker and
  Docker Compose.
- Selective container builds and production releases through three GitHub
  Actions workflows.
- Ephemeral GitHub Actions runners supplied by AWS CodeBuild.
- Amazon ECR for versioned images and registry-backed Buildx cache.
- Immutable deployment revisions packaged in Amazon S3 and released to EC2
  through AWS CodeDeploy.
- Separate OIDC and IAM trust paths for image reads, main-branch image pushes,
  and production deployments.
- Manual service-scoped or full rollback to images from a selected Git commit.
- Three Codex-assisted controls across the delivery lifecycle: weekly local log
  analysis, automatic pull-request review, and failure-triggered pipeline
  diagnosis.
- Automated deployment-failure classification, bounded retry, evidence capture,
  and guarded escalation to Codex for trusted branches.
- Container health checks, deployment validation, bounded log retention, and
  RPA worker heartbeat monitoring.

## Docker and Docker Compose architecture

Both development and production Compose definitions coordinate ten services:

- Keycloak, its MySQL database, and a one-shot Keycloak initialization service.
- Camunda 7 and its MySQL database.
- A separate MySQL database for business data and the labor-incidents data
  initializer.
- A dedicated MySQL database and Python identifier-generation service.
- The Next.js task portal.

Development builds the application services locally and mounts source or
migration paths where hot reload and iteration require them. Production pulls
six application images from ECR: frontend, backend, identifier service,
labor-incidents component, Keycloak, and Keycloak initialization.

Operational controls visible in the production Compose definition include:

- Health checks for seven services and dependency conditions based on service
  health or successful completion.
- Persistent database volumes and one shared bridge network.
- Restart policies for long-running services and explicit one-shot behavior for
  initialization components.
- Read-only filesystems for the Camunda backend and Next.js frontend, with
  `tmpfs` mounts for required writable paths.
- Docker `json-file` logging with bounded file size and rotation for the backend
  and frontend.
- Build SHA propagation to the frontend for deployment traceability.

## Production CI/CD

### Selective build and release workflow

The main `Deploy production` workflow runs on pushes to `main`, pull requests,
and manual dispatches. It contains three stages:

1. Detect changed services and construct a selective build matrix.
2. Build and validate affected images on pull requests, or build and push
   SHA-tagged and `latest` images from `main`.
3. Deploy only the selected Compose services through the protected production
   path.

The workflow uses Docker Buildx and registry-backed ECR caches. Pull requests
receive build validation without image publication. Main-branch builds use a
separate push-capable role, preventing the general build runner from acquiring
an unintended ECR publication path.

### AWS identity and least-privilege separation

- GitHub Actions assumes AWS roles through OIDC instead of stored long-lived AWS
  access keys.
- Branch and pull-request builds receive ECR read and cache permissions.
- Image publication is restricted to a separate role trusted only for `main`.
- Production deployment uses another role trusted through the GitHub
  `production` environment.
- The deployment role can read image metadata, upload revision bundles to the
  designated S3 path, and create CodeDeploy deployments.
- Legacy broad ECR-push and SSM remote-execution permissions are explicitly
  removed by the provisioning scripts.

### CodeDeploy release mechanics

The workflow packages the production Compose file, Apache virtual-host
configuration, CodeDeploy AppSpec, deployment and validation scripts, and an
environment manifest into an immutable ZIP revision. It uploads the bundle to
S3, verifies the object ETag, and creates a `CodeDeployDefault.OneAtATime`
deployment to EC2.

The deployment script:

- Authenticates Docker to ECR and pulls only the requested services.
- Preserves a bounded set of frontend logs before container replacement.
- Recreates selected services and uses Docker Compose health waiting when the
  installed version supports it.
- Installs the Apache configuration only after `apache2ctl configtest`, restoring
  the previous file if validation fails.
- Reloads Apache gracefully and prints the resulting Compose state.

The post-deploy validation hook checks that each selected container is healthy
or running. Successful one-shot containers are accepted only when they exit
with code zero.

## Rollback and deployment recovery

The separate `Rollback production` workflow is manually dispatched with a
target commit and service selection. It validates the request, confirms that
the corresponding immutable images exist in ECR, rewrites a temporary Compose
revision to the target SHA, and uses the same S3 and CodeDeploy path as a normal
release.

This is controlled manual rollback, not automatic rollback. Service-scoped
rollback avoids replacing unaffected components, while full rollback can use
the production Compose definition stored at the selected commit.

## Three-agent Codex operating model

The platform uses three distinct Codex-assisted mechanisms. They are separate
automations with different triggers, context, and safety boundaries rather than
one open-ended multi-agent loop.

### Agent 1: weekly local frontend-log analyst

A Codex Automation runs once a week on a separate local machine and reviews
custom logs generated on the frontend host. It looks for anomalous behavior,
recurring failures, and issues requiring investigation while a more robust
monitoring approach is being developed.

This automation has persistent memory and a small custom harness that gives the
agent the operating context needed to interpret the frontend logs across runs.
The schedule, memory, harness, and local execution are user-confirmed; their
configuration cannot be inspected from the current machine or GitHub
repository.

The weekly agent is a scheduled detective control, not real-time alerting, and
should not be presented as a replacement for centralized metrics, continuous
log aggregation, or an availability monitor.

### Agent 2: automatic Codex Cloud pull-request reviewer

Codex Cloud is configured through the repository's GitHub integration to review
pull requests automatically when they are opened for review or when a draft is
marked ready. It can also be triggered explicitly with `@codex review`.

This is directly visible in GitHub. Recent PRs such as #218 and #219 contain
automated `Codex Review` submissions and inline findings from
`chatgpt-codex-connector`. The integration supplies change context, reviews the
selected commit, and publishes actionable code-review findings or a positive
reaction when no finding is produced. It forms an AI-assisted quality control
within the repository's CI and delivery process, although its trigger is a
Codex Cloud repository setting rather than a workflow YAML file.

### Agent 3: build and deployment failure diagnostic guardian

The `Deploy production guardian` workflow reacts to failed or timed-out
production workflow runs, including failures in the image build and release
pipeline. It acts as a small custom agent harness around Codex:

- Downloads workflow logs and builds a compact failure context artifact.
- Classifies known registry, Buildx, network timeout, rate-limit, and HTTP 5xx
  patterns as probable transient infrastructure failures.
- Requests at most one automatic rerun for a classified transient failure.
- Locates an associated pull request when one exists and records the evidence
  there.
- Verifies whether the failed branch belongs to the trusted repository before
  allowing automated Codex delegation.
- For trusted non-transient failures, constructs a repository-specific prompt
  with captured evidence and either comments on the existing pull request or
  creates a follow-up fix pull request before requesting Codex investigation.
- For untrusted pull-request heads, records that automatic delegation was
  skipped instead of exposing a privileged remediation path.

This provides evidence of triggers and automation workflows, context
management, custom agent scaffolding, tool integration through GitHub, and
approval-aware safety boundaries. It does not demonstrate an open-ended agent
loop: retry is deliberately bounded and production deployment remains gated.

## Scripting and operational automation

The current repository contains 37 files under its operational script surface,
including 15 shell scripts, eight JavaScript modules, eight JSON policy or
configuration files, two Python scripts, two PowerShell scripts, and one YAML
AppSpec file.

The automation covers:

- Idempotent provisioning of CodeBuild runner integration, ECR repositories and
  lifecycle policy, CodeDeploy resources, S3 revision access, IAM policies, and
  GitHub OIDC trust documents.
- Creation and maintenance of the CodeBuild GitHub Actions webhook.
- Selective container build, ECR publication, deployment packaging, health
  waiting, and post-deploy validation.
- BPMN deployment to production.
- Local frontend startup and short-lived Camunda token acquisition.
- SQL Server tunneling for development access.
- Certified-communications testing and certificate retrieval.
- Camunda task-race, realtime, and SSE comparison tooling.
- A restricted `sudo` helper that permits an operations user to read only
  approved Docker Compose logs rather than granting general Docker access.

## Observability and operational reliability

The repository demonstrates operational observability rather than a complete
metrics platform:

- Compose health checks and dependency-aware startup for databases, Keycloak,
  Camunda, and supporting services.
- CodeDeploy deployment waiting and an independent validation hook.
- Bounded Docker log rotation and preservation of recent frontend logs during
  replacement.
- A restricted operational log-access helper.
- RPA worker heartbeats, backend status tracking, a monitoring BPMN process,
  structured worker logging, and diagnostic screenshots on automation failures.
- Live task updates through Server-Sent Events plus dedicated stress and
  comparison tools for realtime behavior.
- Deployment guardian artifacts and pull-request comments for failed-release
  evidence.
- Custom frontend-host logs reviewed by a weekly local Codex Automation with
  persistent memory and a small interpretation harness.

No Prometheus, Grafana, OpenTelemetry, centralized log aggregation, formal SLO,
or uptime-alerting configuration was found in the inspected repository. A more
robust monitoring approach is currently under development.

## My contribution

- Designed and implemented the production CI/CD and operational foundation for
  the Camunda platform.
- Containerized and coordinated the ten-service development and production
  environment.
- Built selective multi-image pipelines, OIDC role separation, ECR caching and
  publication, S3 revision packaging, and CodeDeploy releases to EC2.
- Implemented service-scoped manual rollback and post-deploy container
  validation.
- Configured automatic Codex Cloud review for opened pull requests in the
  repository's delivery process.
- Built a weekly local Codex Automation with memory and a custom harness for
  reviewing frontend-host logs.
- Developed the failure-triggered deployment guardian and its guarded Codex
  follow-up workflow.
- Created AWS provisioning, developer tooling, production BPMN deployment,
  integration-testing, and restricted log-access scripts.
- Implemented RPA health reporting and contributed to container health checks,
  bounded logs, and operational diagnostics.

## GitHub evidence of contribution

- The private repository contains 891 commits in the inspected history, 455 of
  which are attributed to the author's `Vincenzo` identities.
- Across the infrastructure scope used for this entry, Git records 152 unique
  commits, of which 113 are attributed to those identities between September 5,
  2025 and July 16, 2026.
- Git attributes 17 of 18 workflow commits, all nine CI-provisioning commits,
  all five CodeDeploy-script commits, 46 of 65 development-Compose commits, and
  22 of 30 production-Compose commits to those identities.
- The same contribution history spans Keycloak initialization, Dockerfiles,
  developer utilities, and operational log access.
- GitHub exposes a successful AWS CodeBuild status for each of the ten most
  recent commits between July 9 and July 16, 2026. These executions span five
  active delivery days, including four successful statuses on July 16.
- That sample confirms frequent successful CI and runner activity. It is not
  recorded as ten successful production deployments because the available
  connector does not expose the complete GitHub Actions and CodeDeploy run
  history.

## Outcome

- Standardized a ten-service platform across development and production.
- Established selective validation and release paths for six production
  application images.
- Replaced broad, manual production delivery with immutable SHA-tagged images,
  least-privilege OIDC roles, S3 revisions, one-at-a-time CodeDeploy releases,
  and verified container state.
- Added controlled service-level rollback without requiring a rebuild of the
  selected historical images.
- Reduced unattended failure handling risk through bounded retry, trust checks,
  captured evidence, and guarded Codex escalation.
- Established three AI-assisted controls across operations and delivery:
  memory-backed weekly frontend-log analysis, automatic pull-request review,
  and pipeline-failure diagnosis.
- Improved operational diagnosis through health checks, bounded logs, retained
  pre-replacement frontend logs, RPA heartbeats, and restricted log access.
- Recorded at least ten successful AWS CodeBuild statuses across five active
  delivery days in the latest eight-day GitHub sample.
- No verified deployment-frequency, lead-time, failure-rate, recovery-time,
  availability, or manual-time-saving metric is documented yet.

## Technologies

- Containers and runtime: Docker, Docker Compose, Docker Buildx, Linux, Apache,
  EC2, read-only filesystems, `tmpfs`, health checks, and JSON log rotation
- CI/CD: GitHub Actions, AWS CodeBuild GitHub Actions runners, selective build
  matrices, ECR build cache, Amazon ECR, Amazon S3, AWS CodeDeploy, AppSpec, and
  immutable Git SHA image tags
- Cloud security: GitHub OIDC, AWS IAM roles and policies, environment-scoped
  trust, least-privilege separation, and ECR lifecycle policies
- Automation: Bash, PowerShell, Python, JavaScript, AWS CLI, GitHub CLI, Docker
  Compose CLI, and PuTTY/Plink-based remote operations
- Observability and reliability: container health checks, CodeDeploy validation,
  Docker logs, RPA heartbeat monitoring, diagnostic screenshots, SSE stress
  tooling, custom frontend-host logs, and deployment-failure artifacts
- AI-assisted operations: Codex Automations, persistent agent memory, custom
  harnesses, Codex Cloud GitHub reviews, GitHub workflow triggers,
  failure-context assembly, transient-failure classification, bounded reruns,
  guarded Codex delegation, and follow-up pull-request scaffolding

## Reusable resume bullets

- Engineered a ten-service Camunda production platform and six-image release
  pipeline using Docker Compose, GitHub Actions, CodeBuild, ECR, S3, CodeDeploy,
  and EC2.
- Implemented three production workflows for selective delivery, service-scoped
  rollback, and automated failure triage using immutable Git SHA images,
  least-privilege AWS OIDC roles, and post-deploy health validation.
- Implemented a guarded agentic deployment workflow with Codex that captures evidence,
  classifies transient infrastructure failures, performs one bounded retry,
  and scaffolds trusted follow-up pull requests for non-transient failures.
- Integrated three Codex-assisted controls across the delivery lifecycle:
  memory-backed weekly frontend-log review, automatic pull-request review, and
  evidence-backed pipeline-failure diagnosis.

## Public-repository evidence boundary

The public `camunda-modeler-interno` branch contains inherited GitHub Actions
workflows for the upstream desktop modeler. Those workflows are not used as
evidence of personal ownership for this entry. All detailed evidence above
comes from the private Montaner platform repository and user confirmation.

## Related project network

- [Operational Process Digitalization Platform](operational-process-digitalization-platform.md)
  describes the business workflows and application architecture running on this
  foundation.
- [Operations App](operations-app.md) is a separate Next.js and SpacetimeDB
  system with its own deployment architecture.
- [Collaborative Camunda Modeler Fork](camunda-modeler-fork.md) describes the
  separate public modeler experiment.
- [Lead Software Engineer role](../experience/grup-montaner-lead-developer.md) describes
  the team, planning, and GitFlow delivery process.

## Evidence gaps

- Replace the recent CI-status sample with complete deployment frequency, build
  and deployment duration, change-failure rate, mean recovery time, and
  availability when full Actions or CodeDeploy history becomes accessible.
- Record the selected external uptime, alerting, infrastructure-metrics, or log
  aggregation stack when the more robust monitoring work is implemented.
- Add the local weekly agent's schedule, memory structure, harness design, and
  custom frontend-log schema when the separate machine becomes available for
  inspection.
- Confirm whether the GitHub `production` environment currently requires human
  reviewers and whether `main` branch protection is enforced.
- Confirm whether the deployment guardian has already produced successful
  automatic reruns or Codex follow-up pull requests in live operation.
