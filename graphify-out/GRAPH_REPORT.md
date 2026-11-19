# Graph Report - invoice-extract  (2026-11-19)

## Corpus Check
- 87 files · ~23,883 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 592 nodes · 1319 edges · 55 communities (54 shown, 1 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 173 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- CDR
- file_upload/config/module.py
- UploadedFile
- SqlAlchemyJobRepository
- Invoice_Bill_Receipt_Extraction_Architecture_Blueprint.md
- rest/mappers.py
- 24. Detailed Delivery Roadmap and Definition of Done
- 7. Image Reader — First Implementation Milestone
- 14. LangGraph Orchestration — Complete Workflow Design
- 6. Reader Abstraction and Common Document Representation (CDR)
- JobRepository
- 13. Normalization, Validation and Financial Controls
- 15. API Design, Contracts and HTTP Semantics
- 25. Failure Playbooks / Operational Runbooks
- 📑 Invoice Extract API
- .save_to_path
- 11. Canonical Financial JSON Schema v1
- 12. LangChain and LLM Extraction Design
- 17. Background Jobs, Queue and Worker Runtime
- 18. Production Security, Privacy and Compliance Design
- 1. Problem, Goals, and Boundaries
- 8. DOCX Reader — Second Implementation Milestone
- 9. PDF Reader — Third Implementation Milestone
- 10. Document Classification and Scope Gate
- 16. Database Design and Persistence
- 19. Observability, Quality, SLOs and Cost
- 20. Testing, Evaluation Dataset and Release Gates
- 4. End-to-End User Journey and State Machines
- 5. Ingestion Design — Detailed Contract
- 3. System Context and Deployment Model
- Invoice / Bill / Receipt Extraction Microservice
- .save_to_path
- invoice-extract
- Invoice extraction repository instructions
- UploadFile
- file_upload/adapters/inbound/rest/router.py
- LangGraphProcessor
- file_upload/config/module.py
- FileRepositoryPort
- GetFileInput
- Implementation status against Blueprint V1.0

## God Nodes (most connected - your core abstractions)
1. `CDR` - 47 edges
2. `UploadedFile` - 35 edges
3. `ExtractionError` - 25 edges
4. `FileView` - 25 edges
5. `FileRepositoryPort` - 24 edges
6. `LangGraphProcessor` - 23 edges
7. `ExtractionPayload` - 22 edges
8. `SqlAlchemyJobRepository` - 20 edges
9. `ReaderStatus` - 20 edges
10. `PdfReader` - 19 edges

## Surprising Connections (you probably didn't know these)
- `FakeExtractor` --uses--> `LangGraphProcessor`  [INFERRED]
  tests/test_extraction.py → src/modules/extraction/adapters/outbound/orchestration/langgraph_processor.py
- `FakeOCR` --uses--> `LangGraphProcessor`  [INFERRED]
  tests/test_extraction.py → src/modules/extraction/adapters/outbound/orchestration/langgraph_processor.py
- `RepairingExtractor` --uses--> `LangGraphProcessor`  [INFERRED]
  tests/test_extraction.py → src/modules/extraction/adapters/outbound/orchestration/langgraph_processor.py
- `TestReaders` --uses--> `LangGraphProcessor`  [INFERRED]
  tests/test_extraction.py → src/modules/extraction/adapters/outbound/orchestration/langgraph_processor.py
- `TestFileUploadHexagonal` --uses--> `UploadFileInput`  [INFERRED]
  tests/test_file_upload.py → src/modules/file_upload/application/dto/commands.py

## Import Cycles
- None detected.

## Communities (55 total, 1 thin omitted)

### Community 0 - "CDR"
Cohesion: 0.08
Nodes (48): Decimal, LangChainExtractor, LLM adapter: source text is data and has no tools or execution privileges., Application orchestration; adapters are injected and graph nodes stay small., DocxReader, Path, ImageReader, Path (+40 more)

### Community 1 - "file_upload/config/module.py"
Cohesion: 0.15
Nodes (14): commands — application input DTOs for state mutations., Input payload to upload a new file., UploadFileInput, FileView, results — application output DTOs (views) decoupling domain model from callers., Read view of an uploaded file., Protocol, upload_file — inbound port (interface) for uploading files. (+6 more)

### Community 2 - "UploadedFile"
Cohesion: 0.08
Nodes (28): Session, file_repository — SQLAlchemy persistence adapter implementing FileRepositoryPort, PostgreSQL adapter for file persistence., SqlAlchemyFileRepository, mappers — bidirectional mapping between ORM model and domain entity., to_domain(), to_model(), update_model() (+20 more)

### Community 3 - "SqlAlchemyJobRepository"
Cohesion: 0.14
Nodes (12): Session, SqlAlchemyJobRepository, ExtractionJobModel, ExtractionResultModel, Base, ensure_transition(), JobStatus, Enum (+4 more)

### Community 4 - "Invoice_Bill_Receipt_Extraction_Architecture_Blueprint.md"
Cohesion: 0.13
Nodes (14): 21. Suggested Repository / Package Structure, 22.1 Categories of configuration, 22.2 Environments, 22. Configuration and Environment Profiles, 23. Technology Selection — Reasons, Alternatives, Lock-In, 26. What We Have NOT Fully Decided Yet (Explicit Open Questions), 27. Architecture Review Checklist (For Mentor / Engineer), 28. Compact Architectural Decision Summary (One Page) (+6 more)

### Community 5 - "rest/mappers.py"
Cohesion: 0.42
Nodes (4): Validate untrusted upload bytes before the existing upload use case persists the, UploadValidationError, validate_upload(), TestUploadValidation

### Community 6 - "24. Detailed Delivery Roadmap and Definition of Done"
Cohesion: 0.20
Nodes (10): 24. Detailed Delivery Roadmap and Definition of Done, Milestone 0 — Existing Upload Service: verify and freeze, Milestone 1 — Image Reader V1 (NEXT WORK), Milestone 2 — DOCX Reader, Milestone 3 — PDF Reader, Milestone 4 — Classification + Schema, Milestone 5 — LangChain Extraction, Milestone 6 — Business Validation (+2 more)

### Community 7 - "7. Image Reader — First Implementation Milestone"
Cohesion: 0.20
Nodes (10): 7.1 Responsibilities, 7.2 Image Reader pipeline, 7.3 Substeps and inputs/outputs, 7.4 OCR approach, 7.5 OCR quality policy — agreed design, 7.6 Severity-based fallback — agreed design, 7.7 OCR vs Vision conflict, 7.8 Image-specific edge cases (+2 more)

### Community 8 - "14. LangGraph Orchestration — Complete Workflow Design"
Cohesion: 0.25
Nodes (8): 14.1 Why LangGraph, 14.2 Workflow diagram, 14.3 Node contract table, 14.4 State model, 14.5 Graph persistence and checkpointing, 14.6 Retry strategy, 14.7 Human review integration (optional initially), 14. LangGraph Orchestration — Complete Workflow Design

### Community 9 - "6. Reader Abstraction and Common Document Representation (CDR)"
Cohesion: 0.25
Nodes (8): 6.1 Core principle, 6.2 Reader interface — logical, not code, 6.3 Proposed CDR v1 contract, 6.4 Minimum logical block types, 6.5 CDR partial-content policy, 6. Reader Abstraction and Common Document Representation (CDR), CDR design rules, Why CDR matters

### Community 10 - "JobRepository"
Cohesion: 0.08
Nodes (34): create_extraction(), CreateRequest, get_cdr(), get_extraction(), Options, BaseModel, HTTP adapter translating requests into application use cases., respond() (+26 more)

### Community 11 - "13. Normalization, Validation and Financial Controls"
Cohesion: 0.29
Nodes (7): 13.1 Separate three questions, 13.2 Validation layers, 13.3 Indian financial document details, 13.4 Arithmetic correctness, 13.5 What happens if the model is wrong?, 13.6 Confidence vs reliability, 13. Normalization, Validation and Financial Controls

### Community 12 - "15. API Design, Contracts and HTTP Semantics"
Cohesion: 0.29
Nodes (7): 15.1 Separate file upload from extraction, 15.2 Create extraction request, 15.3 Error response contract, 15.4 Error-to-HTTP mapping (proposed), 15.5 Webhook option (future), 15.6 API versioning, 15. API Design, Contracts and HTTP Semantics

### Community 13 - "25. Failure Playbooks / Operational Runbooks"
Cohesion: 0.29
Nodes (7): 25.1 Uploaded file exists but DB row is `PENDING`, 25.2 Job stuck in `PROCESSING`, 25.3 OCR gives text but financial totals are wrong, 25.4 Vision provider unavailable, 25.5 DB unavailable during finalization, 25.6 Sensitive document accidentally logged or exposed, 25. Failure Playbooks / Operational Runbooks

### Community 14 - "📑 Invoice Extract API"
Cohesion: 0.29
Nodes (6): 📌 Available Endpoints in Swagger UI, Extraction pipeline, 📑 Invoice Extract API, 🚀 Running with Docker Compose, 🌐 Swagger UI & Interactive Documentation, 🧪 Testing File Upload via cURL

### Community 15 - ".save_to_path"
Cohesion: 0.16
Nodes (9): LocalDiskFileStorage, BinaryIO, Path, local_storage — physical volume storage adapter implementing FileStoragePort., Storage adapter persisting files to disk / mounted Docker volume., Pre-computes the target absolute path., Write and flush a sibling temporary file, then atomically rename., get_file_storage() (+1 more)

### Community 16 - "11. Canonical Financial JSON Schema v1"
Cohesion: 0.33
Nodes (6): 11.1 Design objectives, 11.2 Proposed data fields, 11.3 Example full response (fictional), 11.4 Invoice vs bill vs receipt extensions, 11.5 Provenance model, 11. Canonical Financial JSON Schema v1

### Community 17 - "12. LangChain and LLM Extraction Design"
Cohesion: 0.33
Nodes (6): 12.1 LLM role, 12.2 Extraction stages, 12.3 Prompt and model policies, 12.4 Long/multi-page documents, 12.5 Hallucination and prompt-injection handling, 12. LangChain and LLM Extraction Design

### Community 18 - "17. Background Jobs, Queue and Worker Runtime"
Cohesion: 0.33
Nodes (6): 17.1 When to introduce Celery/Redis, 17.2 Worker responsibilities, 17.3 Concurrency isolation, 17.4 Cancellation, timeout and retry ownership, 17.5 Storage migration path, 17. Background Jobs, Queue and Worker Runtime

### Community 19 - "18. Production Security, Privacy and Compliance Design"
Cohesion: 0.33
Nodes (6): 18.1 Threat model overview, 18.2 Authentication/authorization rollout, 18.3 Sensitive document policy, 18.4 Permanent storage decision, 18.5 Dependency and runtime hygiene, 18. Production Security, Privacy and Compliance Design

### Community 20 - "1. Problem, Goals, and Boundaries"
Cohesion: 0.33
Nodes (6): 1.1 Business problem, 1.2 Functional goals, 1.3 Nonfunctional goals, 1.4 Document scope, 1.5 Technical scope and non-goals, 1. Problem, Goals, and Boundaries

### Community 21 - "8. DOCX Reader — Second Implementation Milestone"
Cohesion: 0.33
Nodes (6): 8.1 Scope, 8.2 Pipeline, 8.3 Key requirements, 8.4 Alternative: DOCX → PDF conversion, 8.5 DOCX Reader acceptance criteria, 8. DOCX Reader — Second Implementation Milestone

### Community 22 - "9. PDF Reader — Third Implementation Milestone"
Cohesion: 0.33
Nodes (6): 9.1 Why PDF comes after Image Reader, 9.2 PDF page-routing pipeline, 9.3 Detailed behavior, 9.4 Complex PDF situations, 9.5 PDF Reader acceptance criteria, 9. PDF Reader — Third Implementation Milestone

### Community 23 - "10. Document Classification and Scope Gate"
Cohesion: 0.40
Nodes (5): 10.1 Why classification is needed, 10.2 Output classes, 10.3 Classification strategy, 10.4 Rules of separation, 10. Document Classification and Scope Gate

### Community 24 - "16. Database Design and Persistence"
Cohesion: 0.40
Nodes (5): 16.1 Core tables, 16.2 Relationship diagram, 16.3 Indexing, migrations and access, 16.4 Atomic job submission and queue consistency, 16. Database Design and Persistence

### Community 25 - "19. Observability, Quality, SLOs and Cost"
Cohesion: 0.40
Nodes (5): 19.1 Tracing, 19.2 Metrics, 19.3 Quality objectives, 19.4 Cost controls, 19. Observability, Quality, SLOs and Cost

### Community 26 - "20. Testing, Evaluation Dataset and Release Gates"
Cohesion: 0.40
Nodes (5): 20.1 Test pyramid, 20.2 Representative benchmark set, 20.3 Ground-truth annotation strategy, 20.4 Practical release gates, 20. Testing, Evaluation Dataset and Release Gates

### Community 27 - "4. End-to-End User Journey and State Machines"
Cohesion: 0.40
Nodes (5): 4.1 Main journey, 4.2 Upload lifecycle — **separate** from extraction, 4.3 Extraction job lifecycle, 4.4 Consistency and crash recovery, 4. End-to-End User Journey and State Machines

### Community 28 - "5. Ingestion Design — Detailed Contract"
Cohesion: 0.40
Nodes (5): 5.1 File support matrix, 5.2 Validation order, 5.3 Storage, 5.4 Duplicate behavior and idempotency, 5. Ingestion Design — Detailed Contract

### Community 29 - "3. System Context and Deployment Model"
Cohesion: 0.50
Nodes (4): 3.1 Logical architecture, 3.2 Architecture style, 3.3 Component responsibility boundaries, 3. System Context and Deployment Model

### Community 30 - "Invoice / Bill / Receipt Extraction Microservice"
Cohesion: 0.50
Nodes (4): Contents, Executive Summary, Full Architecture & Engineering Design Blueprint (V1.0), Invoice / Bill / Receipt Extraction Microservice

### Community 31 - ".save_to_path"
Cohesion: 0.08
Nodes (25): FastAPI, health_check(), lifespan(), Redirect root path to interactive Swagger documentation., Health check endpoint to verify API server is alive., Application lifespan context for startup and shutdown routines., redirect_to_swagger(), BaseModel (+17 more)

### Community 46 - "Invoice extraction repository instructions"
Cohesion: 0.40
Nodes (4): Architecture, Graphify, Invoice extraction repository instructions, Verification

### Community 48 - "UploadFile"
Cohesion: 0.13
Nodes (11): FileStoragePort, BinaryIO, Protocol, file_storage_port — outbound port (interface) for physical file volume storage., Saves stream to the designated target path and returns total bytes written., Removes physical file from storage., Checks existence of file on storage., Pre-computes the target storage path before physical save. (+3 more)

### Community 49 - "file_upload/adapters/inbound/rest/router.py"
Cohesion: 0.25
Nodes (12): mappers — transforms application view DTOs into REST response schemas., to_file_list_response(), to_file_response(), get_file(), router — HTTP REST inbound adapter exposing file upload and retrieval endpoints., upload_file(), ErrorDetail, FileListResponse (+4 more)

### Community 50 - "LangGraphProcessor"
Cohesion: 0.31
Nodes (4): LangGraphProcessor, Path, WorkflowState, TypedDict

### Community 51 - "file_upload/config/module.py"
Cohesion: 0.23
Nodes (10): list_files(), ListFilesInput, Input query to list files with pagination., ListFilesQuery, Protocol, list_files — inbound port (interface) for listing files., ListFiles, Implements ListFilesQuery inbound port. (+2 more)

### Community 52 - "FileRepositoryPort"
Cohesion: 0.18
Nodes (7): FileRepositoryPort, Protocol, GetFile, Implements GetFileQuery inbound port., get_file_repository(), get_get_file_query(), Session

### Community 53 - "GetFileInput"
Cohesion: 0.29
Nodes (7): download_file(), GetFileInput, queries — application input DTOs for read requests., Input query to fetch file by ID., GetFileQuery, Protocol, get_file — inbound port (interface) for retrieving single file metadata.

### Community 54 - "Implementation status against Blueprint V1.0"
Cohesion: 0.50
Nodes (3): Implementation status against Blueprint V1.0, Next release gates, Verification

## Knowledge Gaps
- **135 isolated node(s):** `invoice-extract`, `Architecture`, `Graphify`, `Verification`, `Full Architecture & Engineering Design Blueprint (V1.0)` (+130 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CDR` connect `CDR` to `JobRepository`, `SqlAlchemyJobRepository`, `LangGraphProcessor`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `UploadedFile` connect `UploadedFile` to `UploadFile`, `file_upload/config/module.py`, `FileRepositoryPort`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `FileStoragePort` connect `UploadFile` to `file_upload/config/module.py`, `file_upload/config/module.py`, `.save_to_path`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `CDR` (e.g. with `CreateRequest` and `Options`) actually correct?**
  _`CDR` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `UploadedFile` (e.g. with `SqlAlchemyFileRepository` and `FileRepositoryPort`) actually correct?**
  _`UploadedFile` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `ExtractionError` (e.g. with `CreateRequest` and `Options`) actually correct?**
  _`ExtractionError` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `FileView` (e.g. with `GetFileQuery` and `ListFilesQuery`) actually correct?**
  _`FileView` has 6 INFERRED edges - model-reasoned connections that need verification._