---
id: project-camunda-websocket-task-events
name: Camunda WebSocket Task Events
type: open-source-library
period: July 2026 - present
status: pre-release
version: 0.1.0-SNAPSHOT
repository: https://github.com/vercinbleach/camunda-websocket-task-events
license: Apache-2.0
distribution_status: source-public-not-on-maven-central
adoption_status: no-users-reported
ci_status: passing
verified_test_count: 55
product_goal: plug-and-play-realtime-collaboration-for-camunda-7
intended_scope: camunda-7-spring-boot-applications
sources:
  - github:vercinbleach/camunda-websocket-task-events
  - user-confirmed: 2026-07-17
  - local-verification: mvnw verify, 2026-07-17
evidence_checked: 2026-07-17
related_projects:
  - operational-process-digitalization-platform.md
  - opensource-contributions.md
related_experience:
  - ../experience/grup-montaner-lead-developer.md
---

# Camunda WebSocket Task Events

## Scope boundary

Camunda WebSocket Task Events is a standalone Apache-2.0 Java library created
and maintained by Vincenzo Rosciano. It provides a plug-and-play realtime
collaboration layer for Camunda 7 applications built with Spring Boot by turning
task events into minimal WebSocket/STOMP invalidations.

The project originates from the need to replace custom SSE infrastructure in
the internal Process Digitalization Platform, but it is a separate public
repository and is designed as a reusable integration rather than company-only
application code.

It is currently a pre-release project. The code is public and its CI and local
test suite pass, but version `0.1.0-SNAPSHOT` has no tag or GitHub release, is
not published to Maven Central, and has no reported users yet. It targets
Camunda 7.24.x and Spring Boot 3.5.x, while the currently documented internal
platform uses Camunda 7.23 and Spring Boot 3.4.4. Production replacement of that
platform's SSE path is therefore not claimed.

## Problem

Camunda 7 Community does not provide the intended shared realtime task
experience out of the box. When several users are authorized to work on the
same task, one user can claim, complete, reassign, or otherwise change it while
the others continue seeing stale state. They may then attempt work that is no
longer available or act on an outdated task list, creating collisions and a
poor collaborative experience.

Realtime task interfaces therefore need to react immediately when Camunda
creates, assigns, updates, or completes work. A custom SSE endpoint can solve
the immediate UI problem, but every application must then maintain its own
transport, proxy, security, connection-management, concurrency, and
observability code.

A richer WebSocket event payload would create a second task data API and risk
duplicating authorization logic or exposing task identifiers, assignees,
variables, tokens, or business data. Events can also occur before the Camunda
transaction commits, so publishing too early can tell clients to reload state
that was later rolled back.

## Solution

The intended product experience is plug and play for Camunda 7 Spring Boot
builds: add one Maven dependency and the library auto-configures a native
WebSocket/STOMP endpoint for task-list invalidation without requiring a second
task API or application-specific authentication implementation.

When a committed task change occurs, every connected user receives a minimal
invalidation and reloads the tasks they are currently authorized to see. This
keeps clients aligned around the latest Camunda state and reduces the window in
which multiple eligible users can unknowingly act on the same stale task.

The library:

- Registers `/ws/task-events` as the default WebSocket endpoint.
- Exposes a private `/user/queue/task-events` STOMP subscription for each
  authenticated or routing-scoped session.
- Listens to Camunda Spring Boot `TaskEvent` objects and publishes only after
  the surrounding transaction commits.
- Sends a versioned two-field envelope:
  `{"schemaVersion":1,"type":"TASKS_INVALIDATED"}`.
- Omits task IDs, variables, assignees, credentials, and business data.
- Keeps Camunda REST and its authorization model as the source of truth; the
  browser reconciles its authorized task state after each invalidation and
  after reconnecting.
- Coalesces event bursts on a bounded executor so a burst can trigger one
  invalidation rather than one message per internal task event.
- Treats realtime delivery as best effort so publication failures do not roll
  back or change the result of a Camunda command.

The WebSocket layer improves shared awareness but does not replace Camunda's
command-level concurrency and authorization controls. If two commands still
race, the process engine and REST API remain responsible for accepting one
valid transition and rejecting or reconciling the stale action.

## Security model

The library reuses authentication already configured by the host application
instead of introducing Keycloak-, issuer-, audience-, or claim-specific
configuration:

- Carries an HTTP-session or login `Principal` into the WebSocket session.
- Reuses the application's `JwtDecoder` and authentication converter for
  stateless JWT bearer tokens supplied in STOMP `CONNECT`.
- Supports Spring Resource Server opaque-token introspection.
- Adapts Camunda REST's `AuthenticationProvider` when the handshake uses its
  existing HTTP authentication path.
