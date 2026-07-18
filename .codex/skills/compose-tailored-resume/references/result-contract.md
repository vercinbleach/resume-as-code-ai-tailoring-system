# Resume Composer result contract

The outbox contains exactly:

- `result.json`;
- `resume.yaml` when `status` is `ready`;
- `resume.pdf` when `status` is `ready`.

No other outbox file is allowed.

For a ready result, preserve at least the baseline's total number of Experience
bullets. When the baseline contains two or more projects, keep at least two
complementary project entries. These are global density constraints, not a
fixed bullet quota per employer.

## Root result

Use exactly these root keys:

```json
{
  "schema_version": 1,
  "status": "ready",
  "inputs": {
    "baseline_sha256": "<sha256>",
    "job_sha256": "<sha256>",
    "knowledge_manifest_sha256": "<sha256>",
    "scout_result_sha256": ["<sha256>"]
  },
  "artifacts": {
    "resume_yaml": {"path": "resume.yaml", "sha256": "<sha256>"},
    "resume_pdf": {"path": "resume.pdf", "sha256": "<sha256>"}
  },
  "provenance": [],
  "visual_inspection": {},
  "blocking_reasons": [],
  "questions": []
}
```

Copy input hashes from the manifest. `scout_result_sha256` contains zero to two
hashes in assignment order. A scout result is advisory and its presence or
absence never changes evidence validity.

## Provenance

Provide exactly one provenance entry for every final experience bullet,
project entry, and individual listed skill. Use a JSON Pointer into
`resume.yaml` as `target`.

Experience bullet or project entry:

```json
{
  "kind": "experience-bullet",
  "target": "/cv/sections/Experience/0/highlights/0",
  "sources": [
    {
      "type": "knowledge-base",
      "file": "knowledge-base/experience/example.md",
      "line_start": 20,
      "line_end": 27
    }
  ]
}
```

Use `kind: project` with a target such as
`/cv/sections/Projects & Open Source/0` for a project entry.

Individual skill:

```json
{
  "kind": "skill",
  "target": "/cv/sections/Technical Skills/0/details",
  "item": "Python",
  "sources": [
    {
      "type": "knowledge-base",
      "file": "knowledge-base/experience/example.md",
      "line_start": 20,
      "line_end": 27
    }
  ]
}
```

Knowledge-base sources must point to copied active experience or project
Markdown and use inclusive line ranges. Scout output and job text are not
candidate evidence.

For text copied exactly from the baseline, a source may instead be:

```json
{"type": "baseline", "pointer": "/cv/sections/Experience/0/highlights/0"}
```

A baseline pointer is valid only when the final text is identical. Rewritten
or combined content must cite the supporting knowledge-base ranges.

## Visual inspection

A ready result uses exactly:

```json
{
  "inspected": true,
  "pdf_sha256": "<same hash as artifacts.resume_pdf.sha256>",
  "page_count": 1,
  "pages_viewed": [1],
  "checks": {
    "no_clipping_or_overlap": true,
    "legible_text": true,
    "balanced_spacing": true,
    "consistent_hierarchy": true
  },
  "issues": []
}
```

Set `inspected` only after viewing an image rendered from the final PDF hash.
Any false check or unresolved issue blocks `ready`.

`balanced_spacing` requires readable separation before every section title. Do
not leave later titles crowded against prior content while avoidable whitespace
remains at the bottom of the page. Preserve the baseline design rather than
compressing section transitions to create unused space.

## Status rules

For `ready`, both artifacts exist, every provenance target resolves, visual
inspection is complete, and `blocking_reasons` and `questions` are empty.

For `needs-evidence`, set `artifacts` and `visual_inspection` to `null`, set
`provenance` to an empty array, provide at least one blocking reason, and do not
write `resume.yaml` or `resume.pdf`.
