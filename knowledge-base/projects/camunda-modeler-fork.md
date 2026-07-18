---
id: project-camunda-modeler-fork
name: Collaborative Camunda Modeler Fork
aliases:
  - Collaborative BPMN Workspace
type: open-source-fork
period: June 2026 - present
status: paused
pause_reason: higher-priority-projects
initiative_type: self-directed-internal-developer-tooling
prototype_status: working-branch-merge-partial-integration
deployment_status: local-only
branch_workflow_status: functional
shared_cloud_status: not-deployed
stakeholder_rollout_status: planned
bpmn_main_deploy_status: repository-pipeline-confirmed
product_scope: internal-collaborative-bpmn-workspace
repository: https://github.com/vercinbleach/camunda-modeler-interno
sources:
  - github:vercinbleach/camunda-modeler-interno
  - user-confirmed: 2026-07-17
evidence_checked: 2026-07-17
related_projects:
  - operational-process-digitalization-platform.md
  - camunda-internal-platform-engineering.md
related_experience:
  - ../experience/grup-montaner-lead-developer.md
---

# Collaborative Camunda Modeler Fork

## Scope boundary

This project is an internal collaborative workspace for the BPMN diagrams used
by Grup Montaner's Camunda 7 process platform. It starts from the upstream
Camunda Modeler desktop codebase but explores a shared web and cloud workflow
rather than remaining only a customized desktop editor.

It is not part of the Operations Outsourcing App and is not an AI conversation
product that generates forms from natural language. Its current purpose is
visual, collaborative BPMN authoring and governance. An AI modeling harness is
a possible future direction, not a feature of the present prototype.

This is a self-directed internal developer-tooling initiative created by the
project owner. Work is currently paused while higher-priority company projects
are delivered.

## Problem

Local Modeler files make collaboration difficult. Several people need to edit,
review, and understand the same business-process diagrams without exchanging
uncontrolled copies or losing track of which version should reach production.

The intended audience extends beyond the engineering team. The workspace is
being designed so BPMN-capable business stakeholders, including the company's
co-CEO, can draw, review, and contribute directly alongside developers and
other employees.

The environment also runs Camunda 7, so the editor must prevent Camunda 8 or
Zeebe-specific models from entering the workflow accidentally.

## Product vision

The product applies GitHub-style collaboration to BPMN diagrams:

1. Contributors work on their own diagram branches. This branch workflow is
   already functional according to the project owner.
2. Changes can be merged into the main diagram version. This merge workflow is
   also functional.
3. BPMN changes merged into the Camunda repository's `main` branch have a
   production path: the existing workflow detects changes under `backend/`,
   rebuilds the backend image, and deploys it through ECR and CodeDeploy.
4. Instant visibility of the shared main version in a common cloud workspace is
   planned but not yet deployed.
5. Access for the co-CEO and other employees is planned for a later rollout.

The branch and merge workflow works, while the shared cloud experience and
broader stakeholder rollout remain incomplete. The exact bridge that writes
Modeler changes into the production Camunda repository was not found in the
fork, so the complete editor-to-production path is not claimed as verified end
to end.

## Implemented prototype

- A Vite and React 18 web MVP renders a Camunda 7 BPMN editor through
  `camunda-bpmn-js` and `camunda-bpmn-moddle`.
- The runnable web route loads and saves diagrams through a process-document
  service. In the inspected snapshot, that service persists XML in browser
  `localStorage`, not in SpacetimeDB.
- A reusable TypeScript `BpmnCanvas` captures modeling commands, serializes safe
  command metadata, emits XML snapshots, accepts remote events, and renders
  remote-selection overlays.
- The canvas can publish snapshots every 25 commands or every 30 seconds through
  an injected collaboration adapter.
- The desktop client contains an optional `SpacetimeDocumentSync` layer for
  loading snapshots and later events, queuing local changes, retrying after
  disconnects, creating periodic snapshots, and blocking edits after revision
  divergence.
- A collaboration-session guard orders remote events by revision, queues gaps,
  acknowledges events produced by the current client, ignores stale events,
  and detects conflicts when two changes touch the same BPMN element.
- Presence and remote-selection components represent collaborators and their
  selected diagram elements.