- Allows a deliberately anonymous application to receive a random,
  session-local routing principal that grants no Camunda or REST permissions.
- Supports ordered custom credential or handshake authenticators for genuinely
  custom application security.

Invalid and unsupported credentials fail closed. Ambiguous bearer
authentication is rejected rather than guessed, token expiry closes the
session, browser `SEND` is denied, and clients may subscribe only to the task
invalidation destination. Origin wildcards are rejected; an empty allowlist
retains Spring's same-origin behavior.

## Reliability, limits, and observability

- `@TransactionalEventListener(AFTER_COMMIT)` prevents invalidations from
  escaping rolled-back Camunda commands.
- The publisher coalesces concurrent bursts and recovers to a retryable state
  when its bounded executor rejects work.
- Realtime delivery is explicitly non-durable and has no replay; reconnecting
  clients reconcile through REST.
- Configurable defaults include a 10-second first-message timeout and
  heartbeat, 500 sessions, one subscription per session, a 64 KiB message
  limit, a 512 KiB send buffer, and a 10-second send-time limit.
- Micrometer instruments committed events, emitted envelopes, rejected
  subscriptions and authentications, delivery failures, publisher rejection,
  active transports, and active subscriptions under the `task_realtime_`
  prefix.
- Logging deliberately avoids task, user, credential, and payload details on
  security and delivery failures.

## Compatibility and distribution

The first declared compatibility target is:

| Component | Target |
| --- | --- |
| Java | 17+ |
| Camunda Platform 7 | 7.24.x |
| Spring Boot | 3.5.x |
| Spring Framework | 6.2.x |

The Maven coordinates are
`io.github.vercinbleach:camunda-websocket-task-events:0.1.0-SNAPSHOT`. The
artifact must currently be installed locally with the included Maven wrapper.
The architecture is intended to be reusable across Camunda 7 Spring Boot
applications, while the broader version matrix still requires verification
beyond the first declared 7.24.x and 3.5.x target.

## Quality evidence

- The repository contains 33 production Java source files and 19 Java test
  files across 63 tracked files.
- `mvn verify` compiled the library and executed 55 tests with zero failures,
  errors, or skipped tests on Java 17.
- Coverage includes Camunda transaction commit and rollback behavior, event
  coalescing, private broadcasting, protocol restrictions, session limits,
  metrics, origin and configuration validation, JWT and opaque-token adapters,
  Camunda REST authentication, and auto-configuration behavior.
- A full embedded-server test authenticates a stateless JWT through STOMP and
  exercises the WebSocket path end to end.
- GitHub Actions runs the Maven verification on Java 17 for pushes to `main`
  and pull requests. The latest five visible runs, including the current head,
  completed successfully after the initial workflow setup was corrected.
- All six repository commits at the inspected head are authored by Vincenzo
  Rosciano.

## My contribution

- Conceived the library from a production-platform need and extracted the
  realtime concern into a reusable public component.
- Defined the product as a plug-and-play collaborative task layer for Camunda 7
  Spring Boot applications, focused on keeping multiple eligible users aligned
  when they share access to the same work.
- Designed the minimal invalidation contract so WebSocket transport does not
  become a second Camunda task API.
- Implemented Spring Boot auto-configuration, WebSocket/STOMP transport,
  after-commit publication, private-user broadcasting, event coalescing,
  session tracking, configurable limits, and Micrometer metrics.
- Designed zero-configuration security inheritance across Spring Security JWT,
  opaque tokens, established HTTP principals, and Camunda REST authentication,
  with fail-closed behavior and extension interfaces for custom mechanisms.
- Built the 55-test suite, Maven wrapper workflow, GitHub Actions CI, public
  documentation, browser integration example, Maven metadata, and Apache 2.0
  licensing.

## Outcome

- Open-sourced the first concrete plugin from the broader Camunda 7 extension
  initiative.
- Addressed the stale-task collaboration gap for users who can access the same
  Camunda work by broadcasting committed changes and reconciling every client
  against the latest authorized REST state.
- Replaced a task-data event stream with a two-field invalidation protocol that
  keeps authorization and business state behind Camunda REST.
- Produced a verified pre-release library with 55 passing tests and green CI.
- Established a reusable security and observability baseline for introducing
  WebSocket task invalidation without application-specific token handling.
- No adoption, production deployment, external contribution, package download,
  or user-impact metric is claimed yet.

## Technologies

- Java 17 and Maven
- Camunda Platform 7.24 and Camunda Spring Boot eventing
- Spring Boot 3.5 and Spring Framework 6.2
- Spring WebSocket, STOMP, private user destinations, and simple broker
- Spring Security, JWT, OAuth 2.0 Resource Server, and opaque-token
  introspection
