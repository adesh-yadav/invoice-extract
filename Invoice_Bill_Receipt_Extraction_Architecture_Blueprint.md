# Invoice / Bill / Receipt Extraction Microservice
## Full Architecture & Engineering Design Blueprint (V1.0)

> **Project:** Financial Document Understanding Service  
> **Technology:** Python, FastAPI, PostgreSQL, LangChain, LangGraph, OCR, Vision AI  
> **Document type:** Architecture / engineering specification — **no implementation code**  
> **Prepared:** 19 November 2026  
> **Intended reader:** Developer, solution architect, reviewer, technical lead  
> **Status:** Design baseline. Decisions explicitly marked *proposed* or *open* require validation before production.

---

## Contents

- [1. Problem, Goals, and Boundaries](#1-problem-goals-and-boundaries)
- [2. Current Project State and Decisions Already Made](#2-current-project-state-and-decisions-already-made)
- [3. System Context and Deployment Model](#3-system-context-and-deployment-model)
- [4. End-to-End User Journey and State Machines](#4-end-to-end-user-journey-and-state-machines)
- [5. Ingestion Design — Detailed Contract](#5-ingestion-design--detailed-contract)
- [6. Reader Abstraction and Common Document Representation (CDR)](#6-reader-abstraction-and-common-document-representation-cdr)
- [7. Image Reader — First Implementation Milestone](#7-image-reader--first-implementation-milestone)
- [8. DOCX Reader — Second Implementation Milestone](#8-docx-reader--second-implementation-milestone)
- [9. PDF Reader — Third Implementation Milestone](#9-pdf-reader--third-implementation-milestone)
- [10. Document Classification and Scope Gate](#10-document-classification-and-scope-gate)
- [11. Canonical Financial JSON Schema v1](#11-canonical-financial-json-schema-v1)
- [12. LangChain and LLM Extraction Design](#12-langchain-and-llm-extraction-design)
- [13. Normalization, Validation and Financial Controls](#13-normalization-validation-and-financial-controls)
- [14. LangGraph Orchestration — Complete Workflow Design](#14-langgraph-orchestration--complete-workflow-design)
- [15. API Design, Contracts and HTTP Semantics](#15-api-design-contracts-and-http-semantics)
- [16. Database Design and Persistence](#16-database-design-and-persistence)
- [17. Background Jobs, Queue and Worker Runtime](#17-background-jobs-queue-and-worker-runtime)
- [18. Production Security, Privacy and Compliance Design](#18-production-security-privacy-and-compliance-design)
- [19. Observability, Quality, SLOs and Cost](#19-observability-quality-slos-and-cost)
- [20. Testing, Evaluation Dataset and Release Gates](#20-testing-evaluation-dataset-and-release-gates)
- [21. Suggested Repository / Package Structure](#21-suggested-repository--package-structure)
- [22. Configuration and Environment Profiles](#22-configuration-and-environment-profiles)
- [23. Technology Selection — Reasons, Alternatives, Lock-In](#23-technology-selection--reasons-alternatives-lock-in)
- [24. Detailed Delivery Roadmap and Definition of Done](#24-detailed-delivery-roadmap-and-definition-of-done)
- [25. Failure Playbooks / Operational Runbooks](#25-failure-playbooks--operational-runbooks)
- [26. What We Have NOT Fully Decided Yet (Explicit Open Questions)](#26-what-we-have-not-fully-decided-yet-explicit-open-questions)
- [27. Architecture Review Checklist (For Mentor / Engineer)](#27-architecture-review-checklist-for-mentor--engineer)
- [28. Compact Architectural Decision Summary (One Page)](#28-compact-architectural-decision-summary-one-page)
- [29. References and Engineering Reading](#29-references-and-engineering-reading)
- [30. Final Build Instruction](#30-final-build-instruction)

---

## Executive Summary

Build **one independently deployable, modular microservice** that accepts a stored image/PDF/DOCX document and returns a **typed, evidence-backed, validated JSON** representation of an **invoice, bill, or receipt**. A separate upload interface already exists and is reused.

The processing architecture is deliberately separated into **file ingestion → document reading → document classification → business-field extraction → normalization/validation → result persistence/delivery**. **LangGraph** orchestrates the process. **LangChain** connects to an LLM for structured extraction. Deterministic Python components perform file inspection, parsers, OCR routing, and financial checks.

**Development order agreed with the project owner:** (1) existing upload service; (2) **Image Reader first**, (3) **DOCX Reader**, (4) **PDF Reader last** so PDF scans reuse OCR; (5) AI extraction and validation; (6) LangGraph and API integration; (7) operational hardening.

**Important distinction:** An accepted file upload is **not** a successful financial extraction. File lifecycle and extraction-job lifecycle are separate.

---

# 1. Problem, Goals, and Boundaries

### 1.1 Business problem

Financial documents arrive with inconsistent layouts and formats. Users upload photographs, scans, digital PDFs, and Word invoices. The downstream application requires one stable JSON contract without manually reading each file.

**Example journey:** a merchant uploads a JPEG receipt; the service reads it, classifies it as a receipt, extracts merchant/date/items/paid total, validates evidence and arithmetic where possible, and exposes a result under an extraction job ID.

### 1.2 Functional goals

1. Accept supported uploaded files and reference them by immutable `file_id`.
2. Read **JPG/JPEG/PNG**, **DOCX**, and **PDF** (digital, scanned, and mixed).
3. Extract text, text positions where possible, table structures where possible, and page references.
4. Identify **invoice**, **bill**, **receipt**, or **unsupported/unknown** content.
5. Extract seller, buyer, document number/date, tax, items, totals, and payment details when present.
6. Return one versioned JSON schema regardless of input format.
7. Preserve the difference between **missing**, **unreadable**, **conflicting**, and **verified** data.
8. Never fabricate a missing financial value to complete a response.
9. Persist job status, result, warnings, extraction method, model/prompt versions and references to evidence.
10. Handle recoverable errors, partial documents, reprocessing, and deterministic retries.

### 1.3 Nonfunctional goals

- **Correctness:** prioritize trustworthy amounts and traceable values over plausible guesses.
- **Safety:** isolate untrusted uploaded files and ignore instructions embedded inside documents.
- **Observability:** trace what happened to each file/job and which provider/model was used.
- **Cost:** avoid OCR/vision on already-readable digital PDFs; bound paid AI calls.
- **Latency:** support synchronous development tests, asynchronous production jobs.
- **Maintainability:** replace parsers, OCR, storage, or LLM independently.
- **Scalability:** separate HTTP request handling from CPU-heavy OCR and external model calls.
- **Recoverability:** do not lose track of in-flight jobs when workers crash.

### 1.4 Document scope

| Category | V1 | Notes |
|---|---|---|
| Tax/commercial invoices | Yes | Including common Indian GST invoices |
| Bills | Yes | Utility, restaurant, retail, service bills where extractable |
| Receipts | Yes | Printed purchase/payment receipts |
| Multiple invoices in one file | **Not guaranteed V1** | Treat as a review case; future document splitting |
| Credit notes / debit notes / purchase orders | Outside default V1 | Introduce explicit types and fields if business requires |
| PAN cards, IDs, resumes, contracts | No | Upload may be valid; classification must reject as unsupported |
| Handwritten receipts | Best-effort / evaluation-dependent | No assumed reliability guarantee |
| Languages | English-first; Hindi/other languages evaluated | Configure OCR models and tests per language |

### 1.5 Technical scope and non-goals

**V1:** modular readers, common representation (CDR), extraction, validation, endpoints, jobs, statuses, tests.

**Not required initially:** vector database/RAG, multi-agent debate, invoice matching to ERP, bank reconciliation, automatic payment, custom model training, autonomous agents, semantic search, or an admin UI. These are not prerequisites for structured extraction.

**Deferred by owner:** authentication/JWT/user ownership **until production integration**; SHA-256-based content deduplication; dynamic customer-specific limits. Until authentication is added, run **only in a trusted, restricted development environment**, never on an open internet endpoint.

---

# 2. Current Project State and Decisions Already Made

## 2.1 What has actually been built

The owner demonstrated a successful upload/metadata response similar to:

```json
{
  "id": "14c22b56-4348-451f-a214-8d2793e2e8d2",
  "original_name": "ishnath_pan.jpeg",
  "stored_name": "14c22b56-4348-451f-a214-8d2793e2e8d2.jpeg",
  "file_extension": ".jpeg",
  "content_type": "image/jpeg",
  "file_size_bytes": 147420,
  "file_path": "/app/uploads/14c22b56-4348-451f-a214-8d2793e2e8d2.jpeg",
  "status": "SUCCESS",
  "error_message": null,
  "created_at": "2026-11-19T08:16:01.474329Z",
  "updated_at": "2026-11-19T08:16:01.492307Z"
}
```

This confirms that an upload succeeds and the API exposes useful metadata. It **does not prove**, by itself, that all promised validations, transaction/recovery scenarios, access controls, or persistence tests have passed. The PAN image is a valid **file-format** example, not a valid **financial-document** example.

## 2.2 Architecture decision register

| ADR | Decision | Status / interpretation |
|---|---|---|
| ADR-001 | Validate extension + MIME + actual format signature/structure | Accepted; MIME supplied by client is untrusted |
| ADR-002 | Limit file bytes **and** PDF page count | Accepted; exact production limits to benchmark |
| ADR-003 | Reject password-protected PDFs in MVP | Accepted; specific error, not “bad format” |
| ADR-004 | Use local file storage initially | Accepted for single-server MVP; **persistent mounted volume**, not ephemeral container files |
| ADR-005 | Generated unique ID; original filename as metadata | Accepted |
| ADR-006 | Defer content duplicate detection | Accepted; not the same as request-idempotency |
| ADR-007 | Retain originals indefinitely | Owner preference; **conditional for production**: deletion rights, purpose, encryption, costs, compliance and backups still required |
| ADR-008 | Token authentication/ownership checks later | Deferred for local/restricted development **only**, production blocker |
| ADR-009 | DB `PENDING` → file saved → DB `STORED`; recovery needed | Accepted target; validate implementation |
| ADR-010 | Recovery worker/schedule for stale uploads | Proposed, not yet selected by owner |
| ADR-011 | Inspect PDF at **page level**; native text where usable, OCR where not | Accepted |
| ADR-012 | Readers produce common text/blocks/tables/page/layout representation | Accepted |
| ADR-013 | Image Reader: OCR first, Vision fallback | Accepted |
| ADR-014 | Assess OCR using multiple quality signals | Accepted |
| ADR-015 | Severity-based targeted fallback for high-risk errors | Accepted; crop context and have full-page fallback |
| ADR-016 | Compare OCR/Vision with source; unresolved conflicts marked uncertain | Accepted |
| ADR-017 | Reader can return `PARTIAL` plus content and warnings | Accepted |
| ADR-018 | Implement Image → DOCX → PDF, reuse shared OCR | Accepted development sequence |
| ADR-019 | Separate `file_id` from `job_id`; normalize financial data into schema | Proposed baseline |
| ADR-020 | Start with one modular service, not three reader deployments | Proposed baseline |

> **Architect’s rule:** “Already decided”, “recommended”, “built”, and “tested” are four different states. Do not call a design decision implemented until it passes acceptance tests.

---

# 3. System Context and Deployment Model

## 3.1 Logical architecture

```mermaid
flowchart TD
  Client[Client / Frontend] --> API[FastAPI]
  API --> Upload[Upload Validation & Metadata]
  Upload --> Files[(Persistent File Storage)]
  Upload --> DB[(PostgreSQL)]
  API --> Jobs[Extraction Job Service]
  Jobs --> Queue[Job Queue - Production]
  Queue --> Worker[Python Extraction Worker]
  Worker --> Graph[LangGraph Orchestrator]
  Graph --> Readers[Reader Router]
  Readers --> Image[Image Reader]
  Readers --> Word[DOCX Reader]
  Readers --> PDF[PDF Reader]
  PDF --> OCR[Shared OCR / Vision Adapter]
  Image --> OCR
  Word --> OCR
  Readers --> CDR[Common Document Representation]
  CDR --> Classifier[Classify Financial Document]
  Classifier --> LLM[LangChain Structured LLM Extraction]
  LLM --> Rules[Normalizer + Validators]
  Rules --> Result[Result / Review State]
  Result --> DB
  API --> DB
```

**The diagram is a dependency picture:** actual reading and classification execute as nodes within a graph. The OCR adapter is a reusable library/service component, not necessarily a network hop.

## 3.2 Architecture style

- **One product-facing microservice** with internal modular boundaries: upload, readers, CDR, extraction, validation, orchestration, persistence, APIs.
- **MVP runtime:** FastAPI + PostgreSQL + persistent local file volume; readers can be tested without queue or LLM.
- **Production runtime:** HTTP API process, PostgreSQL, object storage (or robust shared storage), job broker, scalable worker processes, telemetry.
- **No mandatory network microservice per file type.** Separate deployments only when independent scaling/ownership justifies them.

## 3.3 Component responsibility boundaries

| Component | Must do | Must not do |
|---|---|---|
| Upload API | Receive/validate/store file + metadata | Extract financial fields |
| Reader router | Choose image/docx/pdf adapter | Decide seller or GST totals |
| Readers | Return observed content, structure and evidence | Fabricate missing text; produce final invoice schema |
| OCR/Vision adapter | Recognize image text and locations | Assign accounting meaning by default |
| CDR assembler | Standardize different reader outputs | Declare unverified values as correct |
| Classifier | Decide invoice/bill/receipt/unsupported | Perform accounting validation |
| LLM extractor | Map CDR to financial fields | Control file storage or approve its own accuracy |
| Validator | Deterministically check/normalize outputs | Silently alter source facts |
| LangGraph | Route stages, state and bounded retries | Act as raw file database |
| API delivery | Expose job state, results/errors | Leak internal filesystem locations |

---

# 4. End-to-End User Journey and State Machines

## 4.1 Main journey

1. Client uploads a file using existing endpoint.
2. Upload component validates format/limits/structure and saves file and metadata.
3. Client receives stable `file_id` and upload status `SUCCESS` (better internal meaning: `STORED`).
4. Client requests extraction using `file_id`.
5. Service verifies that file exists, is accepted, and can be accessed by caller when authorization is enabled.
6. New `job_id` is persisted as `queued`.
7. Worker loads file metadata, selects reader, constructs CDR.
8. Workflow classifies content; unsupported documents terminate explicitly.
9. LLM extracts fields into financial schema, preserving evidence links.
10. Deterministic normalizer and validators evaluate reliability.
11. If critical problem is repairable, bounded targeted retry; otherwise `needs_review` or `failed`.
12. Store final result, validation report, versions and trace/cost metadata.
13. Client polls by `job_id` or receives an optional trusted webhook.

## 4.2 Upload lifecycle — **separate** from extraction

```mermaid
stateDiagram-v2
  [*] --> RECEIVING
  RECEIVING --> REJECTED: Invalid / unsafe
  RECEIVING --> PENDING: Initial validation + DB record
  PENDING --> STORED: File safely persisted + DB finalized
  PENDING --> FAILED: Write / persistence failure
  PENDING --> RECOVERING: Stale after crash
  RECOVERING --> STORED: Verified final file
  RECOVERING --> FAILED: Cannot restore
  STORED --> DELETED: Authorized retention / deletion action
```

Current public upload API can keep `SUCCESS` for compatibility; internally map it consistently to `STORED` and avoid conflating it with extraction completion.

## 4.3 Extraction job lifecycle

```mermaid
stateDiagram-v2
  [*] --> QUEUED
  QUEUED --> PROCESSING
  PROCESSING --> COMPLETED: Meets acceptance policy
  PROCESSING --> NEEDS_REVIEW: Ambiguous / unresolved critical fields
  PROCESSING --> UNSUPPORTED: Not invoice / bill / receipt
  PROCESSING --> FAILED: Unrecoverable technical error
  PROCESSING --> RETRY_WAIT: Transient, retryable failure
  RETRY_WAIT --> QUEUED: Scheduled bounded retry
  FAILED --> QUEUED: Explicit new attempt / retry request
  NEEDS_REVIEW --> COMPLETED: Approved/corrected by authorized reviewer
  QUEUED --> CANCELLED: Authorized cancellation
```

**Reader status** (`COMPLETE`, `PARTIAL`, `FAILED`) differs from **job status**. A `PARTIAL` CDR may still yield `NEEDS_REVIEW`, or even `COMPLETED` if missing text is demonstrably irrelevant and policy permits it.

## 4.4 Consistency and crash recovery

PostgreSQL transactions **do not atomically commit filesystem writes**. Proposed pattern:

1. Accept bounded upload into controlled temporary staging.
2. Perform required validation safely.
3. Create `PENDING` record with generated ID and intended final path.
4. Write file to a temporary destination on the target volume, verify exact size/checksum, flush as needed.
5. Atomically rename to final location **on the same filesystem**.
6. Update database status to `STORED`.
7. Only now report success.
8. Reconciler inspects **stale** pending records (not active uploads): final file valid → mark stored; partial file → clean up and fail; DB unavailable → retry later.
9. Cleanup orphan temporary files and independently report consistency failures.

Neither `try/except` alone nor “delete file on error” fully solves power loss. Recovery must be **idempotent**. Never blindly mark every pending record failed on process restart.

---

# 5. Ingestion Design — Detailed Contract

## 5.1 File support matrix

| Format | MIME | Default action | Reader |
|---|---|---|---|
| `.jpg`, `.jpeg` | `image/jpeg` | Accept if genuine, decodable | Image |
| `.png` | `image/png` | Accept if genuine, decodable | Image |
| `.pdf` | `application/pdf` | Accept if valid, unlocked, within limits | PDF |
| `.docx` | OOXML Word MIME | Accept if safe OOXML structure | DOCX |
| `.doc` | Legacy Word binary | **Not supported in initial MVP** | Future isolated converter |
| `.gif`, `.tiff`, `.heic`, `.webp`, `.zip`, `.xlsx`, executable | Various | Reject unless deliberately added | None |

Ensure `.docx` validation examines actual OOXML/ZIP contents, not merely a `PK` ZIP header. Avoid encrypted/macro-enabled office variants unless explicitly supported. Parser/library capability is not equivalent to business support.

## 5.2 Validation order

1. Request body and streaming size cap (before unbounded memory use).
2. Verify supplied extension, received MIME as a hint, and **actual bytes/decodable structure**.
3. Check size, image pixels/dimensions, PDF page count, DOCX expanded ZIP part count/size/ratios.
4. Reject password-protected PDF per ADR-003; reject malformed/truncated files.
5. Use isolated/sandboxed decoders, malware detection where supported, non-executable storage.
6. Normalize safe metadata; generate UUID; never trust `original_name` as a path.
7. Persist and finalize using the state flow above.

**Illustrative initial limits, not production-approved:** file ≤20 MiB, PDF ≤20 pages, finite image pixel count, DOCX expanded-content cap, and bounded decoding/render time. A tiny compressed document can still consume enormous resources when decoded. Choose final limits after dataset benchmarking and infrastructure sizing.

## 5.3 Storage

- **MVP:** `/app/uploads/` may be mounted to a **persistent** volume; ensure the volume really persists across container replacement.
- **Recommended scaling:** object storage (S3/MinIO), storing an opaque key/reference in PostgreSQL.
- **Internal key:** generated UUID-based; never rely on user-supplied filename.
- **Privacy:** encrypt at rest if appropriate; restrict OS permissions, never serve uploads as executable webroot content.
- **Client API:** omit `file_path` from public response and return `file_id` and an approved download/access endpoint instead.
- **Retention:** owner's current “permanent” choice is a policy proposal, not unlimited lawful retention: define purposes, deletion requests, backup retention, access audit and legal obligations before production.

## 5.4 Duplicate behavior and idempotency

- Owner deferred **content deduplication**; two independent uploads get two `file_id`s and may incur two extraction costs.
- **Request idempotency is different:** client timeouts/retries should not produce accidental duplicate jobs; define optional `Idempotency-Key` scoped to caller + operation + request identity.
- SHA-256 may still be calculated for **integrity** even when no content deduplication is performed.
- Reprocessing the same stored file intentionally creates another `job_id`, perhaps with a different extractor/model version.

---

# 6. Reader Abstraction and Common Document Representation (CDR)

## 6.1 Core principle

**Reading is observation; extraction is interpretation.**

Reader statement: “Page 1 bottom-right shows `TOTAL 1180.00`.”  
Extractor statement: “`grand_total` is `1180.00` INR, supported by source block X.”

The distinction prevents OCR internals from becoming accounting/business logic.

## 6.2 Reader interface — logical, not code

**Input:** `{file_id, verified_file_type, storage_reference, options, trace_context}`.

**Output:** `{document_metadata, pages, text_blocks, tables, media_refs, warnings, reader_status, methods_used}`.

Readers must be interchangeable. They should return evidence and partial results **when safe** rather than discard useful text due to one unreadable region.

## 6.3 Proposed CDR v1 contract

```json
{
  "cdr_version": "1.0",
  "file_id": "file_123",
  "source_format": "image/jpeg",
  "reader_status": "PARTIAL",
  "pages": [
    {
      "page_number": 1,
      "width": 1200,
      "height": 1600,
      "coordinate_system": "normalized_0_to_1",
      "methods": ["ocr"],
      "text_blocks": [
        {
          "block_id": "p1_b1",
          "text": "ABC STORE",
          "order": 1,
          "bbox": [0.12, 0.08, 0.54, 0.13],
          "source": "ocr",
          "confidence": 0.94,
          "confidence_provider": "ocr_engine_x"
        }
      ],
      "tables": [],
      "warnings": [
        {
          "code": "UNREADABLE_REGION",
          "severity": "medium",
          "region_bbox": [0.59, 0.84, 0.89, 0.91]
        }
      ]
    }
  ],
  "warnings": ["One image region was unreadable"]
}
```

Illustrative coordinates and confidence values, **not a real OCR result**. Exact schema fields/types must be frozen and validated with Pydantic before downstream integration.

### CDR design rules

- `page_number` is consistently **1-based** in public artifacts.
- `block_id` is unique within one CDR; use stable references for provenance.
- Bounding boxes use one explicit coordinate convention; normalize native PDF pixels/points/image pixels before aggregation, preserve original dimensions and transforms.
- `bbox` is optional (e.g., DOCX paragraph without fixed layout).
- Preserve original OCR text; do **not** silently replace OCR text with a guess.
- `tables` may be absent/empty/low confidence; don't fake grid structure.
- Preserve line order, column relationships, nested table cells if available, page/region context, and reading method.
- Keep **raw source text** as well as normalized fields later.
- Confidence from different providers is **not directly comparable**; record source/method and calibrated reliability separately.
- Large page images, source bytes and crops should live in artifact storage, not in a large LangGraph state/DB payload.
- CDR serialization must have a version and forward/backward migration plan.

## 6.4 Minimum logical block types

`paragraph`, `line`, `word` (if needed), `table`, `cell`, `image_region`, `header`, `footer`, and `unknown`. Do not require that every adapter generate every level. Readability is more important than artificially complete geometry.

## 6.5 CDR partial-content policy

| Situation | Reader status | Output |
|---|---|---|
| All relevant text read | `COMPLETE` | Content, any noncritical warnings |
| Some blocks unreadable | `PARTIAL` | All known content plus warning/regions |
| No usable content, corrupt read, exhausted safe fallback | `FAILED` | Failure reason, safe diagnostic metadata |
| OCR vs Vision unresolved disagreement | Usually `PARTIAL` | Both candidate readings + evidence refs + conflict warning |

### Why CDR matters

Image, DOCX and PDF adapters can evolve separately; a single extractor consumes the same input format. Future email/HTML/other document inputs can join without rebuilding the invoice extractor.

---
# 7. Image Reader — First Implementation Milestone

## 7.1 Responsibilities

The Image Reader is **format-aware but business-agnostic**. It receives a stored JPEG/PNG reference, safely decodes it, identifies text and spatial context, and emits CDR. Its OCR capability must be reusable for scanned PDF pages and embedded DOCX images.

## 7.2 Image Reader pipeline

```mermaid
flowchart TD
  A[Stored Image Reference] --> B[Load + Safe Decode]
  B --> C[Inspect Quality, Orientation, Dimensions]
  C --> D[Optional Non-Destructive Preprocessing]
  D --> E[OCR Adapter]
  E --> F[Text Blocks + Geometry + Signals]
  F --> G[Quality Assessment]
  G --> H{Quality Decision}
  H -->|Accept| I[CDR Assembler]
  H -->|Severe / localized| J[Vision on Crop + Context]
  H -->|No reliable crop| K[Vision on Full Image]
  J --> L[Evidence Comparison]
  K --> L
  L --> I
  H -->|No usable content| M[FAILED / PARTIAL with Reasons]
  I --> N[CDR + Warnings]
```

## 7.3 Substeps and inputs/outputs

| Substep | Input | Output | Important safeguards |
|---|---|---|---|
| 7.3.1 Resolve image | `file_id` / path | Trusted accessible bytes | No arbitrary user-controlled path |
| 7.3.2 Safe decode | Image bytes | Decoded pixel buffer | Hard pixel/size/time limits; decompression-bomb guards |
| 7.3.3 Inspect | Pixels + metadata | DPI/dimensions/orientation flags | EXIF orientation, transparency, blank image detection |
| 7.3.4 Preprocess | Original image | Adjusted temporary rendition | Keep original; avoid degrading thin receipt fonts |
| 7.3.5 OCR | Prepared image | Recognized text + boxes + confidence metadata | Per-language config, timeouts, bounded retries |
| 7.3.6 Evaluate | OCR data | Quality signals and failure reasons | No naive single-threshold assumption |
| 7.3.7 Fallback | Unreliable region/page | Vision evidence | Limit calls and crop dimensions; preserve nearby labels |
| 7.3.8 Reconcile | Original/OCR/Vision | Agreed readings or uncertainty | Never blindly choose newest/most expensive model |
| 7.3.9 Assemble CDR | Observations | `COMPLETE/PARTIAL/FAILED` | Stable IDs, normalized geometry, warnings |

## 7.4 OCR approach

**Proposed initial stack:** Pillow for basic image operations, OpenCV for necessary geometric cleanup, Tesseract for initial OCR, a configurable vision-capable LLM for fallback, and Pydantic for contracts. A managed OCR provider is an alternative if tests reveal unacceptable table or language performance.

**Reader policy:** image preprocessing must be measured, not assumed beneficial. Maintain the pristine source; compare OCR performance with/without rotation, perspective correction, denoising, thresholding and upscale. Some receipts lose characters when aggressively filtered.

## 7.5 OCR quality policy — agreed design

Use multiple signals (ADR-014):

1. **Recognizer confidence** where supplied; by word/line and region, not only document average.
2. **Readability:** empty text, excessive gibberish/symbols, unnatural spacing, broken dates.
3. **Layout quality:** order, overlapping boxes, lost columns, line fragmentation.
4. **Numeric-text quality:** `O/0`, `I/1`, truncated decimals, unreadable totals-like labels, suspicious digit patterns.
5. **Visual context:** blur, glare, shadows, crop, skew and resolution.
6. **Evidence density:** are there recognizable blocks corresponding to visible page regions?

These are **signals**, not proof of correctness. A high confidence score can coexist with a wrong financial digit. Do not use a fixed numeric threshold without evaluating actual OCR confidence behavior on a labeled dataset.

## 7.6 Severity-based fallback — agreed design

| Finding | Default response |
|---|---|
| Minor typo in low-risk descriptive text | Retain OCR reading + warning; no automatic paid fallback by default |
| Unreadable short numeric region | Try relevant crop including nearby label and table context |
| Table reading order/columns unreliable | Larger contextual region or whole page Vision |
| Image mostly blank/unreadable | Bounded full-image attempt; otherwise `FAILED/PARTIAL` |
| OCR and Vision disagree | Compare original evidence, retain alternatives if unresolved |
| Model/API unavailable | Preserve OCR evidence, report degraded/partial result; retry only if policy allows |

**Business-critical field severity** (e.g., a candidate grand total) cannot always be known in a pure reader. Reader flags visually suspicious numeric regions; later extraction/validation may request targeted re-reading of a **specific source region**. This avoids embedding invoice-specific business rules into the OCR adapter.

**Boundaries:** maximum one initial OCR pass, bounded preprocessing attempts, bounded Vision calls/regions, a per-page processing budget and a total per-job budget. Final numerical limits must be benchmarked.

## 7.7 OCR vs Vision conflict

Example: OCR says `₹180.00`; Vision says `₹130.00`.

- Do not assume Vision wins just because it is the fallback.
- Store both candidates and their source references, crop coordinates, methods and quality evidence.
- If visually or contextually verifiable, preserve the supported reading, with a resolution note.
- If still uncertain, mark region as `CONFLICTING_READINGS` and do not present an unqualified verified financial value.
- Step 3/4 may use a targeted re-read or require review, but must not silently “average” conflicting digits.

## 7.8 Image-specific edge cases

- Rotated EXIF images and screenshots; orientation must be normalized predictably.
- Cropped receipts lacking merchant header or total; produce partial output.
- Long thin thermal receipts; handle aspect ratio and OCR scale without extreme memory use.
- Multiple receipts in a single photograph; default to **unsupported multiple-document / review** until segmentation is explicitly implemented.
- Phone glare, shadow, watermark, faded print, folds, low contrast.
- Hindi/English text and mixed numerals; language models/configuration must be tested.
- Currency symbols (`₹`, `Rs`, `INR`) and local separators (e.g. `1,23,456.78`).
- Screenshots of UPI/payment slips; classification distinguishes receipts vs unrelated transaction screenshots according to product policy.
- Redaction/blurred sensitive data; return missing/uncertain, do not reconstruct it.
- Embedded images inside Word documents or rasterized PDF pages should use **the same OCR adapter**, not make another public upload request.

## 7.9 Image Reader acceptance criteria

- [ ] Takes stored `file_id` / trusted reference; does not request a second upload.
- [ ] Preserves original bytes; safely decodes JPEG and PNG.
- [ ] Returns recognized text with region/block IDs and normalized positions.
- [ ] Returns a valid versioned CDR even if some text is unreadable.
- [ ] `PARTIAL` reflects missing/uncertain regions with specific warnings.
- [ ] Produces `FAILED` for truly unusable input with safe error detail.
- [ ] OCR tests cover clear, rotated, shadowed, blurred, long receipts and Hindi/English samples if supported.
- [ ] Vision remains optional, bounded, measurable and mockable in tests.
- [ ] Cropped Vision fallback preserves surrounding context.
- [ ] No invoice-field identification or final business JSON in the reader.

---

# 8. DOCX Reader — Second Implementation Milestone

## 8.1 Scope

Read modern OOXML `.docx` using a parsing adapter. `python-docx` is a practical initial library for paragraphs/tables. DOCX is a structured flow document, **not a fixed-page image**.

## 8.2 Pipeline

```mermaid
flowchart TD
  A[Stored DOCX] --> B[Safe OOXML Container Inspection]
  B --> C[Parse Body in Document Order]
  C --> D[Paragraphs / Runs / Headings]
  C --> E[Tables / Rows / Cells]
  C --> F[Images / Other Media]
  F --> G[Shared Image OCR Adapter if needed]
  D --> H[Merge Ordered Blocks]
  E --> H
  G --> H
  H --> I[CDR with Logical Sections + Warnings]
```

## 8.3 Key requirements

- Preserve paragraph/table sequence and nested structure; don't concatenate all paragraphs followed by all tables.
- Extract relevant headers/footers, and note that contents may repeat across pages in Word rendering.
- Extract tabular cells, merged cells where supported, nested tables and labels/totals.
- Recognize embedded images and route them to the shared OCR component when necessary.
- Some images are floating/drawing elements and not trivially handled by high-level `python-docx`; build a fallback/review path or a conversion renderer if required.
- Do not invent exact page numbers/coordinates for unrendered DOCX; use logical block order and section references; `bbox = null` is acceptable.
- Validate OOXML ZIP parts, relationship targets, embedded objects and resource caps; do not execute macros or external links.
- Old `.doc` should return `UNSUPPORTED_FILE_TYPE` in MVP; later use a sandboxed converter and test fidelity.

## 8.4 Alternative: DOCX → PDF conversion

**When useful:** high layout fidelity or fixed-page coordinates are required.  
**Costs:** extra worker/runtime dependency, formatting differences, font availability, conversion attack surface, latency.  
**Recommended default:** parse DOCX structure directly; add isolated rendering as a targeted fallback, not mandatory for every file.

## 8.5 DOCX Reader acceptance criteria

- [ ] Reads simple paragraph-only document.
- [ ] Reads invoice tables and retains row/cell relationships.
- [ ] Preserves order between paragraph and table elements.
- [ ] Emits a valid CDR with optional/unknown geometries.
- [ ] Handles relevant embedded images through shared OCR when supported.
- [ ] Rejects malformed/oversized OOXML safely.
- [ ] Produces explicit warnings for unsupported floating shapes/conversion-dependent layout.

---

# 9. PDF Reader — Third Implementation Milestone

## 9.1 Why PDF comes after Image Reader

Scanned PDF pages are effectively images. By building shared OCR first, the PDF reader can **render selected page regions and reuse image text-recognition**. This saves duplicate OCR logic and makes failure behavior consistent.

## 9.2 PDF page-routing pipeline

```mermaid
flowchart TD
  A[Stored PDF] --> B[Open / Validate / Count Pages]
  B --> C[For Each Page]
  C --> D[Try Native Text + Layout Extraction]
  D --> E{Usable Native Text?}
  E -->|Yes| F[Keep Native Blocks / Tables]
  E -->|No / Mixed| G[Render Page or Relevant Regions]
  G --> H[Shared OCR and Vision Adapter]
  H --> I[Page CDR]
  F --> I
  I --> J[Combine All Pages in Order]
  J --> K[Document CDR]
```

## 9.3 Detailed behavior

1. Open safely; reject password-protected/invalid PDFs as agreed.
2. Check file/page limits and renderer resource budgets.
3. Iterate **page by page**; don't classify entire PDF as digital/scanned from page 1 alone.
4. Obtain native text blocks, words, positions and layout/table signals.
5. Evaluate whether native text is **usable**, not just non-empty. Some scans have poor OCR text layers that look like embedded text.
6. For missing/unreliable regions, render at controlled resolution and reuse shared OCR.
7. Avoid duplicating existing native text when merging partial OCR output.
8. Preserve page IDs, reading order, coordinates, page rotations and method per region.
9. Combine all pages in order into a single CDR, with page-level warnings.

**Proposed PDF parser:** PyMuPDF. It supports text blocks, page rendering and OCR-related workflows; paid OCR/vision is only needed for difficult cases.

## 9.4 Complex PDF situations

- **Mixed PDF:** digital pages and scanned pages in same file.
- **Mixed page:** selectable heading, scanned table image on same page.
- **Existing bad OCR layer:** selectable text can be wrong; don't automatically trust it.
- **Multi-column page:** naive concatenation breaks reading order.
- **Complex tables:** borderless, merged cells, discounts, multiple tax sections.
- **Rotation:** page rotation and crop boxes affect coordinates.
- **Attachments, XFA/dynamic forms, annotations:** support policy must be explicit; do not assume all content appears in simple page text.
- **Multi-invoice PDF:** one file may contain more than one business document; V1 flags for review, future segmentation may split into subdocuments with traceability.

## 9.5 PDF Reader acceptance criteria

- [ ] Digital PDF extracts text/layout without unnecessary OCR.
- [ ] Scanned PDF routes pages to shared OCR.
- [ ] Mixed PDF processes each page according to its content.
- [ ] Table and page positions are preserved where recoverable.
- [ ] Duplicated native + OCR text is avoided.
- [ ] Page-level partial failure doesn't automatically discard other pages.
- [ ] Password, corruption, enormous raster page and processing limits are safe.
- [ ] Output uses exactly the same CDR contract as Image and DOCX readers.

---

# 10. Document Classification and Scope Gate

## 10.1 Why classification is needed

A valid JPEG or PDF can contain a PAN card, identity document, resume or shopping list. **Upload acceptance validates the format; classification validates the business document category.**

## 10.2 Output classes

- `invoice`
- `bill`
- `receipt`
- `unsupported`
- `unknown`

## 10.3 Classification strategy

1. Use document content/structure and lightweight deterministic cues when reliable.
2. Use structured LLM classification for ambiguous formats if necessary.
3. Preserve evidence for the chosen class and any uncertainty.
4. If confidence is inadequate, return `unknown` or review; don't force every document into invoice.
5. If multiple document types are present in one file, flag a multi-document condition rather than merge them into one fraudulent record.

## 10.4 Rules of separation

- Classifier decides **kind of document**, not invoice totals.
- `unsupported` may be a **successful technical read** but a **nonprocessable business document**.
- Classification model and thresholds must be evaluated against confusing lookalikes: quotes, purchase orders, delivery notes, payment confirmation screens, tax registration cards.

---

# 11. Canonical Financial JSON Schema v1

## 11.1 Design objectives

- Stable across invoice/bill/receipt, with optional specialized fields.
- Versioned independently from CDR and HTTP API.
- Precise money values (`Decimal` in Python; **decimal strings in JSON**).
- Dates as ISO `YYYY-MM-DD` **only when interpretable**; preserve original raw date otherwise.
- Currencies as ISO 4217 (e.g. `INR`) when observed/inferred with clearly documented policy.
- Missing is `null`, **not** `0`, `""`, or a model guess.
- Preserve page/block/region evidence for sensitive or critical fields.
- Do not require invoice-only fields on simple receipts.

## 11.2 Proposed data fields

| Group | Recommended fields |
|---|---|
| Identity | `document_type`, `document_number`, `document_date`, `due_date`, `currency`, `language` |
| Seller | `name`, `address`, `tax_id`, `gstin`, `contact` |
| Buyer | `name`, `address`, `gstin`, `contact` |
| Line items | `description`, `quantity`, `unit`, `unit_price`, `discount`, `tax_rate`, `tax_amount`, `hsn_sac`, `amount` |
| Totals | `subtotal`, `discount_total`, `shipping`, `other_charges`, `cgst`, `sgst`, `igst`, `cess`, `tax_total`, `round_off`, `grand_total` |
| Payment | `payment_method`, `transaction_reference`, `amount_paid`, `balance_due`, `payment_status` |
| Provenance | Source references; original snippets; unresolved candidates; field issues |
| Meta | `schema_version`, `document_type_confidence/quality`, extraction model/prompt versions |

**Tax naming caution:** An invoice may show an overall GST amount and not individual CGST/SGST/IGST. Unknown fields must be `null`; do not invent component taxes. Receipts without explicit invoice numbers should remain valid receipts.

## 11.3 Example full response (fictional)

```json
{
  "schema_version": "1.0",
  "job_id": "job_987",
  "file_id": "file_123",
  "status": "completed",
  "document": {
    "document_type": "invoice",
    "document_number": "INV-1042",
    "document_date": "2026-11-14",
    "due_date": null,
    "currency": "INR",
    "seller": {
      "name": "ABC Traders",
      "address": null,
      "gstin": "09ABCDE1234F1Z5"
    },
    "buyer": {"name": "XYZ Technologies", "address": null, "gstin": null},
    "line_items": [
      {
        "description": "Office Supplies",
        "quantity": "2",
        "unit": null,
        "unit_price": "500.00",
        "discount": null,
        "hsn_sac": null,
        "tax_rate": null,
        "tax_amount": null,
        "amount": "1000.00"
      }
    ],
    "totals": {
      "subtotal": "1000.00",
      "discount_total": null,
      "shipping": null,
      "other_charges": null,
      "cgst": "90.00",
      "sgst": "90.00",
      "igst": "0.00",
      "cess": null,
      "tax_total": "180.00",
      "round_off": null,
      "grand_total": "1180.00"
    },
    "payment": {
      "payment_method": null,
      "transaction_reference": null,
      "amount_paid": null,
      "balance_due": null,
      "payment_status": null
    }
  },
  "validation": {
    "passed": true,
    "issues": []
  },
  "evidence": [
    {
      "field_path": "document.totals.grand_total",
      "page_number": 1,
      "block_ids": ["p1_b25"],
      "raw_text": "Grand Total ₹1,180.00",
      "resolution": "direct_supported_reading"
    }
  ]
}
```

This is an **illustrative contract**, not a claim about the uploaded sample file. The fictional totals assume the printed `0.00` IGST is explicitly observed, and the document happens to add to ₹1,180. The final domain schema may permit `null`/different structures for tax breakdowns and discounts.

## 11.4 Invoice vs bill vs receipt extensions

- **Invoice:** issuer/invoice number, invoice date, due date, tax itemization and buyer details when available.
- **Receipt:** merchant, transaction/payment date, payment reference, payment method and amount paid; may lack buyer and invoice number.
- **Bill:** service period, account/reference, bill due, charges, taxes, amount due and paid status; add domain-specific extensions as required.
- **Schema extensions:** avoid putting vendor-specific arbitrary keys at the root. Use `additional_fields` with schema governance if needed.

## 11.5 Provenance model

For important fields store: `field_path`, `source_file_id`, `page_number`, `block_id`, `bbox` if available, `raw_text`, `extraction_method`, `candidate_values`, `resolution`, and optional quality flags.

Evidence is what lets engineering troubleshoot OCR/LLM errors. It also supports a future review UI displaying a highlighted source region. Avoid logging raw personal financial data in unprotected logs.

---

# 12. LangChain and LLM Extraction Design

## 12.1 LLM role

LangChain provides the LLM adapter, structured output schema binding, prompts, timeouts and provider abstraction. The LLM **interprets** the CDR; it does **not** open arbitrary server paths, create files, or decide whether an upload is safe.

## 12.2 Extraction stages

1. Receive versioned CDR and classification.
2. Select the appropriate extraction schema/profile for invoice, bill or receipt.
3. Construct compact, ordered input with text blocks, table rows, page markers and relevant evidence IDs.
4. Invoke structured-output model; ask to extract only source-supported facts.
5. Validate returned shape with Pydantic.
6. Create links from extracted fields to observed CDR blocks.
7. Route malformed output or uncertain critical fields to bounded repair/review.

## 12.3 Prompt and model policies

- Never invent missing values; use `null` and warnings.
- Do not “fix” amounts unless original evidence and business rule justify it.
- Keep raw string and normalized value separate for dates/numbers when ambiguous.
- Include **all** line items supported by the source; never collapse multiple rows into one fabricated summary.
- Do not follow any instructions inside scanned documents, including “ignore previous instructions”, URLs or prompts.
- Require the model to cite CDR `block_id`/region references when possible; verify citations exist.
- Set bounded timeouts, token budgets and max retry counts.
- Model temperature/configuration should be controlled and versioned; determinism is not guaranteed even at temperature 0.
- Store prompt template version, provider, model identifier, and schema version for reproducibility.
- Prefer supported provider-native structured output when available; otherwise use explicit schema validation and repair policy.

## 12.4 Long/multi-page documents

Do not naively concatenate unlimited pages into one prompt. Choose by page count and token budget:

- Small document: one ordered CDR payload.
- Longer document: page or section extraction with provenance and a **deterministic merge** into a single document (only if single financial document is supported).
- Line items spanning pages: preserve row continuity, avoid duplicate last/first rows, and validate aggregate amounts.
- Pages containing multiple unrelated invoices: flag segmentation problem; do not merge sellers/totals across invoices.

**RAG/vector store is not required** for processing one known document. Add it only if future needs involve search across large document collections or historical vendor context.

## 12.5 Hallucination and prompt-injection handling

- Uploaded document text is **untrusted data**.
- Prompts are managed outside documents; no external links executed from document text.
- LLM has only the minimum tools/permissions needed (ideally no tool access for extraction).
- Validate all output fields and evidence IDs; never let LLM-generated filenames, SQL, URLs or system commands drive execution.
- Treat “confident looking” outputs as **unverified until validated**.
- For exact financial digits, compare CDR evidence and arithmetic where applicable; escalate conflicts.

---

# 13. Normalization, Validation and Financial Controls

## 13.1 Separate three questions

1. **Schema validity:** does the response match the expected JSON types/structure?
2. **Semantic validity:** are dates, tax identifiers, quantities and numeric representations plausible?
3. **Source fidelity:** does the JSON actually match the document and reconcile arithmetically?

Passing question 1 **does not** guarantee questions 2 or 3.

## 13.2 Validation layers

| Layer | Rules | Result |
|---|---|---|
| Type/schema | Pydantic nested objects, enum values, decimals, nullability | Reject malformed shape |
| Dates | ISO conversion, source date preservation, locale ambiguity | Normalize or mark ambiguous |
| Currency | Preserve explicit currency; currency symbols/context carefully | Normalized code or null |
| Identity | Invoice number presence if required by profile, seller/buyer differentiation | Warning/review |
| GSTIN | Syntax/check digit where appropriate; do not claim registration validity | Format issue only |
| Line items | Quantity × unit price vs amount, discounts/tax flags | Mismatch issue |
| Totals | Subtotal ± discount + tax + charges + roundoff vs grand total | Mismatch issue |
| Payment | Amount paid vs total/balance if documented | Possible inconsistency |
| Evidence | Source block exists, digits are legible, document page present | Supported/uncertain |
| Completeness | Critical fields per document type | Complete/needs review |

## 13.3 Indian financial document details

- `CGST`, `SGST`, `IGST`, and possibly `cess` may be separately printed; preserve explicit values.
- A receipt may show **GST-inclusive** prices; avoid automatically adding tax twice.
- Percentage rates may differ per line item; do not assume one flat rate.
- Handle `HSN/SAC`, discounts, multiple rate slabs, round-off and shipping charges as separate components.
- Indian grouping: `1,23,456.78` is a valid amount notation; parse locale carefully.
- Distinguish `total`, `amount due`, `amount paid`, `change returned`, `balance due`, and `subtotal`.
- Duplicate tax/seller copies, `Original / Duplicate`, credit terms, cancelled invoices and refunds require explicit policy.
- A GSTIN matching a format pattern is **not evidence the business exists or tax is legally correct**. Never imply tax/legal validation without an external authoritative check.

## 13.4 Arithmetic correctness

Use decimal-safe calculations. An illustrative invoice equation is:

`grand_total = subtotal − discount_total + tax_total + shipping + other_charges + round_off`

But **only** apply it when the document’s representation actually matches this accounting structure. Tax-inclusive pricing, adjustments, advances and amounts already incorporated into subtotal change the equation. For each failed rule, report expected/observed values and source evidence, with a configurable rounding tolerance.

## 13.5 What happens if the model is wrong?

- **Syntax error:** structured-output retry with bounded attempts.
- **Numerical mismatch and strong source evidence:** ask for targeted re-reading/extraction, then re-validate.
- **Unclear source:** mark field uncertain, do not overwrite with a guessed arithmetic result.
- **Source-supported data but odd business values:** preserve as observed and flag, rather than reject automatically.
- **Critical unresolved issue:** `needs_review` with partial structured data and issue details.
- **True hard failure:** `failed`, retain diagnostic reason and safe artifacts.

## 13.6 Confidence vs reliability

Do not pretend that one LLM-generated `0.98` is an objectively calibrated accuracy probability. Use:

- OCR word/region confidence **with provider label**.
- Layout/readability quality signals.
- Evidence coverage for critical fields.
- Arithmetic and cross-field consistency.
- Document classification uncertainty.
- Evaluation-data calibration if a combined reliability score is eventually introduced.

V1 may expose **issue severity + evidence status** instead of a single fabricated confidence score. This is often more actionable.

---
# 14. LangGraph Orchestration — Complete Workflow Design

## 14.1 Why LangGraph

Our process contains **conditional routing**, **partial failures**, **bounded repair**, and state that must survive long jobs. LangGraph coordinates deterministic Python nodes and targeted LLM calls. It **does not require multiple AI agents**. Most nodes should be ordinary deterministic functions/adapters.

## 14.2 Workflow diagram

```mermaid
flowchart TD
  START([START]) --> Load[Load Job + File Metadata]
  Load --> Route{Verified File Type}
  Route -->|image| IMG[Image Reader]
  Route -->|docx| DOC[DOCX Reader]
  Route -->|pdf| PDF[PDF Reader]
  Route -->|unsupported| Err[Unsupported Format]
  IMG --> CheckCDR[Check Reader Status + CDR]
  DOC --> CheckCDR
  PDF --> CheckCDR
  CheckCDR --> HasContent{Usable Content?}
  HasContent -->|no| Fail[FAILED]
  HasContent -->|yes/partial| Classify[Classify Document]
  Classify --> Kind{Supported Category?}
  Kind -->|unsupported| Unsupported[UNSUPPORTED]
  Kind -->|unknown| Review[NEEDS_REVIEW]
  Kind -->|yes| Extract[LLM Structured Extraction]
  Extract --> Validate[Normalize + Validate]
  Validate --> Decision{Validation Outcome}
  Decision -->|accepted| Done[COMPLETED]
  Decision -->|repairable and budget left| Repair[Targeted Re-read / Re-extract]
  Repair --> Validate
  Decision -->|uncertain| Review
  Decision -->|unrecoverable| Fail
  Done --> Persist[Persist Final Status + Result]
  Review --> Persist
  Fail --> Persist
  Unsupported --> Persist
  Err --> Persist
  Persist --> END([END])
```

**Design refinement:** Sometimes a repaired region needs rerunning **extraction**, not simply validation. The targeted repair node must identify affected field/page and re-enter only the necessary extractor/validator path. The diagram is conceptual; avoid a graph edge that validates stale data.

## 14.3 Node contract table

| Node | Reads from state | Writes to state | Side effects |
|---|---|---|---|
| `load_metadata` | `job_id`, `file_id` | Verified file metadata | DB read |
| `route_reader` | `content_type`, `file_type` | Reader route | None |
| `read_document` | Storage ref | CDR artifact ref, reader status | File read / OCR or Vision calls |
| `assess_cdr` | CDR summary | Quality warnings, read decision | Artifact read |
| `classify` | CDR ref | Document type + class evidence | LLM call if needed |
| `extract_fields` | CDR ref + type | Raw typed extraction + evidence | LLM call |
| `normalize_validate` | Extracted fields | Validated result + issues | None or DB-free deterministic processing |
| `targeted_repair` | Issue + source refs + retry budget | Revised CDR/field candidates | OCR/Vision/LLM calls |
| `finalize` | Final issues/status | Final result reference | DB/artifact write |

## 14.4 State model

Keep state small; prefer references rather than file bytes:

| State field | Example |
|---|---|
| `job_id` | `job_987` |
| `file_id` | `file_123` |
| `trace_id` | `trace_...` |
| `attempt` | `1` |
| `reader_type` | `image` |
| `cdr_artifact_ref` | `artifacts/job_987/cdr-v1.json` |
| `reader_status` | `PARTIAL` |
| `document_type` | `receipt` |
| `extraction_artifact_ref` | `artifacts/job_987/extraction-v1.json` |
| `validation_report_ref` | `artifacts/job_987/validation.json` |
| `issues` | Limited issue codes/field paths |
| `repair_count` | `0` |
| `status` | `processing` |
| `version_bundle` | Reader, OCR, model, prompt, schema |

## 14.5 Graph persistence and checkpointing

- **MVP:** durable job rows and deterministic work stages are sufficient to start; a graph checkpointer can be added when recovery/resume/human review is needed.
- **Production:** use a supported durable checkpointer if using LangGraph resume/interrupt semantics.
- Persisting graph state is **not** the same as exactly-once side effects; OCR provider calls, LLM calls, file writes and DB operations need idempotent retry design.
- Keep raw documents and big CDR payloads outside checkpoints; state stores references.
- Do not rely on an in-memory checkpointer across process restarts.

## 14.6 Retry strategy

| Failure | Retry? | Policy |
|---|---|---|
| Temporary model timeout/429 | Yes, bounded | Backoff, jitter, circuit-breaker/provider limits |
| OCR process crashed transiently | Maybe | One controlled retry; record attempt |
| Corrupt file | No | Fail with specific error |
| Unsupported file | No | Reject/unsupported |
| Invalid JSON shape | Limited | Structured repair once or twice |
| Unreadable numeric region | Limited | Targeted crop/full page attempt within budget |
| Consistent unresolved source conflict | No blind retries | `needs_review` |
| Worker process killed | Yes if safe | Recover with job lease/idempotent stage |

Model retry counts are **budgets**, not promises of guaranteed correction. Beware accidental retry multiplication when HTTP, queue, LangGraph, and LLM clients all retry independently. Set one overall job attempt budget.

## 14.7 Human review integration (optional initially)

If the product later needs human verification:

1. Mark `needs_review` with field-level issues and CDR evidence refs.
2. Authorized reviewer sees source image/page/crop and candidates.
3. Reviewer submits correction with reason and reviewer ID.
4. Persist original AI result and correction separately (audit trail).
5. Run deterministic re-validation; finalize only if policy satisfied.
6. Prevent two reviewers from overwriting each other (optimistic lock/version).

No review UI is required for first reader milestone; define the data hooks early.

---

# 15. API Design, Contracts and HTTP Semantics

## 15.1 Separate file upload from extraction

**Existing functionality:** upload file, store original, return `file_id`.  
**New functionality:** run one or more extraction jobs against a stored `file_id`.

| Method | Endpoint | Responsibility | Expected successful response |
|---|---|---|---|
| `POST` | `/v1/files` | Accept/validate/store upload | `201 Created` + file metadata (existing status conventions may differ) |
| `GET` | `/v1/files/{file_id}` | Return allowed metadata | `200 OK` |
| `POST` | `/v1/extractions` | Create job for `file_id` | `202 Accepted` + `job_id` |
| `GET` | `/v1/extractions/{job_id}` | Fetch status and eventual result | `200 OK` |
| `POST` | `/v1/extractions/{job_id}/retry` | Create explicitly retrying attempt / new job | `202 Accepted` |
| `POST` or `PATCH` | `/v1/extractions/{job_id}/review` | Future verified correction, authorized only | `200/202` |
| `GET` | `/health/live` | Liveness | `200` if process responsive |
| `GET` | `/health/ready` | Dependency readiness | `200/503` |

A REST interface may expose extraction `result_url` and paging when payloads become large. HTTP `202` means accepted/queued, **not extraction complete**.

## 15.2 Create extraction request

```json
{
  "file_id": "14c22b56-4348-451f-a214-8d2793e2e8d2",
  "options": {
    "document_type_hint": null,
    "ocr_language_hints": ["eng"],
    "output_schema_version": "1.0"
  }
}
```

Hint fields must be treated as **untrusted hints**; user may upload the wrong document or specify the wrong type. Restrict model/provider options to server-approved configurations, not arbitrary client prompts or executable templates.

**Accepted response:**

```json
{
  "job_id": "job_987",
  "file_id": "14c22b56-4348-451f-a214-8d2793e2e8d2",
  "status": "queued",
  "status_url": "/v1/extractions/job_987"
}
```

**Status response while running:**

```json
{
  "job_id": "job_987",
  "file_id": "14c22b56-4348-451f-a214-8d2793e2e8d2",
  "status": "processing",
  "stage": "reading",
  "result": null,
  "error": null
}
```

**Terminal response:** add `result` (schema in §11) for completed/reviewable jobs, `validation` and `error` as applicable. Do **not** expose local paths, model secrets, raw system prompts or internal stack traces.

## 15.3 Error response contract

```json
{
  "error": {
    "code": "PASSWORD_PROTECTED_DOCUMENT",
    "message": "This PDF requires a password and is not supported.",
    "retryable": false,
    "details": {"file_id": "file_123"},
    "trace_id": "trace_xyz"
  }
}
```

Use one controlled `error.code` vocabulary across ingestion, reading, extraction, and job lifecycle. Do not return full file bytes or sensitive OCR text inside error messages.

## 15.4 Error-to-HTTP mapping (proposed)

| Condition | Recommended HTTP behavior | Note |
|---|---|---|
| Malformed request | `400` or `422` | Distinguish business validation from request schema |
| Unauthorized caller (production) | `401` | Authentication required |
| Forbidden file (production) | `403` or privacy-preserving `404` | Authorization policy |
| `file_id` missing | `404` | No such upload |
| Unsupported extension/format | `415` | If uploader rejects media type |
| File too large | `413` | Payload limit |
| Encrypted/corrupt file | `422` | Recognized format but unsupported/unprocessable |
| Duplicate idempotency-key with different payload | `409` | Request conflict |
| Provider outage / job submission unavailable | `503` | Retryability explicit |
| Job accepted, not finished | `202` on create; `200` on status read | Never return fake final result |
| Supported format but nonfinancial document | Job `unsupported` | Not an HTTP transport failure |

## 15.5 Webhook option (future)

Optional signed outbound webhook after completion. Requirements: retries, idempotent delivery, signature verification, tenant callback allowlist, HTTPS, SSRF protection, delivery logs and dead-letter handling. Don't implement until a client actually requires push notifications; polling is simpler for MVP.

## 15.6 API versioning

- Route version: `/v1/...`.
- Financial result `schema_version`: e.g. `1.0`.
- CDR version independently: e.g. `1.0`.
- Document parser/model/prompt version independently recorded.
- Add fields compatibly where possible; breaking changes require explicit API/schema rollout and contract tests.

---

# 16. Database Design and Persistence

## 16.1 Core tables

**`uploaded_files`** (existing):

| Column | Notes |
|---|---|
| `id` (UUID) | Primary key |
| `original_name` | Display metadata, untrusted |
| `stored_name` / `storage_key` | Internal opaque object |
| `file_extension` + `content_type` | Verified/normalized; distinguish from client hint |
| `file_size_bytes` | Actual bytes |
| `file_path` | Internal-only in MVP; replace with object storage key later |
| `status` | File lifecycle |
| `error_message` / `error_code` | Safe failure info |
| `created_at`, `updated_at` | UTC timestamps |
| `sha256` (optional) | Integrity, **not** necessarily dedup |
| `page_count` (optional) | For PDF; images use logical page 1 |
| `owner_id`, `tenant_id` (future) | Production auth/authorization |
| `retention_policy_id` (future) | Lifecycle controls |

**`extraction_jobs`**:

| Column | Notes |
|---|---|
| `id` (UUID) | Job identity |
| `file_id` (FK) | One file can have many jobs |
| `status` | Job lifecycle enum |
| `stage` | Reading/classifying/extracting/validating/finalizing |
| `attempt_count` and `repair_count` | Retries |
| `idempotency_key` (optional) | Request-level dedup |
| `locked_by`, `lease_until` (optional) | Crash/worker recovery |
| `cdr_ref` | Internal artifact pointer |
| `model_name`, `model_version`, `prompt_version`, `schema_version` | Reproducibility |
| `error_code`, `error_message` | Safe troubleshooting |
| `created_at`, `started_at`, `completed_at`, `updated_at` | Lifecycle timestamps |

**`extraction_results`**:

| Column | Notes |
|---|---|
| `id` (UUID) | Result ID |
| `job_id` (FK, unique for final result) | Source job |
| `document_type` | Invoice/bill/receipt |
| `extracted_json` (JSONB) | Financial contract |
| `validation_report` (JSONB) | Issue codes/severity |
| `evidence_ref` | CDR/block provenance artifact |
| `result_version` | Changes/approved corrections |
| `created_at`, `updated_at` | Auditing |

**Optional later:** `job_events` (append-only status history), `review_events`, `webhook_deliveries`, `outbox_events`, `processing_costs`, `document_artifacts`, `tenant_policies`.

## 16.2 Relationship diagram

```mermaid
erDiagram
    UPLOADED_FILES ||--o{ EXTRACTION_JOBS : has
    EXTRACTION_JOBS ||--o| EXTRACTION_RESULTS : produces
    EXTRACTION_JOBS ||--o{ JOB_EVENTS : emits
    EXTRACTION_RESULTS ||--o{ REVIEW_EVENTS : may_have
```

## 16.3 Indexing, migrations and access

- Index `extraction_jobs(file_id, created_at)`, `extraction_jobs(status, created_at)` and stale/lease queries as needed.
- Add unique constraint for `extraction_results.job_id` if one final result per job.
- Generate and apply database migrations; rollback strategy and compatibility tests required.
- Use parameterized repository access; no SQL generated directly from uploaded content.
- Restrict app DB credentials to minimum necessary privileges.
- Keep sensitive full-text OCR out of DB application logs.

## 16.4 Atomic job submission and queue consistency

DB insert and broker publish are different systems. If DB says `queued` but publishing to Redis fails, a job can be stranded. Options:

1. **MVP:** create job, enqueue, and have a scheduled job reconciler retry un-dispatched `queued` jobs.
2. **Production robustness:** use a **transactional outbox** row written in the same DB transaction as job creation; a dispatcher publishes and marks outbox delivery. Consumers are idempotent.

Do not claim “exactly once” merely because Celery or LangGraph is present. Queue delivery can be **at least once**; protect side effects and status transitions accordingly.

---

# 17. Background Jobs, Queue and Worker Runtime

## 17.1 When to introduce Celery/Redis

For reader prototype, direct service tests are fine. For multi-page OCR, model latency, concurrent clients and predictable HTTP response times, use background workers.

**Production proposal:** `FastAPI → PostgreSQL job/outbox → Redis broker → Celery worker → LangGraph → PostgreSQL result`. Celery task payload should contain **IDs only** (`job_id`) rather than file bytes/PII.

## 17.2 Worker responsibilities

- Claim a job/lease and verify current state.
- Resolve stored file by trusted reference.
- Execute the graph with timeouts and provider budgets.
- Persist stage progress and artifact references.
- Handle retries and release/expire lease.
- Finalize result once; handle duplicate task delivery safely.

## 17.3 Concurrency isolation

- Image rendering/OCR is CPU/memory intensive; cap process concurrency.
- LLM provider calls consume network rate limits; separate semaphore/rate controls.
- PDFs can be larger than photos; enforce per-page/total budgets.
- Prevent one long document from starving the queue (fair scheduling and limits).
- Queue backlog, processing duration and dead letters need metrics and alerts.
- Temporary files must be cleaned after success/failure; avoid unlimited disk growth.

## 17.4 Cancellation, timeout and retry ownership

- Define max queue wait, max job execution duration and per-model timeout.
- Cancellation should be cooperative; avoid marking `cancelled` while workers still writing results.
- One layer owns job-level retry policy. Other layers have only tightly scoped, bounded retries.
- Expired job lease does not imply work never happened; re-claimed workers must check persisted state and artifact existence.

## 17.5 Storage migration path

A local persistent folder works for one-machine MVP, but **separate production workers on other nodes cannot access it unless shared**. Before horizontal scaling, migrate to object storage or a reliably shared filesystem. Abstraction: reader depends on `storage_provider.open(file_id/storage_key)`, not a hardcoded `/app/uploads` path.

---

# 18. Production Security, Privacy and Compliance Design

> **Production release gate:** authentication and authorization cannot stay deferred if the service is exposed to users or carries sensitive financial data. The owner deferred *implementation timing*, not the production requirement.

## 18.1 Threat model overview

| Threat | Example | Mitigation |
|---|---|---|
| Format spoofing | Executable renamed `invoice.pdf` | Signature, structural parsing, allowlist |
| Parser exploit | Crafted PDF or OOXML ZIP | Sandboxing, dependency updates, resource limits |
| Zip/decompression bomb | Tiny DOCX expands to huge resources | Expanded-size/ratio/part caps |
| Path traversal | Filename `../../...` | Generated storage key; no filename-derived paths |
| Unauthorized access | Guess someone else's file ID | Auth + tenant/ownership authorization |
| Prompt injection | Document says “ignore system instructions” | Treat file text as inert data; constrained model capabilities |
| SSRF | External links/media inside document | Disable/limit external fetches, allowlist providers |
| Data exfiltration | Logging full invoice, unapproved model API | PII-safe logs, vendor/privacy review, encryption |
| Excessive cost | Thousands of Vision calls | Page, token, retry and per-client budgets |
| Duplicate delivery | Same job processed twice | Idempotent job claims and writes |
| Storage leak | File served by webroot | Private storage; authorized access endpoints |

## 18.2 Authentication/authorization rollout

**Restricted MVP:** no public authentication flow implemented; bind locally or behind trusted network controls. Use internal service credentials where necessary.

**Production:**

- Verify signed access token/JWT with issuer, audience, expiry and key rotation policies.
- Map caller to user/tenant identity; don't trust user IDs from request body.
- Authorize every `GET file`, `POST extraction`, `GET job`, `retry`, and `review` using ownership/tenant/role policy.
- Use least-privilege roles (`submitter`, `reader`, `reviewer`, `admin`) only if business needs them.
- Rate limit, audit sensitive access, and ensure ID guessing never bypasses authorization.
- Treat file ID as an identifier, **not a secret or authorization token**.

## 18.3 Sensitive document policy

Invoices/receipts can include names, addresses, GSTINs, phone numbers, customer identifiers and bank/payment references. Define before production:

- Data classification and purpose limitation.
- Encryption in transit (TLS) and at rest.
- Application, worker, DB, storage and model-provider access restrictions.
- Minimal retention for temporary OCR crops and intermediate images.
- Review of vendor processing/retention/region policies, applicable contracts and laws.
- Redacted logs/traces; no raw documents in application error strings.
- Backup access and restore testing.
- User-requested deletion, legal hold (if applicable), and deletion across replicas/backup lifecycle.
- Model training/data-use policy and opt-out/agreements appropriate to provider.

## 18.4 Permanent storage decision

The owner prefers indefinite original-file retention for auditing/debugging. **It is technically feasible but not universally appropriate.** The final production policy must explicitly cover consent/contractual basis, lawful retention, archival cost, deletion obligations, retention changes and backup expiration. Build retention metadata from day one if feasible. Do not equate “retain original for debugging” with “store every file forever without a deletion path”.

## 18.5 Dependency and runtime hygiene

- Pin/test compatible Python and third-party dependency versions; update security patches.
- Container runs as non-root where possible; use read-only base filesystem and dedicated writable work dirs.
- Set CPU/memory/pixel/render/time quotas for parsers/OCR workers.
- Use secrets manager/environment injection, not secrets in repository or prompts.
- Network egress from OCR/parser workers should be tightly restricted; external model access goes through a controlled adapter.
- Prevent model provider responses from initiating arbitrary local file access or URL fetches.

---

# 19. Observability, Quality, SLOs and Cost

## 19.1 Tracing

One `trace_id` correlates:

`HTTP request → file_id → job_id → LangGraph stages → OCR/model calls → validation → DB result`.

Record methods and versions, not complete raw sensitive documents by default. LangSmith or OpenTelemetry-based traces may be used after privacy controls are established.

## 19.2 Metrics

| Metric | Why |
|---|---|
| Upload success/failure by reason | Ingestion health |
| Queue depth and oldest waiting job | Backlog |
| Worker utilization and retry count | Capacity/errors |
| `read_complete`, `read_partial`, `read_failed` | Parser/OCR quality |
| Fallback rate by format/vendor | OCR performance and model cost |
| OCR time per page | Pipeline efficiency |
| LLM latency, token usage, provider errors | API cost/reliability |
| Job end-to-end p50/p95 latency | User experience |
| Field exact-match score per type | Extraction accuracy |
| Line-item precision/recall | Table extraction quality |
| `needs_review` rate | Operational burden |
| Arithmetic mismatch rate | Financial correctness |
| Cost per document and page | Unit economics |
| Storage growth and orphan-file count | Retention/consistency |

## 19.3 Quality objectives

Avoid unsupported promises such as “99% accurate” until a ground-truth dataset exists. Define actual **release targets after baseline measurements**. Useful dimensions:

- Critical amount/date/document-number field accuracy.
- False-positive rate for wrong totals marked `completed` (**especially important**).
- Percentage of files fully read vs partial/unreadable.
- Manual-review rate and review time.
- Accuracy by **format, scan quality, vendor layout, language, and page count**.
- Operational SLOs for `POST extraction` availability and job completion latency.

## 19.4 Cost controls

- Parse digital PDF natively first; OCR only necessary pages/regions.
- Stage low-cost OCR before optional paid Vision.
- Crop selectively but preserve label/context and compare benchmark performance.
- Cap pages, pixels, input tokens, output tokens, requests, repair attempts and time.
- Track model spend per job and format; investigate high fallback and repeated requests.
- Consider cached CDR by exact immutable file **and reader version** later, separately from content deduplication. Respect privacy and tenant boundaries.

---

# 20. Testing, Evaluation Dataset and Release Gates

## 20.1 Test pyramid

1. **Unit tests:** format sniffing, date parsers, amount normalizers, total rules, CDR/schema validation, routing logic.
2. **Adapter tests:** Image, DOCX, PDF parsers against fixtures; mock OCR/model providers.
3. **Contract tests:** reader outputs CDR v1; API responses stable; DB migrations safe.
4. **Integration tests:** storage + DB, job queue, LangGraph stages, retries/worker crashes.
5. **End-to-end tests:** upload real invoice → run extraction → final JSON + evidence.
6. **Security/performance tests:** malformed documents, decompression bombs, large pages, concurrency, failed dependencies.
7. **Regression evaluation:** same labeled documents after model/prompt/library/version changes.

## 20.2 Representative benchmark set

| Fixture | Expected behavior |
|---|---|
| Clear JPEG receipt | Complete CDR + correct reading |
| Rotated image | Orientation handled; original preserved |
| Low-light/faded receipt | Partial warnings or justified fallback |
| Receipt with `O/0` ambiguity | Numeric uncertainty preserved, not silently corrected |
| Long narrow receipt | Bounded OCR resource use |
| Hindi/English mixed receipt | Language-specific measurement, not assumed support |
| DOCX paragraph invoice | Sequential paragraphs captured |
| DOCX table with merged cells | Structure retained or specific warning |
| DOCX with embedded image | Shared OCR called |
| Digital PDF | Direct text extraction path |
| Scanned PDF | OCR path |
| Mixed-page PDF | Page-level routing |
| PDF page with mixed raster/vector | Region-based reading |
| Bad OCR text layer PDF | Quality gate triggers correction/review |
| Password-protected PDF | Explicit rejection |
| Wrong extension/MIME | Format mismatch error |
| PAN card JPEG | Valid upload, `unsupported` category |
| Two receipts in one photo/PDF | Review/segmentation-needed, not merged silently |
| Invoice with multi-rate GST | Preserve printed split tax structure |
| Amount arithmetic mismatch | Validation issue / review |
| Model timeout / rate-limit | Bounded retry and terminal state |
| Crash after file save before DB update | Recovery reconciles stale pending record |
| Worker duplicate task | Only one consistent final job result |

## 20.3 Ground-truth annotation strategy

For each fixture store: original file, document category, expected fields, line items, source spans/regions for key fields, ambiguity notes, reviewer consensus and schema version. Keep benchmark files access-controlled. For impossible-to-read documents, “unknown” is a legitimate correct expected value.

**Metrics:** document-type accuracy, field precision/recall/exact match, normalized value match, line-item precision/recall, total-error severity, source evidence coverage, latency and cost.

## 20.4 Practical release gates

- Critical rules and schemas covered by automated tests.
- No missing financial value silently invented by evaluator baseline.
- Known bad-total regression cases cannot pass as confidently completed.
- `PARTIAL/FAILED/UNSUPPORTED` behaviors are deterministic and documented.
- No unbounded resource consumption for malicious inputs.
- Crash recovery demonstrated for upload and extraction job flows.
- Production auth/security/privacy review complete before external exposure.
- Versioned API and rollback strategy documented.

---
# 21. Suggested Repository / Package Structure

This is a **target structure**. Create modules as they become necessary; avoid dozens of empty files on day one.

```text
invoice-extraction-service/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── v1_files.py
│   │   ├── v1_extractions.py
│   │   └── health.py
│   ├── core/
│   │   ├── settings.py
│   │   ├── error_codes.py
│   │   ├── logging.py
│   │   └── limits.py
│   ├── domain/
│   │   ├── upload_contracts.py
│   │   ├── cdr_contracts.py
│   │   ├── financial_contracts.py
│   │   ├── job_contracts.py
│   │   └── validation_issues.py
│   ├── storage/
│   │   ├── storage_interface.py
│   │   ├── local_storage.py
│   │   └── object_storage.py        # future
│   ├── readers/
│   │   ├── router.py
│   │   ├── image_reader.py
│   │   ├── docx_reader.py
│   │   └── pdf_reader.py
│   ├── ocr/
│   │   ├── image_quality.py
│   │   ├── preprocessing.py
│   │   ├── ocr_adapter.py
│   │   ├── vision_adapter.py
│   │   └── evidence_reconciler.py
│   ├── intelligence/
│   │   ├── classifier.py
│   │   ├── extraction_service.py
│   │   └── prompt_registry.py
│   ├── validators/
│   │   ├── schema_validation.py
│   │   ├── normalization.py
│   │   ├── financial_rules.py
│   │   └── evidence_checks.py
│   ├── workflow/
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   ├── state.py
│   │   └── routing.py
│   ├── services/
│   │   ├── ingestion_service.py
│   │   ├── extraction_job_service.py
│   │   └── result_service.py
│   ├── repositories/
│   │   ├── files_repository.py
│   │   ├── jobs_repository.py
│   │   └── results_repository.py
│   └── workers/
│       ├── tasks.py
│       └── recovery.py
├── migrations/
├── tests/
│   ├── fixtures/
│   ├── unit/
│   ├── adapters/
│   ├── integration/
│   ├── contracts/
│   ├── security/
│   └── evaluation/
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── adr/
│   └── runbooks/
├── docker/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml           # local development only
├── .env.example                  # no real secrets
└── README.md
```

### Package dependency direction

`API → services → domain/interfaces → adapters/repositories`; the domain schemas must not import FastAPI or a specific model vendor. Readers use shared CDR schema but not LangGraph internals. LangGraph imports service/adapters, not the reverse.

---

# 22. Configuration and Environment Profiles

## 22.1 Categories of configuration

| Category | Example keys/policies |
|---|---|
| API | Bind host, request timeout, CORS allowlist, client limits |
| Files | Allowed formats, max bytes, max PDF pages, max decoded pixels |
| Storage | Provider local/S3, private path/bucket, encryption |
| OCR | Engine, languages, DPI, per-page timeout, preprocess flags |
| Vision | Provider, model ID, max calls, max image size/crops |
| LLM | Provider, model, timeouts, structured-output mode, token budget |
| Graph | Retry budgets, status transitions, checkpoint provider |
| DB | Connection pool, migration version |
| Queue | Broker connection, worker concurrency, queue names, retry policy |
| Logging | Log levels, redaction, tracing enablement |
| Security | Authentication flag **only for restricted dev**, token verification config for production |
| Retention | Original/temporary/artifact lifetimes and deletion policy |

## 22.2 Environments

| Environment | Expectations |
|---|---|
| Developer laptop | Single FastAPI, PostgreSQL, persistent local storage; mocked LLM possible |
| CI | Temporary fixtures, stub providers, deterministic adapter/contract tests |
| Staging | Representative anonymized files; real queue and provider integration; auth enabled |
| Production | Auth and privacy controls, durable storage, queue, recovery, backups, alerts, scaling |

**Never** assume that the provider's latest model name or newest library version is permanently stable. Pin/test compatible versions, monitor release notes, and store exact versions in job metadata.

---

# 23. Technology Selection — Reasons, Alternatives, Lock-In

| Capability | Proposed | Why | Alternative / change trigger |
|---|---|---|---|
| Python web API | FastAPI | Type hints, request handling, API docs | Existing company API stack if mandated |
| Contracts | Pydantic | Nested typed models and serialization | Dataclass/JSON schema if interoperability demands |
| Image manipulation | Pillow + OpenCV | Decode, rotate, deskew and preprocess | Managed image pipeline |
| Primary OCR | Tesseract | Local, controllable baseline | Cloud document OCR if tables/languages fail benchmark |
| Difficult visual layouts | Vision-capable LLM | Contextual reading fallback | Managed Document AI + deterministic evidence merge |
| DOCX | python-docx | Direct paragraph/table access | Isolated rendering/converter for visual fidelity |
| PDF | PyMuPDF | Text blocks, coordinates, rendering | pdfplumber/others depending table benchmark/license |
| Structured LLM access | LangChain | Provider abstraction and schema output | Direct provider SDK if chain layer unnecessary |
| Workflow | LangGraph | Conditional stateful nodes, optional persistence | Plain Python pipeline for minimal MVP |
| DB | PostgreSQL | Reliable relational jobs + JSONB | Organization-approved relational DB |
| Queue | Celery + Redis | Background distribution/retries | Cloud-managed queue/worker platform |
| File storage | Persistent local initially | Owner already implemented it | S3/MinIO before distributed scaling |

**Licensing note:** Check the current licenses and commercial implications of selected libraries, particularly PDF-related software, before production distribution. Do not assume all packages have identical licenses.

---

# 24. Detailed Delivery Roadmap and Definition of Done

## Milestone 0 — Existing Upload Service: verify and freeze

**Already evidenced:** upload works and returns metadata/UUID.  
**Remaining validation checklist:**

- [ ] Extension/MIME/actual decoding checks verified with spoofed files.
- [ ] Byte/page/expanded-resource limits tested.
- [ ] Password-protected PDF rejection tested.
- [ ] Persisted local directory survives container restart/redeploy.
- [ ] DB `PENDING` → `STORED` and recovery tests pass.
- [ ] Public API does not expose internal `file_path` when productionizing.
- [ ] Authentication remains **restricted-environment-only** until production readiness.

**Output contract:** trusted `file_id`, verified metadata and durable file reference.

## Milestone 1 — Image Reader V1 (NEXT WORK)

1. Resolve existing file ID and load image safely.
2. Inspect orientation, dimensions, basic quality.
3. Produce text blocks + bounding boxes via OCR.
4. Convert to agreed CDR v1 with `COMPLETE/PARTIAL/FAILED`.
5. Add fixtures for clear and unreadable receipts.
6. Only after baseline: preprocessing and configurable Vision fallback.

**Definition of done:** clear receipt recognized; original untouched; CDR schema valid; unreadable image has explicit partial/failed behavior; no LangChain invoice extraction required.

## Milestone 2 — DOCX Reader

1. Safely open DOCX.
2. Read paragraphs, tables and document order.
3. Define headers/footers support and embedded image behavior.
4. Reuse OCR component for embedded raster content.
5. Emit same CDR schema; test merged cells and incomplete layout.

**Definition of done:** DOCX invoice text/table relationship preserved in CDR, with warnings where structure is not recoverable.

## Milestone 3 — PDF Reader

1. Digital page text and coordinate extraction.
2. Page-level native text quality assessment.
3. Render only scan/missing regions and reuse shared OCR.
4. Merge pages and mixed regions into CDR.
5. Test digital, scanned, mixed PDF and malformed/password cases.

**Definition of done:** one CDR contract across all three supported formats, with page-level evidence and partial failures.

## Milestone 4 — Classification + Schema

1. Freeze financial JSON v1/Pydantic models.
2. Define invoice/bill/receipt/unsupported classification behavior.
3. Write tests for nonfinancial images (e.g., PAN), unknown and mixed documents.
4. Define field-to-source evidence convention.

**Definition of done:** supported/unsupported policy and schema tests agreed.

## Milestone 5 — LangChain Extraction

1. Choose model/provider using labeled benchmark.
2. Implement structured extraction against CDR.
3. Add prompt/model versions and token budgets.
4. Test seller/buyer, dates, line items, GST and totals.
5. Handle missing values and ambiguous source evidence safely.

**Definition of done:** extraction returns schema-valid, evidence-linked financial data; accuracy measured, not assumed.

## Milestone 6 — Business Validation

1. Normalize dates, money and currencies.
2. Add line-item and invoice arithmetic rules.
3. Add invoice/receipt/bill-specific completeness policies.
4. Add issue codes and `needs_review` decisions.
5. Run regression set of known wrong totals.

**Definition of done:** key arithmetic conflicts cannot silently produce trusted `completed` status.

## Milestone 7 — LangGraph + Extraction API

1. Add job IDs/status endpoints.
2. Route file type to readers and CDR to classification/extraction.
3. Implement bounded targeted repairs.
4. Persist results, warnings, error codes, versions.
5. Test end-to-end with stored files and no second upload.

**Definition of done:** file upload → extraction job → final job JSON, including failure paths.

## Milestone 8 — Production Readiness

1. Enable authentication, ownership/tenant isolation, rate limits.
2. Move to queue and worker processes; validate idempotency and crash recovery.
3. Migrate to accessible durable storage if workers scale horizontally.
4. Establish retention/deletion/security/privacy policies.
5. Add monitoring, alerts, costs, load test and backup restore test.
6. Review external model data processing requirements and test rollback.

**Definition of done:** operational release gates in §20 pass; service may be exposed to intended users.

---

# 25. Failure Playbooks / Operational Runbooks

## 25.1 Uploaded file exists but DB row is `PENDING`

- Confirm record is older than the active upload lease/window.
- Check actual final file and exact size/checksum, not merely filename.
- If safely complete, atomically finalize DB state; if partial, quarantine/clean up and mark failed.
- Record a `recovery_event`, alert on repeated cases.

## 25.2 Job stuck in `PROCESSING`

- Check worker lease and trace/stage timestamps.
- Determine whether worker is still active; do not create duplicate work blindly.
- Reclaim only expired jobs with idempotent stage execution.
- Check queue depth, OCR process health and provider rate limits.

## 25.3 OCR gives text but financial totals are wrong

- Inspect source image/page and CDR block positions.
- Determine whether reading, LLM interpretation or validation caused the error.
- If reading error: targeted re-read and keep conflicting evidence.
- If interpretation error: targeted re-extraction with clear source context.
- If rules issue: fix validator; **do not change source observations**.
- Add regression test fixture before rolling out a fix.

## 25.4 Vision provider unavailable

- Use primary OCR evidence when reliable enough.
- If critical regions unreadable, mark partial/review.
- Retry transient rate-limit/service issues only within a bounded budget.
- Record provider error code, not raw secret/sensitive payload.

## 25.5 DB unavailable during finalization

- Store durable intermediate artifact if possible.
- Retry final DB update idempotently; avoid claiming completion to client before durable final state exists.
- Reconciler checks terminal artifacts and finalization events when DB recovers.

## 25.6 Sensitive document accidentally logged or exposed

- Restrict access and stop the leak.
- Follow incident response and data handling procedures.
- Assess impacted users and legal/contractual notification obligations.
- Purge unauthorized copies/traces where feasible and remediate logging/configurations.

---

# 26. What We Have NOT Fully Decided Yet (Explicit Open Questions)

This is the most important **architecture maturity list**. Do not treat every proposed technology/threshold in this document as final business approval.

| Decision | Default proposal | Evidence needed to finalize |
|---|---|---|
| Max file/page/image limits | 20 MiB / 20 PDF pages as illustrative starting limits | Production fixture sizes and performance tests |
| OCR engine | Start with Tesseract | Accuracy benchmark across photos, Hindi/English, tables |
| Vision model/provider | Pluggable Vision LLM fallback | Privacy, cost, latency and numeric accuracy comparison |
| LLM model/provider | Pluggable structured-output model | Ground-truth evaluations and provider policies |
| Multi-document per file | Unsupported/review initially | Business requirement and segmentation benchmark |
| Handwriting and languages | Best-effort / configured language support | Representative labeled dataset |
| Exact CDR schema fields | Contract in §6 | Adapter prototype feasibility |
| Extraction JSON specifics | Baseline in §11 | Downstream consumers/accounting requirements |
| Critical fields by category | Type-specific policy | Product owner acceptance criteria |
| Review workflow | Status and evidence hooks only | Human reviewer product requirement |
| Permanent retention | Owner preference, conditional | Privacy/legal/cost assessment |
| Production storage | S3/MinIO recommended | Hosting topology/security/cost |
| Recovery cadence/lease | Scheduled reconciler proposed | Load and operational SLO |
| Auth/JWT | Deferred in restricted MVP | Production integration contract |
| Queue delivery | Celery/Redis proposed | Deployment environment and throughput |
| Performance/quality SLO | Baseline then set targets | Benchmark results |
| Webhook | Optional | Client integration need |
| Vendor-specific extraction templates | Later optimization | Error analysis and repeated layouts |

---

# 27. Architecture Review Checklist (For Mentor / Engineer)

Before introducing a new component, answer in order:

1. **Responsibility:** Exactly one thing this module owns?
2. **Input:** Trusted IDs, metadata, bytes, or CDR? Who guarantees validity?
3. **Output:** Versioned typed contract? What happens when partially successful?
4. **Dependencies:** Storage, OCR, database, LLM or queue? Can it be mocked?
5. **Happy path:** What are its deterministic steps?
6. **Error path:** What can fail? Retryable or permanent? How represented?
7. **Evidence:** Can a reviewer trace important values back to the original page?
8. **Security:** Does it touch untrusted bytes, PII, models or external URLs?
9. **Performance:** Worst-case page/pixel/token/time/memory costs?
10. **Tests:** Which fixtures prove the component meets its contract?
11. **Monitoring:** Which signals will reveal a production failure?
12. **Future change:** Can provider, format or output version evolve independently?

**Teaching model (Hinglish):** Pehle *WHAT/WHY*, phir *INPUT/OUTPUT*, phir *SUBSTEPS*, phir *FAILURE CASES*, phir *TRADE-OFFS*, phir *TESTS*. Code sabse last mein. Ek component ka contract freeze karo, tab agla build karo.

---

# 28. Compact Architectural Decision Summary (One Page)

| Area | Final/current baseline |
|---|---|
| Architecture shape | One modular Python/FastAPI microservice |
| Original file handling | Existing upload API; unique ID; local persistent storage in MVP; metadata PostgreSQL |
| User auth | Deferred for **restricted MVP only**; mandatory before production exposure |
| Duplicate file content | Separate upload records; no SHA-based dedup initially |
| Original retention | Owner prefers permanent, but compliance/deletion/backup policy unresolved |
| Reader build order | **Image → DOCX → PDF** |
| OCR | Shared reusable adapter; OCR first |
| Vision | Selective, bounded severity-based fallback, not blind truth |
| Reading errors | `COMPLETE`, `PARTIAL`, `FAILED`; preserve warnings/evidence |
| PDF processing | Page/region-level native-text vs OCR routing |
| Reader output | Versioned **Common Document Representation (CDR)** |
| Business classification | Invoice/bill/receipt vs unsupported/unknown |
| LLM responsibilities | Structured financial interpretation via LangChain |
| Numeric/data rules | Decimal-safe deterministic validation, `null` for unknown |
| Conflict handling | Preserve candidates; unresolved → uncertain/review |
| Workflow | LangGraph deterministic graph with conditional routing and bounded repair |
| Background jobs | Sync tests first; async queue/worker for production |
| Delivery | `file_id` → `job_id` → status/result API |
| Reliability | Separate upload/job states; durable DB; idempotent recovery |
| Measurement | Accuracy, p95 latency, fallback rate, review rate, spend per document |
| Current next task | **Image Reader V1: stored image → OCR blocks/positions → CDR** |

---

# 29. References and Engineering Reading

The following public documentation was checked when preparing this blueprint. They are **technical references**, not a substitute for your team's own security review and reproducible benchmarking.

1. **FastAPI — Request Files / UploadFile:** https://fastapi.tiangolo.com/tutorial/request-files/
2. **OWASP — File Upload Cheat Sheet:** https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
3. **LangGraph — Overview:** https://docs.langchain.com/oss/python/langgraph/overview
4. **LangGraph — Persistence:** https://docs.langchain.com/oss/python/langgraph/persistence
5. **LangChain — Structured Output:** https://docs.langchain.com/oss/python/langchain/structured-output
6. **PyMuPDF — OCR:** https://pymupdf.readthedocs.io/en/latest/ocr/index.html
7. **PyMuPDF — Text Extraction:** https://pymupdf.readthedocs.io/en/latest/recipes-text.html
8. **python-docx — Quickstart:** https://python-docx.readthedocs.io/en/latest/user/quickstart.html
9. **python-docx — Images and Shapes:** https://python-docx.readthedocs.io/en/stable/user/shapes.html
10. **Celery — Introduction to Task Queues:** https://docs.celeryq.dev/en/stable/getting-started/introduction.html

---

# 30. Final Build Instruction

**Do not attempt to build everything at once.** Keep this file as the system's **architecture baseline**, update its decision register when real benchmarks change assumptions, and version it in the project repository.

**Your next concrete milestone:**

> Given the `file_id` of an already stored JPEG/PNG invoice/receipt, build an **Image Reader V1** that loads the stored file, reads text with OCR, captures block positions, returns a valid **CDR v1**, and reports `COMPLETE`, `PARTIAL` or `FAILED` with reasons. Do **not** implement invoice JSON, LangChain, or LangGraph before this reader contract is demonstrably stable.

After this milestone, implement **DOCX Reader**, then **PDF Reader reusing the same OCR adapter**. Add LLM extraction and validation only after the reader contract is reliable. Finally wrap the tested components with LangGraph, background jobs and production safeguards.

---

**End of Architecture Blueprint V1.0**  
*Scope note: this is a complete design baseline and build plan, not evidence that every component is already implemented or benchmark-verified.*
