# Structured claim contract

Canonical knowledge remains in the Markdown files. Machine-readable facts live
inside one delimited JSON block in each participating file:

````text
<!-- structured-claims:start -->
```json
{
  "schema_version": 1,
  "claims": [],
  "evidence_gaps": []
}
```
<!-- structured-claims:end -->
````

The markers are part of the contract. A file may contain at most one block.
The JSON must conform to `claim.schema.json` and the additional cross-file
checks performed by `scripts/knowledge_claims.py`.

## Claim rules

- Give every claim a globally unique, stable `claim-...` identifier.
- Keep `statement` atomic. Do not join unrelated accomplishments.
- Record where the claim came from in `evidence`.
- Use `status: confirmed` only when the statement is supported as written.
- Use `status: partial` when a narrower statement is supported and explain the
  boundary in `caveats`.
- Set `resume_safe` to `false` for `unverified`, `conflicting`, or confidential
  claims.
- Do not encode an unresolved historical metric as a confirmed claim.
- Keep technologies and dimensions normalized; put spelling variants in
  `aliases`.

## Evidence precedence

When sources disagree, retain the disagreement rather than selecting the more
impressive version. Use this default precedence only when the sources address
the same fact:

1. Current user confirmation or current public repository verification.
2. Local verification of current code or artifacts.
3. Historical CVs or LinkedIn snapshots.
4. Inference.

Inference may help an advisory scout locate evidence, but an inferred claim is
not resume safe until confirmed.

## Narrative evidence

A source does not need a structured claim before it can provide Composer
context. The complete Markdown remains canonical and is copied read-only into a
tailoring snapshot. Advisory scouts may point to relevant passages, but their
reports are non-binding. The Resume Composer verifies final wording directly
against the supplied Markdown or confirmed claims. This does not modify the
Markdown or automatically promote a passage into `claims.jsonl`.

## Evidence gaps

Evidence gaps are questions, not negative claims. Link them to affected claims
when possible. A gap remains `open` until new evidence resolves it or it is
explicitly marked `unrecoverable`.

## Commands

```powershell
python scripts/knowledge_claims.py validate
python scripts/knowledge_claims.py build
python scripts/knowledge_claims.py check
```

`build` writes `knowledge-base/generated/claims.jsonl` in stable claim-ID order.
`check` validates the Markdown blocks and fails when that generated index is
stale.
