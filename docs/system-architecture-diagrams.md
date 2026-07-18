# Atlas visual de la arquitectura del resume

Estos diagramas representan la arquitectura activa simplificada. El sistema
compone un resume global por oferta, promueve un PDF validado y termina en Clean
QA. Completar y enviar la candidatura queda fuera de alcance.

## 0. Vista simplificada por bloques

```mermaid
flowchart LR
    U["Usuario"] --> B1["1. Job Intake"]
    B1 --> B3["3. Advisory Scouts"]
    B2["2. Knowledge Base"] --> B3
    B1 --> B4["4. Resume Composer"]
    B2 --> B4
    B3 --> B4
    BASE["Resume baseline"] --> B4
    B4 --> B5["5. Coordinator Gate"]
    B5 --> B6["6. Clean QA terminal"]
    B6 --> FINAL["Resultado final:<br/>resume PDF + QA"]
```

## 1. Arquitectura general completa

```mermaid
flowchart TB
    U["Usuario<br/>URL de oferta + objetivo"] --> COORD["Codex coordinator"]

    subgraph INTAKE["Bloque 1: Job Intake"]
        COORD --> BROWSER["Browser<br/>oferta + Apply visible"]
        BROWSER -. "nunca escribir, subir,<br/>autenticar, consentir o enviar" .-> SAFE["Safety boundary"]
        BROWSER --> RAW["job-intake.json<br/>captura auditable"]
        RAW --> NORMALIZE["Validar + normalizar"]
        NORMALIZE --> JD["job-description.md"]
    end

    subgraph KB["Bloque 2: Knowledge Base"]
        EXP["knowledge-base/experience/<br/>Markdown completos"] --> KBSNAP["Snapshot read-only"]
        PROJECTS["knowledge-base/projects/<br/>Markdown completos"] --> KBSNAP
        CLAIMS["Claims estructurados<br/>cuando existen"] -. "ayuda, no gate" .-> KBSNAP
    end

    subgraph SCOUTS["Bloque 3: Advisory Scouts"]
        JD --> SWAVE["Crear tasks top-level nuevas"]
        KBSNAP --> SWAVE
        SWAVE --> S1["Scout advisory A<br/>gpt-5.6-terra / xhigh"]
        SWAVE --> S2["Scout advisory B<br/>gpt-5.6-terra / xhigh"]
        SWAVE --> SN["Scout advisory N<br/>gpt-5.6-terra / xhigh"]
        S1 --> SOUT["Reportes advisory<br/>relevancia, gaps, riesgos"]
        S2 --> SOUT
        SN --> SOUT
        S1 -. "no lee" .-> S2
        S2 -. "no lee" .-> SN
    end

    subgraph COMPOSE["Bloque 4: Resume Composer"]
        BASE["Canonical RenderCV YAML<br/>baseline read-only"] --> PACK["Composer input packet"]
        JD --> PACK
        KBSNAP --> PACK
        SOUT --> PACK
        PACK --> COMP["Una task top-level nueva<br/>gpt-5.6-sol / high"]
        COMP --> PLAN["Plan global del CV<br/>densidad total + portfolio"]
        PLAN --> WRITE["Bullets + projects + links<br/>+ skills sin duplicacion"]
        WRITE --> CYAML["Job-specific resume.yaml"]
        CYAML --> RENDER["RenderCV"]
        RENDER --> CPDF["Candidate resume.pdf"]
        CPDF --> VISUAL["Inspeccion visual propia"]
        VISUAL -->|"ajuste dentro de la misma task"| WRITE
        VISUAL -->|"candidate ready"| HANDOFF["Composer bundle privado"]
    end

    subgraph GATE["Bloque 5: Coordinator Gate"]
        HANDOFF --> VERIFY["Hashes + inventario + source drift"]
        VERIFY --> DENSITY["Experience >= baseline total<br/>Projects >= 2 si disponibles"]
        DENSITY --> PREFLIGHT["PDF preflight + una pagina<br/>secciones + links"]
        PREFLIGHT --> DECIDE{"Pasa todo?"}
        DECIDE -->|"no"| HOLD["No promover"]
        DECIDE -->|"si"| PROMOTE["Promocion atomica<br/>a composer/"]
        BASE -. "hash intacto" .-> LOCKED["Baseline canonico sin cambios"]
    end

    subgraph CLEAN["Bloque 6: Clean QA terminal"]
        PROMOTE --> QSTART["Crear judges seleccionados"]
        JD --> QSTART
        QSTART --> TECH["Technical<br/>solo PDF"]
        QSTART --> LEAD["Leadership<br/>solo PDF"]
        QSTART --> MATCH["Job Match<br/>PDF + JD"]
        QSTART --> CALLBACK["Callback<br/>PDF + JD"]
        TECH --> QFAN["Coordinator QA fan-in"]
        LEAD --> QFAN
        MATCH --> QFAN
        CALLBACK --> QFAN
        QFAN --> REPORT["report.md + report.json"]
        REPORT -->|"si se solicita"| COMPARE["Comparacion entre versiones<br/>sesion o PDF exacto"]
        REPORT -->|"sin comparacion"| END["Fin de pipeline<br/>sin retorno al Composer"]
        COMPARE --> END
    end
```