- Camunda REST `AuthenticationProvider`
- Transactional event listeners and bounded Java executors
- Micrometer
- JUnit 5, AssertJ, Mockito, Spring Boot Test, H2, and embedded Tomcat
- GitHub Actions and Apache License 2.0

## Structured claims

<!-- structured-claims:start -->
```json
{
  "schema_version": 1,
  "claims": [
    {
      "id": "claim-camunda-websocket-authored-library",
      "statement": "Vincenzo created and maintains the public Apache-2.0 Camunda WebSocket Task Events library.",
      "dimensions": ["open-source", "product", "technical"],
      "technologies": ["Java", "Camunda Platform 7", "Spring Boot", "WebSocket", "STOMP"],
      "evidence": [
        {
          "source_type": "repository-verified",
          "locator": "github:vercinbleach/camunda-websocket-task-events",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "public",
      "aliases": ["Camunda realtime collaboration plugin", "Camunda WebSocket plugin"],
      "caveats": ["The library remains pre-release and is not published to Maven Central."]
    },
    {
      "id": "claim-camunda-websocket-fifty-five-tests",
      "statement": "The library passed 55 tests with zero failures, errors, or skipped tests on Java 17 and has green GitHub Actions CI.",
      "dimensions": ["impact", "open-source", "reliability", "technical"],
      "technologies": ["Java 17", "JUnit 5", "Maven", "GitHub Actions"],
      "evidence": [
        {
          "source_type": "local-verification",
          "locator": "mvnw verify: 2026-07-17",
          "checked": "2026-07-17"
        },
        {
          "source_type": "repository-verified",
          "locator": "GitHub Actions run 29581900547",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "public",
      "aliases": ["55 passing tests", "green CI"],
      "caveats": []
    },
    {
      "id": "claim-camunda-websocket-minimal-invalidation",
      "statement": "The library broadcasts a versioned two-field task invalidation after transaction commit and keeps task data behind authorized Camunda REST reconciliation.",
      "dimensions": ["product", "reliability", "security", "technical"],
      "technologies": ["Camunda Platform 7", "Spring WebSocket", "STOMP", "Camunda REST"],
      "evidence": [
        {
          "source_type": "repository-verified",
          "locator": "github repository implementation and README",
          "checked": "2026-07-17"
        },
        {
          "source_type": "local-verification",
          "locator": "mvnw verify: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "public",
      "aliases": ["TASKS_INVALIDATED", "after-commit invalidation"],
      "caveats": ["Realtime delivery is best effort and clients reconcile through REST after reconnecting."]
    },
    {
      "id": "claim-camunda-websocket-security-inheritance",
      "statement": "The library inherits host-application authentication for HTTP principals, JWT, opaque tokens, and Camunda REST while failing closed on invalid or ambiguous credentials.",
      "dimensions": ["security", "technical"],
      "technologies": ["Spring Security", "JWT", "OAuth 2.0 Resource Server", "Camunda REST"],
      "evidence": [
        {
          "source_type": "repository-verified",
          "locator": "commit bffbea90621b23df9ed0e2502c7886327d49a4db",
          "checked": "2026-07-17"
        },
        {
          "source_type": "local-verification",
          "locator": "security and end-to-end test suite: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "public",
      "aliases": ["zero-configuration authentication", "fail-closed authentication"],
      "caveats": []
    },
    {
      "id": "claim-camunda-websocket-observability-limits",
      "statement": "The library includes bounded event coalescing, configurable session and transport limits, privacy-conscious logging, and Micrometer metrics.",
      "dimensions": ["reliability", "security", "technical"],
      "technologies": ["Java executors", "Micrometer", "Spring WebSocket"],
      "evidence": [
        {
          "source_type": "repository-verified",
          "locator": "github repository implementation and README",
          "checked": "2026-07-17"
        },
        {
          "source_type": "local-verification",
          "locator": "mvnw verify: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "public",
      "aliases": ["event coalescing", "task_realtime_ metrics"],
      "caveats": ["Load-test results for connection scale, latency, and memory use have not been recorded."]
    },
    {
      "id": "claim-camunda-websocket-no-adoption-yet",
      "statement": "The public pre-release library has no reported users, production deployments, releases, or package downloads yet.",
      "dimensions": ["impact", "open-source", "product"],
      "technologies": [],
      "evidence": [
        {
          "source_type": "repository-verified",
          "locator": "github repository state: 2026-07-17",
          "checked": "2026-07-17"
        },
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "public",
      "aliases": ["pre-release", "no users reported"],
      "caveats": ["Do not imply production adoption or external usage."]
    },
    {
      "id": "claim-camunda-websocket-internal-sse-replacement",
      "statement": "The public library has replaced the internal platform's existing SSE implementation in production.",
      "dimensions": ["impact", "operations", "product", "technical"],
      "technologies": ["Camunda Platform 7", "Server-Sent Events", "WebSocket"],
      "evidence": [
        {
          "source_type": "repository-verified",
          "locator": "public library compatibility target and internal platform version comparison",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "unverified",
      "resume_safe": false,
      "sensitivity": "internal-anonymized",
      "aliases": ["production SSE replacement"],
      "caveats": ["The public library targets Camunda 7.24 and Spring Boot 3.5, while the documented internal platform uses Camunda 7.23 and Spring Boot 3.4.4; replacement is not claimed."]
    }
  ],
  "evidence_gaps": [
    {
      "id": "gap-camunda-websocket-compatibility-matrix",
      "question": "Which additional Camunda 7 and Spring Boot version combinations pass the full test suite?",
      "importance": "medium",
      "status": "open",
      "affects_claims": ["claim-camunda-websocket-authored-library"]
    },
    {
      "id": "gap-camunda-websocket-load-tests",
      "question": "What connection count, event burst, publication latency, memory, and reconnect results does load testing produce?",
      "importance": "high",
      "status": "open",
      "affects_claims": ["claim-camunda-websocket-observability-limits"]
    },
    {
      "id": "gap-camunda-websocket-internal-validation",
      "question": "Has the library been validated against or deployed to the internal Camunda 7.23 and Spring Boot 3.4.4 platform?",
      "importance": "high",
      "status": "open",
      "affects_claims": ["claim-camunda-websocket-internal-sse-replacement"]
    },
    {
      "id": "gap-camunda-websocket-adoption",
      "question": "When does the project receive its first release, external user, download, contribution, or production deployment?",
      "importance": "medium",
      "status": "open",
      "affects_claims": ["claim-camunda-websocket-no-adoption-yet"]
    }
  ]
}
```
<!-- structured-claims:end -->