- A Rust 2021 SpacetimeDB 1.0 module provides shared workspaces, projects,
  processes, BPMN documents, ordered events, snapshots, published revisions,
  presence, and workspace roles.
- The desktop fork removes DMN, Forms, RPA, Camunda 8, and Zeebe providers from
  the active tab workflow. It rejects BPMN files containing Zeebe namespaces or
  Camunda 8 execution-platform metadata with an explicit compatibility error.

## Current integration state

The repository contains the major collaboration pieces, but they are not yet
connected as one complete product in the inspected `develop` branch:

- The visible Vite MVP uses `BpmnProcessEditor`, while the collaboration-capable
  `BpmnCanvas` exists as a separate component.
- The Vite process-document service saves to `localStorage`.
- The desktop sync layer expects a SpacetimeDB client to be injected through
  application globals, but concrete client creation and generated bindings were
  not found in the inspected feature surface.
- The Rust module has revision and published-version concepts, but it does not
  yet model Git-style diagram branches, pull requests, or merge operations.
- The project owner confirms that diagram branches and merge work today, which
  indicates that branch governance is handled outside the current SpacetimeDB
  schema or through another integration layer.
- The Camunda application repository confirms that backend changes pushed to
  `main` trigger its production workflow. Because BPMN definitions live under
  the backend resources directory, the repository has a working BPMN production
  delivery path.
- The fork does not yet provide a deployed shared cloud workspace, and neither
  the co-CEO nor other non-development stakeholders have access yet.

This is therefore a substantive local prototype with functional branch and
merge behavior, but not yet a deployed multi-user cloud product.

## Collaboration and versioning design

- `Workspace`, `Project`, `Process`, and `ProcessDocument` organize diagrams.
- `DocumentEvent` assigns ordered revisions to changes.
- `DocumentSnapshot` stores periodic full BPMN XML states.
- `ProcessDocument` tracks current and published revisions.
- `DocumentPresence` records collaborator activity and selections.
- Workspace roles include owner, administrator, editor, and viewer, with
  server-side permission checks for editing and publication.
- Client guards detect missing revisions, stale events, local acknowledgements,
  late non-conflicting changes, element conflicts, and changes requiring rebase.

## Product and engineering scope in GitHub

- Git attributes 15 fork-specific commits on June 23, 2026 to `Vincenzo
  Rosciano` or `vercinbleach`: seven implementation commits and eight merge or
  integration commits.
- Seven feature pull requests were merged into the fork's `develop` branch.
- The current collaboration-specific surface contains 16 files and 1,902 lines
  across the web canvas, desktop synchronization, collaboration guard, presence
  UI, tests, and Rust module.
- The Rust module defines eight SpacetimeDB tables and ten reducers.
- The collaboration guard has six focused Mocha and Chai tests covering outgoing
  revision metadata, strict remote ordering, own-event acknowledgement,
  non-conflicting late changes, element conflicts, and rebase signaling.
- The inherited upstream Camunda history is not counted as personal contribution.

## My contribution

- Forked Camunda Modeler and built the initial web BPMN editing workspace.
- Implemented the standalone BPMN canvas and collaboration adapter contract.
- Designed event ordering, snapshot, retry, offline, divergence, conflict, and
  presence behavior for collaborative diagram sessions.
- Built the Rust SpacetimeDB data model and reducers for workspaces, roles,
  diagrams, events, snapshots, presence, and published revisions.
- Added desktop-client synchronization hooks and status feedback.
- Restricted the active modeler workflow to Camunda 7 BPMN and added explicit
  rejection of Camunda 8 and Zeebe diagrams.
- Integrated the work through seven feature pull requests on the fork.
- Conceived and drove the initiative independently to improve the internal
  developer experience around BPMN modeling and governance.

## Outcome

- Demonstrated a browser-based Camunda 7 BPMN editing MVP.
- Established a functional diagram branch and merge workflow for collaborative
  BPMN development.
- Established the data and client-side foundations for ordered real-time diagram
  collaboration, snapshots, presence, permissions, and conflict detection.
- Connected the product direction to the existing Camunda repository pipeline,
  where backend changes merged into `main` trigger production delivery.