## 2. Bloque Job Intake

```mermaid
flowchart TB
    URL["URL de oferta"] --> OPEN["Abrir oferta"]
    OPEN --> EXPAND["Expandir contenido visible"]
    EXPAND --> APPLY["Abrir Apply real"]
    APPLY --> OBSERVE["Observar campos, preguntas,<br/>opciones, documentos y avisos"]
    OBSERVE --> RAW["job-intake.json"]
    RAW --> VALIDATE["Validar captura"]
    VALIDATE --> JD["job-description.md"]

    APPLY -. "stop antes de" .-> FORBIDDEN["Datos personales<br/>upload<br/>login<br/>consentimiento<br/>submit"]
    HIDDEN["ATS oculto, ranking,<br/>auto-reject"] --> UNKNOWN["Unknown, nunca inferir"]
```

Job Intake crea evidencia observable de la oferta. No completa la candidatura y
no convierte reglas ocultas del ATS en supuestos del sistema.

## 3. Bloque Knowledge Base

```mermaid
flowchart TB
    USER["Recuerdo y confirmacion del usuario"] --> MD["Markdown canonico"]
    REPOS["Repositorios y artefactos"] --> MD
    LINKS["Fuentes publicas verificadas"] --> MD
    OLD["CV historicos"] -. "fuente secundaria" .-> MD

    MD --> EXP["experience/*.md completos"]
    MD --> PROJ["projects/*.md completos"]
    MD --> EDU["education/*.md"]
    MD --> PREF["career-preferences.md"]
    MD --> CLAIMS["Claims atomicos opcionales"]

    EXP --> SNAP["Snapshot read-only por sesion"]
    PROJ --> SNAP
    CLAIMS -. "indices y anchors" .-> SNAP
```

Los archivos Markdown completos son la fuente de contexto del Composer. Los
claims estructurados ayudan a localizar y verificar, pero no sustituyen el
texto completo ni requieren un gate semantico separado.

## 4. Bloque Advisory Scouts

```mermaid
flowchart TB
    COORD["Coordinator"] --> START["Crear scout wave"]
    JOB["Oferta normalizada"] --> START
    MD["Snapshot Markdown read-only"] --> START

    START --> A["Task A<br/>gpt-5.6-terra / xhigh"]
    START --> B["Task B<br/>gpt-5.6-terra / xhigh"]
    START --> N["Task N<br/>gpt-5.6-terra / xhigh"]

    A --> AO["Advisory report A"]
    B --> BO["Advisory report B"]
    N --> NO["Advisory report N"]

    AO --> COLLECT["Coordinator collect + validate"]
    BO --> COLLECT
    NO --> COLLECT
    COLLECT --> READY["Pinned scout outputs"]

    A -. "sin acceso" .-> BO
    B -. "sin acceso" .-> NO
    AO -. "no escribe CV" .-> LIMIT["Advisory only"]
```

Los scouts amplian cobertura y reducen puntos ciegos. Un scout puede señalar
riesgo, pero su reporte sigue siendo advisory y no bloquea por si solo. No hay
gates semanticos adicionales antes de la composicion.

## 5. Bloque Resume Composer

