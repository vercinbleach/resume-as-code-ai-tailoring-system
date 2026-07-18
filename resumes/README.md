# Resume sources

- `vincenzo-rosciano-one-page.yaml`: canonical one-page RenderCV source.
- `vincenzo-rosciano-jakes-cambria.yaml`: Cambria typography experiment.
- `vincenzo-rosciano-jake.tex`: direct LaTeX comparison source.
- `variants/`: RenderCV theme-comparison inputs, not tailored job variants.

Build the canonical source with `scripts/build-resume.ps1`. Generated PDFs and
render intermediates belong in `output/` and are never sources of truth.

For job-specific tailoring, one global Resume Composer receives read-only copies
of the canonical YAML, normalized job, advisory scout reports, and every complete
experience and project Markdown snapshot. It writes and renders the tailored
candidate in its private workspace. The coordinator validates and promotes the
complete bundle to `tailoring/sessions/<session-id>/composer/`.

Tailored runs do not mutate the canonical YAML. Only explicit user-approved
baseline design or content decisions belong here. The current baseline keeps
Education clear and compact by placing each credential immediately below its
institution. Do not copy tailored variants, raw job intake, previous CVs,
knowledge-base files, evidence reviews, or advisory scout reports into this
folder.

The approved baseline uses the exact title `Lead Software Engineer` and treats
Innovery-to-Neverhack as one continuous line, `Neverhack (formerly Innovery)`,
rather than a thin standalone Neverhack block. Tailoring may replace
the bullets by relevance, but must preserve that employer and title metadata.
The consolidated line uses the single parseable title `Software Engineer`;
career progression remains knowledge-base evidence and is not encoded as a
compound `Junior Software Engineer to Software Engineer` title.
