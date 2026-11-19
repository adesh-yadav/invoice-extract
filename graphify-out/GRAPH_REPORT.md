# Graph Report - invoice-extract  (2026-11-19)

## Corpus Check
- 101 files · ~33,784 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 731 nodes · 1725 edges · 60 communities (56 shown, 4 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 216 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9591d0c0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- CDR
- LangGraphProcessor
- LangGraphProcessor
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
- e2e_smoke.py
- Invoice extraction job analysis
- uploaded_file.py
- file_upload/config/module.py
- FileView
- web/__init__.py
- Implementation status against Blueprint V1.0
- ollama-model.sh
- file_upload/config/module.py
- rest/mappers.py
- JPEG OCR case: text mila, financial extraction kyun ruki
- .save_to_path

## God Nodes (most connected - your core abstractions)
1. `CDR` - 74 edges
2. `UploadedFile` - 35 edges
3. `SqlAlchemyJobRepository` - 32 edges
4. `Page` - 29 edges
5. `TextBlock` - 28 edges
6. `LangGraphProcessor` - 26 edges
7. `ExtractionError` - 25 edges
8. `FileView` - 25 edges
9. `TestReaders` - 25 edges
10. `TesseractOCR` - 24 edges

## Surprising Connections (you probably didn't know these)
- `FakeExtractor` --uses--> `LangGraphProcessor`  [INFERRED]
  tests/test_extraction.py → src/modules/extraction/adapters/outbound/orchestration/langgraph_processor.py
- `FakeOCR` --uses--> `LangGraphProcessor`  [INFERRED]
  tests/test_extraction.py → src/modules/extraction/adapters/outbound/orchestration/langgraph_processor.py
- `RepairingExtractor` --uses--> `LangGraphProcessor`  [INFERRED]
  tests/test_extraction.py → src/modules/extraction/adapters/outbound/orchestration/langgraph_processor.py
- `TestReaders` --uses--> `LangGraphProcessor`  [INFERRED]
  tests/test_extraction.py → src/modules/extraction/adapters/outbound/orchestration/langgraph_processor.py
- `TestJobPersistence` --uses--> `SqlAlchemyJobRepository`  [INFERRED]
  tests/test_job_persistence.py → src/modules/extraction/adapters/outbound/persistence/job_repository.py

## Import Cycles
- None detected.

## Communities (60 total, 4 thin omitted)

### Community 0 - "CDR"
Cohesion: 0.07
Nodes (51): Decimal, LangChainExtractor, BaseChatModel, LLM adapter: source text is data and has no tools or execution privileges., DocxReader, Path, ImageReader, Path (+43 more)

### Community 1 - "LangGraphProcessor"
Cohesion: 0.18
Nodes (36): banner(), byId(), card(), checkService(), clear(), fetchJob(), field(), human() (+28 more)

### Community 2 - "LangGraphProcessor"
Cohesion: 0.14
Nodes (11): LangGraphProcessor, Path, Application orchestration; adapters are injected and graph nodes stay small., WorkflowState, A short-lived DB session per event keeps LangGraph nodes independent of the work, SqlAlchemyProcessingEventSink, ProcessingEventSink, Protocol (+3 more)

### Community 3 - "SqlAlchemyJobRepository"
Cohesion: 0.06
Nodes (37): FastAPI, FileResponse, health_check(), lifespan(), Open the extraction dashboard; API docs remain at /docs., Health check endpoint to verify API server is alive., Application lifespan context for startup and shutdown routines., redirect_to_dashboard() (+29 more)

### Community 4 - "Invoice_Bill_Receipt_Extraction_Architecture_Blueprint.md"
Cohesion: 0.11
Nodes (18): 21. Suggested Repository / Package Structure, 22.1 Categories of configuration, 22.2 Environments, 22. Configuration and Environment Profiles, 23. Technology Selection — Reasons, Alternatives, Lock-In, 26. What We Have NOT Fully Decided Yet (Explicit Open Questions), 27. Architecture Review Checklist (For Mentor / Engineer), 28. Compact Architectural Decision Summary (One Page) (+10 more)

### Community 5 - "rest/mappers.py"
Cohesion: 0.10
Nodes (18): Session, file_repository — SQLAlchemy persistence adapter implementing FileRepositoryPort, PostgreSQL adapter for file persistence., SqlAlchemyFileRepository, mappers — bidirectional mapping between ORM model and domain entity., to_domain(), to_model(), update_model() (+10 more)

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
Cohesion: 0.06
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
Cohesion: 0.22
Nodes (8): 📌 Available Endpoints in Swagger UI, Extraction pipeline, 📑 Invoice Extract API, Local document workspace, 🚀 Running with Docker Compose, 🌐 Swagger UI & Interactive Documentation, 🧪 Testing File Upload via cURL, Text from any supported document

### Community 15 - ".save_to_path"
Cohesion: 0.18
Nodes (8): LocalDiskFileStorage, BinaryIO, Path, local_storage — physical volume storage adapter implementing FileStoragePort., Storage adapter persisting files to disk / mounted Docker volume., Pre-computes the target absolute path., Write and flush a sibling temporary file, then atomically rename., TestLocalStorage

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
Cohesion: 0.42
Nodes (4): Validate untrusted upload bytes before the existing upload use case persists the, UploadValidationError, validate_upload(), TestUploadValidation

### Community 31 - ".save_to_path"
Cohesion: 0.15
Nodes (13): Session, SqlAlchemyJobRepository, ExtractionEventModel, ExtractionJobModel, ExtractionResultModel, ExtractionSourceModel, Base, ensure_transition() (+5 more)

### Community 46 - "Invoice extraction repository instructions"
Cohesion: 0.40
Nodes (4): Architecture, Graphify, Invoice extraction repository instructions, Verification

### Community 48 - "e2e_smoke.py"
Cohesion: 0.36
Nodes (9): Client, Response, docx_bytes(), image_bytes(), main(), pdf_bytes(), process(), Run synthetic upload-to-result checks against a locally running API. (+1 more)

### Community 49 - "Invoice extraction job analysis"
Cohesion: 0.14
Nodes (13): ₹1.00 ka TOTAL_MISMATCH exactly kaise bana, Claude ne kya extract kiya, Code mein provider ke default model names, Configured aur actually used ka farq, Data kahan store hua hai?, Is case mein kya review karna chahiye?, Job ka exact timeline: pehle kya hua, phir kya hua, Job report: invoice extraction ka complete flow (+5 more)

### Community 50 - "uploaded_file.py"
Cohesion: 0.15
Nodes (15): DomainError, InvalidFileNameError, InvalidStatusTransitionError, Exception, exceptions — domain level errors for file upload., Raised when original filename is empty or invalid., Raised when an illegal lifecycle state transition is attempted., Base domain exception. (+7 more)

### Community 51 - "file_upload/config/module.py"
Cohesion: 0.12
Nodes (23): download_file(), get_file(), list_files(), router — HTTP REST inbound adapter exposing file upload and retrieval endpoints., upload_file(), commands — application input DTOs for state mutations., Input payload to upload a new file., UploadFileInput (+15 more)

### Community 52 - "FileView"
Cohesion: 0.17
Nodes (11): FileView, results — application output DTOs (views) decoupling domain model from callers., Read view of an uploaded file., GetFile, get_file — use case for retrieving a single file view., Implements GetFileQuery inbound port., ListFiles, list_files — use case for retrieving paginated file views. (+3 more)

### Community 54 - "Implementation status against Blueprint V1.0"
Cohesion: 0.50
Nodes (3): Implementation status against Blueprint V1.0, Next release gates, Verification

### Community 56 - "file_upload/config/module.py"
Cohesion: 0.15
Nodes (12): FileStoragePort, Protocol, file_storage_port — outbound port (interface) for physical file volume storage., Removes physical file from storage., Checks existence of file on storage., Pre-computes the target storage path before physical save., upload_file — use case coordinating the upload lifecycle., Implements UploadFileUseCase inbound port. (+4 more)

### Community 57 - "rest/mappers.py"
Cohesion: 0.31
Nodes (9): mappers — transforms application view DTOs into REST response schemas., to_file_list_response(), to_file_response(), ErrorDetail, FileListResponse, FileUploadResponse, BaseModel, responses — HTTP REST response schemas with OpenAPI / Swagger documentation meta (+1 more)

### Community 58 - "JPEG OCR case: text mila, financial extraction kyun ruki"
Cohesion: 0.33
Nodes (5): JPEG OCR case: text mila, financial extraction kyun ruki, Kaise dekhein?, Kya fix hua?, Kya hua tha?, Naye job ka actual verification

## Knowledge Gaps
- **155 isolated node(s):** `invoice-extract`, `ollama-model.sh script`, `terminalStatuses`, `state`, `jobFromUrl` (+150 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CDR` connect `CDR` to `JobRepository`, `LangGraphProcessor`, `.save_to_path`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `UploadedFile` connect `rest/mappers.py` to `file_upload/config/module.py`, `uploaded_file.py`, `FileView`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `UploadedFileModel` connect `rest/mappers.py` to `CDR`, `JobRepository`, `SqlAlchemyJobRepository`, `.save_to_path`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `CDR` (e.g. with `CreateRequest` and `Options`) actually correct?**
  _`CDR` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `UploadedFile` (e.g. with `SqlAlchemyFileRepository` and `FileRepositoryPort`) actually correct?**
  _`UploadedFile` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `SqlAlchemyJobRepository` (e.g. with `ExtractionEventModel` and `ExtractionJobModel`) actually correct?**
  _`SqlAlchemyJobRepository` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Page` (e.g. with `DocxReader` and `TesseractOCR`) actually correct?**
  _`Page` has 9 INFERRED edges - model-reasoned connections that need verification._