```mermaid
flowchart TB
    BASE["Canonical resume baseline"] --> INPUT["Composer packet completo"]
    JOB["Normalized job"] --> INPUT
    SCOUTS["Todos los advisory reports"] --> INPUT
    EXP["Todos los experience Markdown"] --> INPUT
    PROJ["Todos los project Markdown"] --> INPUT

    INPUT --> TASK["Una Resume Composer task<br/>gpt-5.6-sol / high"]
    TASK --> GLOBAL["Planificar documento global<br/>y medir espacio real"]
    GLOBAL --> E["Seleccionar bullets de Experience"]
    GLOBAL --> P["Seleccionar portfolio de Projects"]
    GLOBAL --> L["Seleccionar links defendibles"]
    GLOBAL --> S["Agrupar Technical Skills"]

    E --> DEDUPE["Deduplicar logros y evidencia"]
    P --> DEDUPE
    L --> DEDUPE
    S --> DEDUPE
    DEDUPE --> DENSITY["Conservar densidad global:<br/>Experience >= baseline<br/>Projects >= 2 si disponibles"]
    DENSITY --> SOURCE["Escribir resume.yaml"]
    SOURCE --> RENDER["RenderCV"]
    RENDER --> PDF["resume.pdf"]
    PDF --> VIEW["Inspeccion visual"]
    VIEW --> CHECK{"Una pagina, legible,<br/>coherente y sin colisiones?"}
    CHECK -->|"no"| GLOBAL
    CHECK -->|"si"| OUT["Composer bundle"]
```

El Composer decide el CV como un solo producto. Puede intercambiar espacio entre
secciones y detectar redundancia que un Writer por seccion no puede resolver. No
edita la knowledge base ni el baseline canonico.

## 6. Bloque Coordinator Gate

```mermaid
flowchart TB
    OUT["Composer bundle privado"] --> ID["Verificar task, model y reasoning"]
    ID --> HASH["Verificar inputs, hashes<br/>y source drift"]
    HASH --> INV["Verificar inventario esperado"]
    INV --> LOCK["Comparar metadata factual bloqueada"]
    LOCK --> DENSITY["Validar densidad global"]
    DENSITY --> PDF["PDF checks deterministas"]
    PDF --> GATE{"Batch completo y valido?"}
    GATE -->|"no"| REJECT["Rechazar sin promocion parcial"]
    GATE -->|"si"| PROMOTE["Promocion atomica a<br/>tailoring/sessions/session-id/composer/"]
    PROMOTE --> RECEIPT["Checks + receipt + final PDF"]
```

El coordinator valida y promueve. No reescribe contenido semantico ni fusiona
resultados de Writers por seccion.

## 7. Bloque Clean QA terminal

```mermaid
flowchart TB
    PDF["Promoted resume.pdf"] --> START["Crear QA session"]
    JD["job-description.md"] --> START
    START --> T["Technical task nueva<br/>solo PDF"]
    START --> L["Leadership task nueva<br/>solo PDF"]
    START --> J["Job Match task nueva<br/>PDF + JD"]
    START --> C["Callback task nueva<br/>PDF + JD"]
    T --> FAN["Validar batch"]
    L --> FAN
    J --> FAN
    C --> FAN
    FAN --> REPORT["report.md + report.json"]
    REPORT -->|"opcional"| COMPARE["Comparar sesiones o PDFs exactos"]
    REPORT --> HUMAN["Decision humana"]
    COMPARE --> HUMAN
    HUMAN --> APPROVE["Usar resume candidato"]
    HUMAN --> CLOSE["Cerrar oferta o iniciar<br/>una nueva sesion manual"]

    REPORT -. "nunca" .-> COMPOSER["No retorno al Composer"]
    REPORT -. "nunca" .-> NEXT["No evidencia para otro judge"]
```

Clean QA juzga el artefacto final sin contexto de construccion. Es terminal: no
existe repair automatico ni una segunda pasada del Composer. Una comparacion
posterior pertenece al coordinator, nunca entra en los prompts de los judges y
no transfiere scores antiguos a un PDF modificado.

## 8. Fronteras de acceso por artefacto

