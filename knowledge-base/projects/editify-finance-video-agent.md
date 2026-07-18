---
id: project-editify-finance-video-agent
name: Editify
type: hackathon-project
event: Speak Money - Voice x Fintech Hackathon
date: 2026-07-09
location: Barcelona, ES
team_size: 3
technical_members: 1
nontechnical_members: 2
status: prototype
repository: https://github.com/vercinbleach/hackaton-cala-voice-of-finance
event_url: https://luma.com/iidgd0eg
sources:
  - https://luma.com/iidgd0eg
  - github:vercinbleach/hackaton-cala-voice-of-finance
---

# Editify - Multi-Agent Financial Video Editor

## Hackathon context

Editify was built for the
[Speak Money - Voice x Fintech Hackathon](https://luma.com/iidgd0eg), a
one-night Barcelona event on July 9, 2026 where teams created voice or
sound-enabled fintech products and presented a live three-minute demo.

The project was delivered by a three-person multidisciplinary team. Vincenzo was
the only developer; the other two team members were non-technical contributors
focused on visual style and references, financial content, voice selection, and
editorial QA.

## Problem

Producing short financial-news videos requires several disconnected activities:
researching traceable market data, writing a factual script, generating and
aligning narration, creating charts and visual assets, deciding the edit, and
rendering a final video. Performing that workflow manually makes frequent video
production slow and difficult to reproduce.

## What the application does

Editify converts a financial brief into a faceless financial-news video through
a local multi-agent pipeline. It coordinates research, script generation,
voice, visual assets, editing decisions, media validation, and video rendering
through structured project artifacts.

The initial target was a 45-90 second daily “top movers” video covering five
gainers, five losers, their percentage movements, sourced catalysts, and what to
watch next.

## Solution

- A Cala adapter retrieves financial context and preserves source provenance.
- A Codex-based script agent converts the research and brief into grounded,
  schema-constrained narration.
- ElevenLabs generates the voiceover and timing alignment.
- Deterministic media workers turn the script, alignment, and generated assets
  into `edit.json` and a HyperFrames composition containing scenes, captions,
  charts, transitions, timing, and visual effects.
- HyperFrames validates and renders the composition before FFmpeg produces the
  final MP4.
- A Vite and React interface collects the brief, references, style, voice, and
  format and displays live pipeline state and outputs through SSE.
- A Bun and TypeScript backend orchestrates dependencies, retries, state, and
  provider integrations through JSON, Markdown, media, and NDJSON artifacts.

## Agent and orchestration architecture

- The target architecture defined research, script, and editor reasoning roles,
  but the coded prototype used Codex for grounded script generation and kept
  research, assets, voice, edit planning, and rendering behind controlled
  provider adapters or deterministic workers.
- A custom Codex harness launches `codex exec` non-interactively, streams JSONL,
  constrains output with JSON Schema, limits prompt and process output size,
  enforces a timeout, and validates the final response against research sources.
- The pipeline progresses through intake, research, script, voice, assets, edit,
  render, and completion stages. Voice and asset generation run in parallel.
- Stages exchange artifacts by `projectId` instead of maintaining a chat-style
  shared context. Failed runs can resume at the failed stage and reuse already
  validated outputs.
- Provider calls include controlled retry classification and heartbeat events
  for long-running Cala, Codex, ElevenLabs, and render operations.

## My contribution

- Served as the sole developer in a three-person multidisciplinary team.
- Designed the multi-agent architecture and file-based orchestration model.
- Built the React and Vite interface and the Bun and TypeScript backend.
- Implemented provider adapters for Cala, Codex, and ElevenLabs.
- Built the custom Codex execution harness and its prompt-grounding, structured
  output, timeout, and failure-classification safeguards.
- Built the edit planning, HyperFrames, FFmpeg, validation, and media pipeline.
- Implemented REST endpoints, resumable runs, SSE progress delivery, persistent
  NDJSON event history, operation heartbeats, and retry handling.
- Defined JSON contracts, functional gates, preflight scripts, and tests for
  intake, research, scripts, voice alignment, edits, SSE events, and media.
- Translated the non-technical teammates' visual, editorial, and voice decisions
  into reusable style rules and product inputs.

## Development and evaluation approach

- Built the implementation through a fully AI-assisted vibe-coding workflow,
  with Vincenzo directing the product and architecture, reviewing generated
  code, running tests, and making the final acceptance decisions.
- Used LLM-as-judge during development to critique outputs and guide iterations;
  this was a development-time evaluation practice rather than a production
  evaluator embedded in the committed runtime pipeline.
- Combined AI evaluation with Vincenzo's own human review, collaborator QA, and
  automated regression tests.
- Implemented tracing and logging through Codex JSONL events, persistent
  `events.ndjson` run histories, SSE progress streams, stage transitions,
  heartbeats, artifacts, checks, retries, and terminal failure records.
- Added deterministic graders and quality gates for input boundaries, source
  provenance, script grounding, JSON Schema compliance, voice alignment,
  continuous edit timelines, SSE integrity, and FFprobe media constraints.
- The public repository contains nine automated test files covering contracts,
  API behavior, orchestration, provider adapters, UI state, media generation,
  retry behavior, failure cases, and malformed fixtures.

## AI engineering and agent harness

- Worked close to the model by integrating Codex CLI directly instead of using
  an all-in-one agent framework such as LangChain or LangGraph.
- Built custom agent scaffolding around `codex exec` with `Bun.spawn`, prompt
  delivery over standard input, ephemeral sessions, a read-only sandbox,
  configurable model selection, schema-constrained output, and JSONL event
  parsing.
- Extracted the final agent message from the event stream and validated both its
  structure and its financial grounding before allowing the pipeline to
  continue.
- Implemented harness reliability controls including prompt and process-output
  size limits, timeouts with process termination, typed provider errors,
  retryability classification, and safe handling of authentication and
  rate-limit failures.
- Managed context explicitly by combining a normalized user brief with retrieved
  Cala research, available ticker constraints, and source identifiers, while
  keeping long-lived workflow state in artifacts scoped by `projectId`.
- Integrated the agent workflow with external APIs and command-line tools through
  provider adapters and deterministic workers: Cala, ElevenLabs, HyperFrames,
  FFmpeg, and FFprobe.
- Added agent-safety and system-safety boundaries through a read-only execution
  sandbox, schema validation, research-grounding checks, URL and upload limits,
  path-traversal protection, secret-safe errors, and controlled retries.

## Stack boundaries

- Used OpenAI Codex, TypeScript, Bun, React, Vite, and Hono in this project.
- Did not use Claude, Gemini, Python, Next.js, MCP, Agent SDK, LangChain,
  LangGraph, a vector database, Mem0, Zep, or persistent conversational memory.
- Retrieval was structured financial retrieval from Cala followed by grounded
  generation, rather than embedding-based semantic search.

## Team collaboration

- Non-technical teammate 1 selected reference videos and documented hooks,
  charts, captions, pacing, colors, typography, and examples.
- Non-technical teammate 2 tested ElevenLabs voices, prepared realistic market
  prompts, checked financial facts and sources, and reviewed pronunciation.
- Vincenzo owned the complete technical implementation and integrated their
  domain and editorial work into the prototype.
- Vincenzo also participated in the product's technical explanation to a panel
  of two judges and a live audience.

## Event experience

- The team entered through the event's `wildcard` route. According to Vincenzo's
  recollection, no other team appeared to be competing through that route, but
  the team did not receive a prize or formal winner designation.
- Vincenzo remembers the event as an enjoyable experience with a particularly
  positive and welcoming atmosphere.

## Outcome

- Delivered a substantial coded prototype during a one-night hackathon.
- Produced a local application with a web interface, API, provider adapters,
  orchestration, media-processing modules, automated checks, and test fixtures.
- Explained the product's technical implementation as part of the team
  presentation to two judges and an audience.
- Demonstrated how non-technical specialists can contribute directly to a
  complex AI product through structured inputs and QA responsibilities.
- The team did not win an award. No production deployment, user-adoption, or
  generated-video volume is recorded.

## Technologies

- TypeScript
- Bun
- React 19 and Vite 7
- Hono
- Codex CLI and a custom agent execution harness
- Cala API
- ElevenLabs
- HyperFrames
- FFmpeg and FFprobe
- GSAP and Lucide React
- Vitest, Bun Test, React Testing Library, Playwright, and JSDOM
- JSON Schema, AJV, and Zod
- REST, Server-Sent Events, JSON, and NDJSON
- Bun subprocess orchestration and JSONL agent-event processing
- File-based workflow state and artifact persistence
- Agent orchestration, LLM-as-judge, tracing, quality gates, and human review

## Links

- [GitHub repository](https://github.com/vercinbleach/hackaton-cala-voice-of-finance)
- [Hackathon page](https://luma.com/iidgd0eg)

## Reusable resume bullet

- Developed Editify, a multi-agent financial video editor, in one night as the sole
  developer on a three-person team with two non-technical collaborators,
  orchestrating Cala, Codex, ElevenLabs, HyperFrames, and FFmpeg from brief to
  rendered-video pipeline.

## Evidence gaps

- Confirm whether the team completed and presented a fully rendered live video.
- Add the final demo duration, number of successful pipeline runs, and generation
  time if available.
- Add any specific jury feedback or continuation after the event.
- Confirm the official name and participation rules of the `wildcard` route if it
  is ever used in a public-facing description.
- Confirm whether any part of the documented multi-evaluator video loop ran
  end-to-end; LLM-as-judge is currently confirmed as part of the development and
  review workflow, not as a committed runtime stage.
