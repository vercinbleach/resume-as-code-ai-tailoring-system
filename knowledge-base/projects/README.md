# Project knowledge base

This folder contains one canonical Markdown file per project. Repeated wording
from older CVs is merged into the same file, while conflicting or unsupported
details are recorded as evidence gaps instead of being presented as facts.

## Canonical projects

| Project | Category | Evidence status |
| --- | --- | --- |
| [Editify - Multi-Agent Financial Video Editor](editify-finance-video-agent.md) | Hackathon project | Event and public repository confirmed |
| [Operational Process Digitalization Platform](operational-process-digitalization-platform.md) | Internal program | CV confirmed; acts as the umbrella architecture |
| [Operations App](operations-app.md) | Internal workforce and payroll-operations application | User-confirmed production workflow; adoption counts remain incomplete |
| [Adversarial RPA Refactor Loop](adversarial-rpa-refactor-loop.md) | Internal agentic engineering workflow | GitHub PR evidence; bounded loop applied to an RPA refactor |
| [Camunda WebSocket Task Events](camunda-websocket-task-events.md) | Open-source Java library | Public pre-release; green CI and 55 tests verified |
| [Collaborative Camunda Modeler Fork](camunda-modeler-fork.md) | Open-source fork | GitHub-confirmed technical MVP |
| [Camunda Internal Platform Engineering](camunda-internal-platform-engineering.md) | Internal infrastructure and DevOps | User-confirmed; exact tools and metrics need expansion |
| [Enterprise SOAR Automation Delivery](enterprise-soar-automation-delivery.md) | Client cybersecurity automation | Repeated across five CVs; dates need confirmation |
| [Internal Process Automation Platform](internal-process-automation-platform.md) | Internal BPM and integrations | Repeated across five CVs; related SuiteCRM commits found |
| [AI-Powered Mortgage Agent](ai-powered-mortgage-agent.md) | Banking data and AI | Repeated across five CVs; merged with mortgage reporting |
| [AI Document Support Assistant](ai-document-support-assistant.md) | AI support tooling | Repeated across three CVs |
| [Firewall Zero-Touch Provisioning PoC](firewall-zero-touch-provisioning.md) | Network automation | CV plus user-confirmed scope |
| [Financial Collections Reporting](financial-collections-reporting.md) | Financial reporting | Two CV sources |
| [Ecommerce Final Project](ecommerce-final-project.md) | Academic project | CV plus user-confirmed conservative scope |
| [Discord Media Voting Bot](discord-media-voting-bot.md) | Incomplete personal project | User-confirmed match with public `animexbot` repository |
| [Resume as Code and AI Tailoring System](resume-as-code-ai-tailoring-system.md) | Personal developer tool | Local implementation; 23 tests passing; public link pending |

## Open-source work

- [Open Source Contributions](opensource-contributions.md) records upstream
  contributions and authored public libraries separately from employer-only
  projects.
- [Camunda WebSocket Task Events](camunda-websocket-task-events.md) is a public
  Apache-2.0 library with a verified 55-test suite; it remains pre-release and
  has no reported users yet.
- The SuiteCRM entry documents the DocumentRevision V8 API pull request,
  including its original and correctly targeted versions.

## Deduplication rules applied

- SOAR descriptions under Innovery and Neverhack are one project line until the
  acquisition-transition dates are confirmed.
- A one-page targeted resume may consolidate the employment line as `Neverhack,
  formerly Innovery` and omit SOAR when stronger role-relevant Innovery
  evidence is available; this presentation choice does not remove the project
  from the knowledge base.
- Legacy no-code, ProcessMaker BPM, PHP middleware, and CRM-to-ERP integration
  are one internal process-automation platform.
- Mortgage web scraping, weekly mortgage and loan reports, and the AI-powered
  mortgage agent are one project until the older macroeconomic API wording is
  confirmed as the same or a separate system.
- `vercinbleach/animexbot` is the Discord anime bot described in the CV. The
  repository's TypeScript implementation overrides the older CV's Python claim.
- The Operations App is separate from the wider digitalization program.
- The Camunda Modeler fork is separate from both until its production
  relationship is confirmed.
- Camunda WebSocket Task Events is a standalone open-source extraction from the
  internal platform's realtime needs. It does not yet replace production SSE.
- Camunda Internal Platform Engineering contains the CI/CD, Docker, Docker
  Compose, scripting, and monitoring work supporting the internal environment.

## Source CVs reviewed

- `archive/previous-cvs/CV Vincenzo 2025.pdf`
- `archive/previous-cvs/CV Vincenzo 2026 (1).pdf`
- `archive/previous-cvs/CV Vincenzo Actualizado - Copy.pdf`
- `archive/previous-cvs/CV Vincenzo Actualizado ENG.pdf`
- `archive/previous-cvs/vin cv.pdf`

The source PDFs remain unchanged.

## Structured-claim pilot

The first machine-readable claim pass covers three deliberately different
projects:

- `ai-powered-mortgage-agent.md`: AI tooling, evaluation methods, operational
  reporting, an unverified historical metric, and cost evidence gaps.
- `firewall-zero-touch-provisioning.md`: infrastructure ownership, team scope,
  CI uncertainty, and a conflicting vendor list.
- `camunda-websocket-task-events.md`: repository-verified architecture,
  security, test evidence, pre-release status, and explicit non-adoption.

Run `python scripts/knowledge_claims.py check` after structured claims change.
Active tailoring also supplies every complete project Markdown file directly to
the advisory scouts and Resume Composer.
