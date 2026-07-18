---
id: project-ai-document-support-assistant
name: AI Document Support Assistant
aliases:
  - RAG Ticket Support Assistant
  - Internal Document Recommendation Assistant
type: client-project
organization: Innovery
duration: 3 months
status: draft
sources:
  - archive/previous-cvs/CV Vincenzo 2025.pdf
  - archive/previous-cvs/CV Vincenzo Actualizado - Copy.pdf
  - archive/previous-cvs/CV Vincenzo Actualizado ENG.pdf
  - user-confirmed: 2026-07-17
evidence_checked: 2026-07-17
---

# AI Document Support Assistant

## Problem

Support teams needed a faster way to find the correct internal procedures and
documentation while resolving incidents. The source material was distributed
across internal PDFs, making manual retrieval slow, dependent on individual
knowledge, and difficult to connect consistently with ticket categories and
resolution steps.

The three-month project began shortly after Retrieval-Augmented Generation had
emerged as a practical architecture and capable AI APIs had become available.
At the time, the approach was comparatively new and model inference was
expensive enough for retrieval quality, chunking, and context size to affect
product viability.

## What the application does

The application ingests and chunks internal PDF documentation, generates vector
representations, and stores searchable knowledge in Weaviate. LangChain
orchestrated the AI API with the support ticket, its category, retrieved
document chunks, and available application functions to decide which resources
to recommend.

The ticketing integration automatically publishes the top three recommended
documents in a comment on the ticket, including direct links for internal
support staff. The team also provided a chatbot through a custom frontend. The
linked conversational experience used the document and ticket context so staff
could ask follow-up questions and receive AI-assisted resolution guidance.

The project also organized and categorized tickets and represented structured
relationships between tickets, document metadata, categories, and vectorized
content in Weaviate. It progressed beyond a one-off internal chatbot into a
reusable product concept that could be offered to other organizations.

## Solution

- Python and FastAPI backend for document ingestion, retrieval, ticket context,
  and conversational endpoints.
- PDF parsing, chunking, embeddings, vectorization, and metadata enrichment.
- Weaviate vector storage for semantic retrieval and structured knowledge
  organization.
- LangChain orchestration around an AI API, retrieval functions, recommendation
  logic, and context assembly.
- Ticket-driven automation that posts the top three relevant documents directly
  as a ticket comment.
- A custom frontend and API flow for chatting with the recommended document in
  the context of the active support ticket.
- Retrieval and context optimizations intended to improve relevance while
  controlling the token and inference cost of early AI API usage.

## My contribution

- Implemented core RAG foundations, including PDF chunking, vectorization,
  Weaviate ingestion and retrieval, metadata relationships, and knowledge
  categorization.
- Built and optimized Python and FastAPI endpoints for document processing,
  ticket integration, recommendation, and conversational access.
- Integrated LangChain with an AI API, retrieval, and application functions so
  the model could select relevant supporting resources from ticket context.
- Connected retrieval results to the internal open-source ticketing platform,
  automatically surfacing the top three documents, resolution guidance, and
  direct download links in ticket comments.
- Collaborated on the custom chatbot frontend by implementing the API used to
  converse with the document and active ticket context.
- Iterated on chunking, retrieval, and context construction to balance answer
  quality against the comparatively high AI API cost at the time.

## Outcome

- Delivered an early end-to-end RAG implementation during a three-month project,
  from ingestion and vector storage to ticket automation and conversational
  support.
- Embedded AI assistance inside the existing support workflow rather than
  requiring staff to search a separate knowledge portal.
- Reduced the recommendation set to the top three contextually relevant
  documents for human review within each ticket.
- Produced a reusable product concept for document-grounded support assistance.

The CVs describe improved support efficiency, but they do not provide a verified
time-to-resolution, retrieval-quality, adoption, or usage metric.

## Technologies

- Python
- FastAPI
- Pandas
- LangChain
- AI APIs
- Weaviate
- PDF processing
- Document chunking
- Embeddings and vectorization
- Vector search
- Retrieval-Augmented Generation (RAG)
- Semantic search
- Metadata filtering and knowledge categorization
- Context management
- Tool and function orchestration
- Ticketing integration
- REST APIs
- Custom AI application scaffolding

## Agent and tool-use classification

The following categories from the agent and tool-use questionnaire are supported
by the current evidence:

- Tool calling / function calling: the LLM operated with retrieval,
  recommendation, ticket-context, and document-access functions. The exact
  provider-native function-calling API remains to be confirmed.
- Context management: the system assembled ticket data, categories, retrieved
  chunks, document metadata, and conversational context within API limits.
- Triggers / automation workflows: ticket activity drove automatic top-three
  document recommendations posted as comments in the existing workflow.
- Memory / retrieval / RAG: the core architecture used chunking, embeddings,
  Weaviate vector retrieval, LangChain, and grounded generation.
- Custom agent harnesses or scaffolding: the team built its own ingestion,
  retrieval, prompt and function orchestration, FastAPI layer, ticket adapter,
  and chatbot integration instead of relying on a complete packaged product.

Agent loops are not currently supported by the evidence. The system performed
retrieval and function-guided recommendation, but no autonomous iterative loop
has been described.

## AI evaluation and testing classification

- Human review is supported: support staff received the top-three documents in
  the ticket and remained responsible for choosing and applying the guidance.
- Quality checks are plausible through iterative relevance review during the
  project, but the exact acceptance process is not documented yet.
- AI API cost influenced chunking and context optimization, but formal cost or
  latency tracking has not been confirmed.
- No current evidence supports formal test sets, graders or evaluators,
  LLM-as-judge, tracing or logging as an AI evaluation method, or regression
  testing of retrieval quality.

## Reusable resume bullets

- Implemented an early RAG support assistant that surfaced the top three relevant
  documents directly in support tickets by implementing PDF chunking, AI API
  integration, LangChain orchestration, Weaviate retrieval, and FastAPI
  integrations.
- Delivered a three-month document-grounded support prototype spanning vector
  ingestion, semantic retrieval, ticket comments, and conversational APIs,
  turning internal PDF knowledge into a reusable AI product concept.

## Evidence gaps

- Identify the open-source ticketing platform by name if it can be disclosed.
- Confirm the embedding model, PDF parser, chunking strategy, retrieval `top_k`,
  metadata filters, reranking behavior, and exact AI API integration.
- Confirm the document and ticket volume, number of users, response time,
  retrieval relevance, adoption, and measurable effect on ticket resolution.
- Recover any test set, manual relevance rubric, logging, tracing, cost data, or
  regression checks used during development.
- Confirm whether the product concept was demonstrated, sold, piloted, or
  deployed for clients beyond the internal support workflow.
