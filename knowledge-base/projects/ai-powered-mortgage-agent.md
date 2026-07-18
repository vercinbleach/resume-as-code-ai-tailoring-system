---
id: project-ai-powered-mortgage-agent
name: AI-Powered Mortgage Agent
aliases:
  - Mortgage and Loan Competitive Reporting
  - Banking Market Web Scraping
type: client-project
organization: Innovery
team_size: 3
status: draft
sources:
  - archive/previous-cvs/CV Vincenzo 2025.pdf
  - archive/previous-cvs/CV Vincenzo 2026 (1).pdf
  - archive/previous-cvs/CV Vincenzo Actualizado - Copy.pdf
  - archive/previous-cvs/CV Vincenzo Actualizado ENG.pdf
  - archive/previous-cvs/vin cv.pdf
  - user-confirmed: 2026-07-17
evidence_checked: 2026-07-17
---

# AI-Powered Mortgage Agent

## Deduplication decision

The mortgage and loan reporting, bank-site web scraping, OCR pipeline, and AI
enrichment were parts of the same client project.

## Problem

A banking-sector client needed a weekly comparison of its own products against
the complete public mortgage and loan market in Spain. Product information was
distributed across bank websites, PDFs, and images, with different structures
and terminology for every institution.

## What the application does

The system covered every bank operating in Spain, with a separate acquisition
pipeline for each bank. It collected every publicly available mortgage and loan
product rather than a single standard product per institution.

Mortgage coverage included standard, youth, green or eco, and other published
product variants. Loan coverage included student, personal, instant, and other
public loan types. The client's own products were included alongside competitors
for comparison and validation.

The pipeline extracted as much public product information as possible,
including interest-rate fields such as TIN and TAE, eligibility rules, product
conditions, fees, and other relevant terms.

## Pipeline architecture

1. Ran a bank-specific Selenium and BeautifulSoup pipeline against each public
   website, before reliable native browser tools were commonly available for
   LLM workflows.
2. Extracted key text and product fields from pages and documents, including
   TIN, TAE, conditions, fees, and eligibility information.
3. Cleaned, normalized, and validated the collected data with deterministic
   Python and Pandas transformations.
4. Used LLM enrichment when deterministic parsing was insufficient for
   categorization or normalization.
5. Allowed the model to call predefined functions and tools inside the custom
   workflow.
6. Generated intermediate CSV data and a client-facing Excel workbook with two
   worksheets: mortgages and loans.
7. Ran the pipeline weekly, monitored executions, and emitted alerts when a
   bank-specific pipeline or reporting stage failed.

## OCR and image pipeline

As OCR and multimodal extraction improved, Vincenzo implemented an alternative
image-based pipeline for sources that were difficult or expensive to process as
HTML or PDFs. On some runs this reduced processing costs substantially, although
the exact before-and-after amount is no longer available.

## AI agent and tool-use mapping

- Tool calling / function calling: Confirmed. The LLM could invoke predefined
  functions and tools during enrichment and report preparation.
- Context management: Confirmed at pipeline level. Bank and product content was
  extracted, cleaned, normalized, and scoped before being passed to the model.
- Agent loops: Possible but not yet confirmed as a distinct autonomous loop.
  Function calling alone does not prove a multi-step agent loop.
- Triggers / automation workflows: Confirmed. The complete process ran weekly
  and included failure alerts.
- Memory / retrieval / RAG: Not evidenced for this project.
- Custom agent harness or scaffolding: Confirmed in the practical sense of a
  custom Python and LangChain workflow coordinating acquisition, deterministic
  processing, model tools, enrichment, validation, and output generation.

## AI evaluation and testing mapping

- Test sets: Partial evidence. The team and client validated test cases or
  samples, but the dataset, fields, and acceptance thresholds are not recalled.
- Graders / evaluators: Confirmed through the experimental LLM-as-judge stage
  and deterministic output checks.
- LLM-as-judge: Confirmed. It was tested during an early period when judge
  reliability was still weak and did not perform consistently enough on its
  own.
- Tracing / logging: Confirmed as operational pipeline monitoring, execution
  logs, and failure alerts. Model-span tracing is not confirmed.
- Quality checks: Confirmed through deterministic cleaning, output validation,
  hallucination mitigation, and client review.