```mermaid
flowchart LR
    RAW["job-intake.json"] --> COORD["Coordinator"]
    JD["job-description.md"] --> SCOUTBOX["Scout sandboxes"]
    MDSNAP["Full Markdown snapshot"] --> SCOUTBOX
    SCOUTBOX --> SOUT["Advisory reports"]

    JD --> CBOX["Composer sandbox"]
    BASE["canonical resume.yaml"] --> CBOX
    MDSNAP --> CBOX
    SOUT --> CBOX
    CBOX --> CBUNDLE["Private Composer bundle"]
    CBUNDLE --> CGATE["Coordinator gate"]
    CGATE --> PDF["Promoted resume.pdf"]

    PDF --> QBOX["Clean QA sandboxes"]
    JD --> QBOX
    QBOX --> REPORTS["QA reports"]

    RAW -. "no se copia" .-> SCOUTBOX
    RAW -. "no se copia" .-> CBOX
    RAW -. "no se copia" .-> QBOX
    SOUT -. "no se copia" .-> QBOX
    MDSNAP -. "no se copia" .-> QBOX
    CBOX -. "no parent context" .-> QBOX
    REPORTS -. "no retorno" .-> CBOX
```

Las aristas `no se copia` son controles del coordinator sobre inputs. No
representan una frontera de seguridad del sistema operativo.

## 9. Sandbox ligero v1

```mermaid
flowchart TB
    SOURCE["Coordinator source files"] --> CREATE["Crear workspace por task"]
    CREATE --> INPUTS["inputs/<br/>copias read-only + SHA-256"]
    CREATE --> WORK["work/<br/>scratch privado"]
    CREATE --> OUT["outputs declarados"]
    CREATE --> MAN["manifest.json<br/>inventario + hashes"]

    OUT --> VERIFY["Verificar manifest, hashes,<br/>source drift e inventario"]
    INPUTS --> VERIFY
    MAN --> VERIFY
    VERIFY --> VALIDATE["Validar contrato del rol"]
    VALIDATE --> PROMOTE["Promocion all-or-nothing"]
    PROMOTE --> CLEAN["Cleanup despues del exito"]

    CREATE -. "policy-only" .-> LIMIT["Aislamiento logico same-user<br/>no contenedor ni frontera OS"]
```

Esta version no incorpora contenedores, VMs, identidades separadas, firewall,
bloqueo tecnico de red, sandboxes calientes, JSONL, telemetria, scheduler ni
retries automaticos.

## 10. Roles activos

```mermaid
flowchart TB
    ACTIVE["Activos"] --> AS["Advisory Scouts"]
    ACTIVE --> RC["Single Resume Composer"]
    ACTIVE --> CQ["Clean QA judges"]
```

Los archivos legacy de orquestaciones anteriores pueden seguir presentes para
trazabilidad, pero no se invocan en una sesion activa ni definen la arquitectura
vigente.

## Lectura rapida

- Job Intake observa y normaliza la oferta.
- La Knowledge Base conserva todos los Markdown completos.
- Advisory scouts encuentran señales y riesgos sin decidir el CV.
- Un solo Resume Composer compone, renderiza e inspecciona el documento global.
- El coordinator valida y promueve sin reescribir contenido.
- Clean QA juzga unicamente el PDF promovido y es terminal.
- La aplicacion se completa manualmente fuera del sistema.

## Estrategia y decisiones de ROI

La arquitectura usa fan-out solo donde aporta perspectivas independientes: los
scouts y los judges limpios. La sintesis permanece en una sola task con la foto
completa para evitar optimizacion local, duplicacion y decisiones incoherentes
entre secciones.

Implementado como politica activa:

- scouts nuevos y aislados con `gpt-5.6-terra` y reasoning `xhigh`;
- una sola composicion global con `gpt-5.6-sol` y reasoning `high`;
- baseline, oferta, advisory reports y todos los Markdown completos como input
  del Composer;
- render e inspeccion visual dentro de la misma task de composicion;
- validacion y promocion exclusiva del coordinator;
- Clean QA aislado y terminal;
- no gates semanticos obligatorios entre scouts y Composer, y no escritura
  semantica dividida por secciones.

Pospuesto hasta que exista una necesidad medible:

- embeddings, vector database, RRF y reranker dedicado;
- contenedores o VMs, sandboxes calientes, firewall, JSONL y telemetria;
- QA-to-Composer repair, segunda composicion automatica, variantes multiples y
  retries.
