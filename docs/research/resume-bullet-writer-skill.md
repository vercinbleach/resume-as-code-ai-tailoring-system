# Resume bullet writer skill review

Source reviewed:

- https://www.skills.sh/paramchoudhary/resumeskills/resume-bullet-writer
- https://github.com/Paramchoudhary/ResumeSkills/blob/main/skills/resume-bullet-writer/SKILL.md
- https://www.skills.sh/paramchoudhary/resumeskills/resume-section-builder
- https://github.com/Paramchoudhary/ResumeSkills/blob/main/skills/resume-section-builder/SKILL.md

The upstream project is MIT licensed. This repository does not install or copy
either upstream skill wholesale. Its useful guardrails inform the single global
Resume Composer without copying the upstream orchestration model.

## Adopted

- Diagnose duty language before rewriting.
- Select between XYZ, CAR, and condensed STAR.
- Ask targeted clarification questions before inventing detail.
- Use domain-specific verbs and metrics.
- Lead with outcomes, scale, or a technically meaningful result.
- Require system and integration bullets to explain the supported effect or
  capability, not only the components connected.
- Surface verified production reliability signals, such as failures, recovery,
  latency, throughput, availability, or cost, and leave the gap explicit when
  the evidence does not provide them.
- Keep bullets concise and relevant to the target role.
- Check specificity, ownership, result, method, and length.
- Avoid repetitive generic openers when a more precise evidence-backed verb
  exists, without treating verbs as interchangeable.
- Lead with the agentic system, multi-agent workflow, or harness and keep vendor
  tools as implementation details when that better represents the work.
- Prefer `AI APIs` or `AI SDKs` over specific foundation-model names and
  versions in resume-facing wording.
- Prefer a supported capability such as `authentication` over a vendor name
  when the vendor itself is not relevant to the target role.
- Preserve supported differentiating technical nouns such as `Custom Agent
  Harnesses` when relevant.
- Describe executive or Board interaction only through the exact relationship,
  action, and supported decision or outcome.
- Keep one achievement per bullet; do not combine coaching with executive
  prioritization when each belongs to a different outcome.
- Keep bullet-only review requests bounded and do not rewrite unrelated
  metadata, roles, projects, or sections.
- Distinguish upstream merge status, downstream fork adoption, and verified
  production use instead of treating them as interchangeable signals.
- Reject duty-only wording and vague final verbs such as `responsible for`,
  `worked on`, and `helped with`.
- Keep multiple roles at one company separate and prohibit claim movement
  across employers, roles, or projects.
- Exclude soft skills, assumed or basic skills, outdated technologies, and
  skills the candidate cannot defend in an interview.
- Require explicit evidence before assigning proficiency levels.
- Preserve the one-page Jake structure, locked metadata, and section order in
  the global composition task.

## Restricted to this project

- Software engineering.
- Data and AI.
- Engineering management and technical leadership.

Sales, marketing, customer success, academic, volunteer, career-change, and
employment-gap guidance were excluded.

## Rejected

- Requiring at least one number in every bullet.
- Estimating metrics, using approximate values, or lowering an uncertain guess.
- Quantifying activity merely because an outcome metric is missing.
- Treating strong verbs as interchangeable without checking ownership.
- Varying verbs cosmetically or using executive proximity as prestige without a
  supported action and result.
- Allowing job-description language to broaden the underlying evidence.
- Requiring four to six bullets per role.
- Allowing a two-page result.
- Placing Skills before Experience.
- Adding a Summary, Objective, headline, or other new section.

The Resume Composer receives full experience and project Markdown snapshots,
the normalized job, the baseline, and advisory scout reports. It applies these
writing guardrails while planning the complete document, so bullet strength,
project selection, links, skills, duplication, and one-page density are resolved
together. The active architecture does not divide semantic writing by section.