## GitHub evidence

- [Repository](https://github.com/vercinbleach/camunda-websocket-task-events)
- [Initial implementation](https://github.com/vercinbleach/camunda-websocket-task-events/commit/ef489b957731efe65fe139f7a9bdf5212563307c)
- [Application security inheritance](https://github.com/vercinbleach/camunda-websocket-task-events/commit/bffbea90621b23df9ed0e2502c7886327d49a4db)
- [Current successful CI run](https://github.com/vercinbleach/camunda-websocket-task-events/actions/runs/29581900547)
- [README and integration contract](https://github.com/vercinbleach/camunda-websocket-task-events/blob/main/README.md)
- [Apache 2.0 license](https://github.com/vercinbleach/camunda-websocket-task-events/blob/main/LICENSE)

## Reusable resume bullets

- Open-sourced a Camunda 7 WebSocket/STOMP integration verified by 55 passing
  tests, using after-commit invalidations, bounded burst coalescing, inherited
  Spring and Camunda authentication, session limits, and Micrometer metrics.
- Built a plug-and-play realtime collaboration layer for Camunda 7 Spring Boot
  task lists, keeping users with access to the same work synchronized through
  committed invalidations and authorized REST reconciliation.
- Reduced realtime task-event exposure to a two-field versioned invalidation
  envelope, keeping task IDs, variables, assignees, tokens, and business data
  behind authorized Camunda REST reconciliation.
- Built zero-configuration authentication inheritance for HTTP principals,
  JWT, opaque tokens, and Camunda REST, with fail-closed credential handling and
  an end-to-end stateless JWT-over-STOMP test.

## Related project network

- [Operational Process Digitalization Platform](operational-process-digitalization-platform.md)
  contains the existing SSE implementation and the wider three-plugin Camunda
  extension initiative from which this public library emerged.
- [Open Source Contributions](opensource-contributions.md) provides the summary
  view across authored public projects and upstream contributions.
- [Lead Software Engineer role](../experience/grup-montaner-lead-developer.md) contains
  the broader technical-leadership context.

## Evidence gaps

- Publish the first version to Maven Central and record its stable coordinates,
  tag, release notes, and compatibility matrix.
- Verify the plug-and-play claim across additional Camunda 7 and Spring Boot
  version combinations beyond the first supported target.
- Validate compatibility with the internal Camunda 7.23 and Spring Boot 3.4.4
  platform or complete its upgrade before claiming an SSE replacement there.
- Add load-test results for connection count, event bursts, publication
  latency, memory use, and reconnect behavior.
- Record external users, downloads, stars, forks, issues, pull requests, or
  production deployments when adoption begins.
