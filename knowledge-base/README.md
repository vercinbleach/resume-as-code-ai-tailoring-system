# Knowledge base

Esta carpeta contendrá la versión extensa y verificable del historial profesional.
Aquí no existe el límite de una página del CV.

- `experience/`: un archivo Markdown por empresa, rol o etapa profesional.
- `projects/`: un archivo Markdown por proyecto relevante.
- `education/`: formación, certificaciones y aprendizaje relevante.
- `career-preferences.md`: preferencias profesionales actuales para job
  matching; deben verificarse de nuevo antes de cada candidatura.

Cada entrada podrá incluir contexto, responsabilidades, contribuciones,
tecnologías, resultados, métricas y enlaces de evidencia.

## Structured claims

Selected entries also contain a delimited JSON block of atomic claims and
evidence gaps. Markdown remains the canonical human-readable source; claims are
optional verification anchors and retrieval helpers, not a replacement for the
complete source files or a mandatory semantic gate.

- Contract: `contracts/claim-contract.md`
- Claim schema: `contracts/claim.schema.json`
- Generated index: `generated/claims.jsonl`

Validate and rebuild the index from the repository root:

```powershell
python scripts/knowledge_claims.py validate
python scripts/knowledge_claims.py build
python scripts/knowledge_claims.py check
```

The first pilot covers the mortgage agent, firewall provisioning PoC, and
Camunda WebSocket library. Other entries remain valid narrative sources until
their claims are structured during normal knowledge-base review.

Active tailoring snapshots every complete experience and project Markdown file
for advisory scouts and the Resume Composer. The Composer must verify final
wording against those sources. Structured claims improve precision but are not
required before a canonical Markdown passage can support conservative wording.
