---
name: write-xyz-resume-bullets
description: Write, diagnose, shorten, or revise evidence-backed resume and project bullets for software engineering, data and AI, or engineering management roles. Use for ad hoc bullet-level work outside the automated Resume Composer when supplied wording needs stronger outcomes, technical specificity, verified metrics, scale, ownership, or job relevance.
---

# Technical Resume Bullet Writer

Write achievement-focused bullets for software, data and AI, and engineering
management. Optimize for truthful evidence density, not forced quantification.

Read `references/technical-patterns.md` when choosing domain-specific metrics,
verbs, diagnostic questions, or bullet structures.

## Evidence boundary

- Use only facts explicitly supplied by the user or present in named source
  artifacts.
- When the user identifies one bullet or a bounded set of bullets, revise only
  that scope. Do not recompose unrelated roles, projects, sections, or layout.
- Preserve uncertainty, caveats, and exact ownership scope.
- Ask a focused question when a material fact is missing instead of inferring
  or inventing it.
- Treat a job description as relevance guidance, never as evidence about the
  candidate.

## Do not

- Do not ship duty-only bullets or use `responsible for`, `worked on`,
  `helped with`, `assisted with`, or `participated in` as final wording.
- Do not strengthen limited contribution into architecture, leadership,
  ownership, or direct management. State the supported scope or omit it.
- Do not invent, estimate, approximate, back-calculate, round, or improve a
  metric. Do not require a number in every bullet or turn uncertainty into a
  range.
- Do not move or combine claims across employers, roles, or projects.
- Do not repeat the same accomplishment or metric across bullets.
- Do not add job-description keywords, technologies, or proficiency levels
  without allowed evidence.
- Do not list soft skills, assumed or basic skills, outdated technologies, or
  skills the candidate cannot defend in an interview.
- Do not use vague claims such as `high impact`, `scalable`, `robust`,
  `optimized`, or `improved` without supporting what changed.
- Do not end a system or integration bullet with a component inventory. State
  the supported operational, user, reliability, delivery, or business result.
- Do not collapse verified production deployment into generic adoption. For
  open source, distinguish upstream merge status, downstream fork use, and
  production use when the evidence supports each state.
- Do not repeat a generic opener such as `Built` across nearby bullets when a
  more precise verb describes the action. Do not swap verbs merely for variety
  or use verb changes to inflate ownership.
- Do not replace a supported differentiating term such as `Custom Agent
  Harnesses` with a generic catch-all solely to simplify the skills section.
- Do not make a vendor or coding tool the subject when the accomplishment is the
  system or workflow. Name the system first and describe the tool as the method,
  such as `agentic system with Codex`.
- Do not imply Board, executive, or director-level influence from proximity.
  Distinguish formal reporting, direct collaboration, presentation audience,
  and the decision or outcome produced.
- Do not combine people development or coaching with executive prioritization
  when they are separate achievements. Attach executive collaboration to the
  process, program, or delivery decision it shaped.
- Do not change employer, title, date, chronology, acquisition formatting, or
  section order during a bullet-only correction unless explicitly requested.
- Do not use bold text inside bullets or Unicode U+2014.

## Framework selection

Choose the structure that best fits the evidence:

- XYZ: verified outcome and metric exist. `Accomplished X, measured by Y, by doing Z.`
- CAR: a technical challenge, concrete action, and result are clearer than a
  strict metric-first sentence.
- Condensed STAR: context is necessary to understand ownership or management
  scope, but omit background that does not earn space.
- Build-scale-outcome: the strongest evidence is a system, its scale or
  constraints, and what it enabled.
- Scope-action-outcome: the strongest evidence is team scope, a leadership
  action, and an outcome delivered through others.

Do not force every bullet into XYZ or require every bullet to contain a number.
A precise qualitative result is stronger than an unsupported metric.

## Workflow

1. Classify the bullet as software, data and AI, or engineering management.
2. Resolve the supplied facts and named evidence before drafting.
3. Diagnose the original for duty language, vague ownership, missing outcome,
   irrelevant stack listing, excessive length, or unsupported scope.
4. Identify the candidate's specific contribution, the system or team scope,
   the verified result, and the methods that materially explain it.
5. Ask only questions whose answers could materially improve or validate the
   bullet. Prefer ownership, before/after, scale, reliability, cost, delivery,
   adoption, or people-development questions.
6. Select the best framework and lead with the most differentiating evidence.
7. Remove redundant context, filler, adjectives, and duty language.
8. Validate the final bullet against every rule below.

## Writing rules

- Express one achievement per bullet.
- Start with an accurate action verb.
- For systems and integrations, state what became possible, centralized,
  faster, safer, more reliable, or easier to operate after the work.
- Distinguish individual contribution, team contribution, technical leadership,
  and direct people management.
- State technologies only when they explain the method or match a supported
  target criterion. Avoid stack inventories inside a sentence.
- Prefer concrete system behavior, scale, reliability, delivery, user, cost, or
  business evidence over generic claims such as `high impact` or `scalable`.
- For production systems, surface verified reliability evidence when available,
  such as failures, incidents, recovery, latency, throughput, availability, or
  cost. If it is unavailable, record the gap instead of inventing a metric.
- Keep the bullet concise enough for one or two rendered lines when practical.
- Preserve technically meaningful constraints and caveats.
- Preserve supported technical nouns that materially distinguish the work,
  including `harness`, protocol, evaluation, orchestration, and safety terms.
- For executive or Board interaction, name the exact relationship and connect
  it to prioritization, alignment, a decision, delivery, or another supported
  outcome. Use `reported to` only for a real reporting line.
- Use job-description terminology only when it is a technically defensible
  synonym for the evidence.

## Ad hoc output

By default, return:

1. Final bullet.
2. Supporting claim IDs or named evidence.
3. One short caveat or missing-evidence question only when needed.

For multiple bullets, keep the same order as the input. If the user requests
final copy only, return only the bullets.

## Final validation

Reject or revise a bullet if any answer is no:

- Is every fact supported?
- Is ownership stated at the correct level?
- Is the result concrete, or honestly qualitative when no metric exists?
- Does a system or integration bullet explain its effect rather than only list
  what was built or connected?
- Does each number come directly from allowed evidence?
- Does the method explain how the result happened?
- Is the bullet relevant to software, data and AI, or engineering management?
- Is it concise, natural, and free of duty language?