- Cost or latency tracking: Cost-aware comparison is confirmed because the OCR
  pipeline materially reduced costs on some runs. Systematic latency tracking
  is not confirmed.
- Regression testing: Not confirmed.
- Human review: Confirmed through team review and validation with the client,
  whose own products also appeared in the report.

## Reliability work

Early versions had problems with hallucinated values and unreliable Excel
generation. The team iteratively reduced these failures using deterministic
cleaning and validation, narrower model responsibilities, human review, and
pipeline monitoring. Exact failure rates and test-suite details are no longer
available.

## My contribution

- Collaborated in a three-person team on the monitoring agent and reporting
  workflow.
- Engineered parts of the bank-specific extraction and transformation pipelines
  for public financial data from websites, PDFs, and images.
- Implemented the later OCR and image pipeline that substantially reduced costs
  on some executions.
- Helped build the custom model and tool orchestration, deterministic cleaning,
  output validation, monitoring, alerts, and weekly report generation.
- Converted unstructured mortgage and loan conditions into structured CSV and
  two-sheet Excel deliverables.

## Outcome

- Produced weekly mortgage and loan market reports covering public products
  from every bank operating in Spain.
- Delivered structured CSV data and a client Excel workbook separating mortgage
  and loan products.
- Reduced processing costs substantially on some runs through the OCR and image
  pipeline, with no surviving percentage or currency metric.
- Improved reliability over successive iterations by addressing hallucinations,
  Excel-generation failures, and bank-specific extraction failures.

## Technologies

- Python
- Selenium
- BeautifulSoup
- Pandas
- OCR
- LangChain
- LLMs
- Tool calling and function calling
- Custom agent harness and scaffolding
- Context management
- LLM-as-judge
- Deterministic validation and quality checks
- Tracing, logging, monitoring, and alerts
- Human review
- Cost optimization
- CSV and Excel generation
- Web and PDF extraction

## Structured claims