- Created an access path intended to include engineering, BPMN-capable business
  employees, and the company's co-CEO in process design.
- No verified internal deployment, active-user count, simultaneous-editor test,
  synchronization latency, or shared cloud workspace is recorded yet.

## Technologies

- Upstream platform: Camunda Modeler, Electron 39, npm workspaces
- BPMN: BPMN 2.0, Camunda 7, `camunda-bpmn-js`, `bpmn-js`,
  `camunda-bpmn-moddle`, properties panel, diagram overlays
- Web: React 18, Vite, JavaScript, TypeScript, CSS
- Collaboration backend: Rust 2021, SpacetimeDB 1.0, tables, reducers,
  identities, roles, event revisions, snapshots, presence
- Synchronization: WebSocket-oriented adapter contracts, ordered events,
  snapshotting, retry queues, divergence guards, conflict detection
- Quality: Mocha, Chai, ESLint, six collaboration-session tests
- Delivery workflow: Git branches and pull requests for prototype development;
  diagram branching and merge are functional, while the shared cloud workspace
  remains a product goal

## GitHub evidence

- [Repository](https://github.com/vercinbleach/camunda-modeler-interno)
- [Standalone BPMN canvas](https://github.com/vercinbleach/camunda-modeler-interno/commit/8da00df1)
- [Web BPMN editor MVP](https://github.com/vercinbleach/camunda-modeler-interno/commit/fbc57fef)
- [Canvas collaboration synchronization](https://github.com/vercinbleach/camunda-modeler-interno/commit/ecf0f1c6)
- [SpacetimeDB Rust module](https://github.com/vercinbleach/camunda-modeler-interno/commit/31d2f44e)
- [Desktop document synchronization](https://github.com/vercinbleach/camunda-modeler-interno/commit/2f765299)
- [Revision guard, tests, and presence](https://github.com/vercinbleach/camunda-modeler-interno/commit/2313816b)
- [Camunda 7 compatibility restriction](https://github.com/vercinbleach/camunda-modeler-interno/commit/24eb9c57)

## Reusable resume bullets

- Built a collaborative Camunda 7 BPMN prototype across 16 feature files,
  implementing eight SpacetimeDB tables, ten Rust reducers, ordered revisions,
  snapshots, presence, and element-level conflict detection.
- Established a functional branch and merge workflow for BPMN development and
  designed its promotion model around an existing `main`-triggered Camunda
  production pipeline.
- Extended Camunda Modeler with a React and Vite web editor, desktop
  synchronization hooks, remote-selection overlays, offline retry, divergence
  guards, and six focused collaboration tests.
- Designed the remaining shared-cloud and stakeholder experience for a
  GitHub-style BPMN workspace; the initiative is paused while higher-priority
  company projects are delivered.

## Related project network

- [Operational Process Digitalization Platform](operational-process-digitalization-platform.md)
  supplies the Camunda 7 processes that this workspace is intended to govern.
- [Camunda Internal Platform Engineering](camunda-internal-platform-engineering.md)
  contains the existing backend-image and CodeDeploy pipeline triggered when
  BPMN changes reach the Camunda repository's `main` branch; the Modeler-to-Git
  bridge still needs to be documented.
- [Lead Software Engineer role](../experience/grup-montaner-lead-developer.md) contains
  the engineering-team and stakeholder context.

## Future direction

After the collaborative workspace and governance workflow are stable, a future
agent harness could expose the modeler to AI tools so an agent can create or
modify BPMN diagrams. This is a roadmap possibility only. The current project
does not claim natural-language modeling, AI-generated forms, or autonomous
production deployment.

## Evidence gaps

- Identify the implementation that connects the Modeler branch and merge
  workflow to the `camunda-bpm-montaner` repository.
- Define whether diagram branches are Git branches, external workflow entities,
  or a hybrid with SpacetimeDB revisions.
- Add the planned resume criteria and hosting architecture for the shared cloud
  workspace when the initiative is reprioritized.
- Add the number of simultaneous editors, tested diagram size, synchronization
  latency, and conflict scenarios once end-to-end collaboration is connected.
- Confirm whether the upstream Electron desktop shell remains part of the final
  product or only serves as a source of reusable modeler components.
