# Project rules

- Never use bold text inside resume bullet points.
- Never use Unicode U+2014 in authored or generated project content; use a comma, colon, semicolon, or ASCII hyphen instead.
- Use `AI APIs` or `AI SDKs` in resume-facing wording instead of specific foundation-model names or versions.
- For QA orchestration, read `qa/resume-qa/SKILL.md`. An explicitly invoked `resume-*-clean` evaluator follows only its own isolation skill.
- Run every clean semantic evaluator in a new top-level Codex task. Never use subagents, forks, or a previously used evaluator task.
- Tailoring scouts use new top-level `gpt-5.6-terra` tasks with `xhigh`; the global Resume Composer uses a new top-level `gpt-5.6-sol` task with `high`.
- The Resume Composer must render and visually inspect its actual one-page PDF before finalizing.
- When behavior or contracts change, update every impacted active doc and diagram and remove stale active descriptions; do not rewrite historical or generated artifacts.
- Keep sandbox v1 changes within `docs/lightweight-sandbox-v1-scope.md`; expansion requires explicit user approval.
- Keep Composer changes within `docs/writer-orchestration-v1-scope.md`; run advisory scouts and the single Resume Composer in fresh top-level Codex tasks, never subagents, forks, or reused tasks.
- Treat documentation and Mermaid diagrams as part of every behavior change: update every impacted canonical file in the same task, or state why none is affected.
- Before claiming a project-wide documentation change is complete, search all active Markdown and state any historical or generated exclusions.
- When an approved resume correction reveals a reusable authoring rule, update the affected canonical baseline or knowledge-base source plus the existing authoring skill and active docs in the same task; do not create another skill unless explicitly requested.
- Treat localized post-pipeline review comments as targeted edits: change only the named content, rerender, inspect visually, and run deterministic PDF checks. Do not rerun semantic QA unless the user explicitly requests it.
- Semantic scores belong only to the exact PDF and QA session that produced them. Label cross-version comparisons by session or PDF identity; a modified PDF is unscored until a new clean session finishes.