<!-- structured-claims:start -->
```json
{
  "schema_version": 1,
  "claims": [
    {
      "id": "claim-mortgage-spain-market-coverage",
      "statement": "The weekly pipeline covered publicly available mortgage and loan products from every bank operating in Spain.",
      "dimensions": ["impact", "operations", "product"],
      "technologies": [],
      "evidence": [
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "internal-anonymized",
      "aliases": ["all banks operating in Spain", "Spanish banking market coverage"],
      "caveats": ["The exact bank and product counts for a representative run have not been recovered."]
    },
    {
      "id": "claim-mortgage-bank-specific-extraction",
      "statement": "A separate Selenium and BeautifulSoup acquisition pipeline extracted public product information for each bank.",
      "dimensions": ["technical", "operations"],
      "technologies": ["Python", "Selenium", "BeautifulSoup"],
      "evidence": [
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "internal-anonymized",
      "aliases": ["web scraping pipeline", "one pipeline per bank"],
      "caveats": []
    },
    {
      "id": "claim-mortgage-deterministic-cleaning",
      "statement": "Python and Pandas transformations cleaned, normalized, and validated extracted financial product data before reporting.",
      "dimensions": ["technical", "reliability"],
      "technologies": ["Python", "Pandas"],
      "evidence": [
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "internal-anonymized",
      "aliases": ["deterministic validation", "data normalization"],
      "caveats": []
    },
    {
      "id": "claim-mortgage-tool-calling-harness",
      "statement": "A custom Python and LangChain workflow let the LLM call predefined functions and tools for enrichment and report preparation.",
      "dimensions": ["ai", "technical"],
      "technologies": ["Python", "LangChain", "LLMs", "Tool calling"],
      "evidence": [
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "internal-anonymized",
      "aliases": ["function calling", "custom agent harness", "custom scaffolding"],
      "caveats": ["A distinct autonomous agent loop has not been confirmed."]
    },
    {
      "id": "claim-mortgage-weekly-csv-excel",
      "statement": "The monitored weekly workflow delivered CSV data and a client Excel workbook with separate mortgage and loan worksheets.",
      "dimensions": ["impact", "operations", "product", "reliability"],
      "technologies": ["CSV", "Excel"],
      "evidence": [
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "internal-anonymized",
      "aliases": ["weekly report", "two-sheet workbook"],
      "caveats": []
    },
    {
      "id": "claim-mortgage-ocr-cost-reduction",
      "statement": "The later OCR and image extraction path substantially reduced processing costs on selected runs.",
      "dimensions": ["ai", "impact", "technical"],
      "technologies": ["OCR", "Multimodal extraction"],
      "evidence": [
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "medium",
      "status": "partial",
      "resume_safe": true,
      "sensitivity": "internal-anonymized",
      "aliases": ["image pipeline", "OCR pipeline", "cost optimization"],
      "caveats": ["The exact before-and-after cost and the affected run count have not been recovered."]
    },
    {
      "id": "claim-mortgage-ai-evaluation",
      "statement": "The team used LLM-as-judge experiments, deterministic quality checks, execution logging, failure alerts, and client human review.",
      "dimensions": ["ai", "reliability", "technical"],
      "technologies": ["LLM-as-judge", "Logging", "Monitoring", "Human review"],
      "evidence": [
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "medium",
      "status": "partial",
      "resume_safe": true,
      "sensitivity": "internal-anonymized",
      "aliases": ["graders", "evaluators", "tracing", "quality checks"],
      "caveats": ["Model-span tracing, the test-set definition, and regression testing are not confirmed."]
    },
    {
      "id": "claim-mortgage-one-hundred-percent-accuracy",
      "statement": "The historical CV described the pipeline as achieving 100% data accuracy.",
      "dimensions": ["impact", "reliability"],
      "technologies": [],
      "evidence": [
        {
          "source_type": "historical-cv",
          "locator": "archive/previous-cvs historical accuracy wording",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "low",
      "status": "unverified",
      "resume_safe": false,
      "sensitivity": "internal-anonymized",
      "aliases": ["100% data accuracy"],
      "caveats": ["The validation method, sample size, and measurement period have not been recovered."]
    }
  ],
  "evidence_gaps": [
    {
      "id": "gap-mortgage-exact-coverage-counts",
      "question": "How many banks and individual products were present in a representative weekly run?",
      "importance": "medium",
      "status": "open",
      "affects_claims": ["claim-mortgage-spain-market-coverage"]
    },
    {
      "id": "gap-mortgage-validation-cases",
      "question": "Which validation cases, fields, acceptance thresholds, and client checks were used?",
      "importance": "high",
      "status": "open",
      "affects_claims": ["claim-mortgage-ai-evaluation", "claim-mortgage-one-hundred-percent-accuracy"]
    },
    {
      "id": "gap-mortgage-ocr-cost",
      "question": "What was the measured cost difference between the original and OCR extraction paths?",
      "importance": "high",
      "status": "open",
      "affects_claims": ["claim-mortgage-ocr-cost-reduction"]
    },
    {
      "id": "gap-mortgage-agent-loop",
      "question": "Did retries and repeated tool calls form a formal autonomous agent loop?",
      "importance": "medium",
      "status": "open",
      "affects_claims": ["claim-mortgage-tool-calling-harness"]
    }
  ]
}
```
<!-- structured-claims:end -->

## Reusable resume bullets

- Delivered weekly competitive intelligence covering public mortgage and loan
  products from every bank operating in Spain by orchestrating bank-specific
  Selenium, BeautifulSoup, OCR, Pandas, and LLM pipelines.
- Implemented an OCR and image-based extraction pipeline that substantially
  reduced processing costs on selected runs while preserving the structured CSV
  and two-sheet Excel reporting workflow.
- Improved the reliability of an LLM-assisted financial-data pipeline by
  combining function calling, deterministic validation, LLM-as-judge
  experiments, human review, monitoring, and failure alerts.

## Evidence gaps

- Confirm whether the older references to economic and macroeconomic datasets
  and REST APIs belong to this project or to a separate application.
- Recover the exact bank and product counts for a given weekly run.
- Recover the original validation cases, fields, and client acceptance criteria.
- Recover the cost comparison between the original and OCR pipelines.
- Confirm whether retries and repeated tool calls formed a formal agent loop.
- Treat the historical `100% data accuracy` CV claim as unverified until its
  validation method, sample size, and measurement period are recovered.
