# Implementation status against Blueprint V1.0

| Milestone | Current state | Evidence / limitation |
|---|---|---|
| 0 Upload | Implemented and hardened | Existing upload preserved; format/size inspection, atomic write, stale PENDING reconciliation added. Existing and new tests pass. |
| 1 Image reader | Implemented | Pillow decode, Tesseract blocks with normalized boxes, optional bounded vision fallback, CDR status and warnings. Mocked reader and generated receipt OCR smoke tested. |
| 2 DOCX reader | Implemented | Ordered paragraphs/tables, header/footer text and shared OCR for embedded images. Nested/floating layout fidelity needs real fixtures. |
| 3 PDF reader | Implemented | Page-level native/OCR routing, mixed raster handling, table extraction attempt, page warnings. Complex invoice table benchmark still needed. |
| 4 Classification/schema | Implemented baseline | Conservative rules for invoice/bill/receipt and unsupported/unknown. Ambiguous documents route to review. |
| 5 LangChain extraction | Wired; live verification pending | Structured `ExtractionPayload`, prompt version and source citations. Requires `OPENAI_API_KEY` in local `.env` for provider test. |
| 6 Validation | Implemented baseline | Decimal normalization, evidence checks, GSTIN format, date, line item and totals checks. Needs representative financial document evaluation. |
| 7 LangGraph/API/jobs | Implemented | Durable DB job rows, worker lease/recovery, one bounded repair, result persistence, create/status/retry/CDR endpoints. Smoke tested to OCR and model configuration boundary. |
| 8 Production readiness | Open | Authentication/ownership, real migration plan, provider cost and privacy review, benchmark SLOs, backups and operational policy are not finalized. Blueprint explicitly defers some of these decisions. |

## Verification

- `docker compose up -d --build` starts API, worker and PostgreSQL.
- `docker compose run --rm --no-deps api python -m unittest discover -s tests -q` passes 21 tests.
- `GET /health/ready` returns ready with PostgreSQL available.
- A generated PNG receipt uploaded through `/v1/files/upload` produced a valid OCR CDR and extraction job. Its job ended with `MODEL_NOT_CONFIGURED` because no provider key is configured; this is the expected technical result for the current environment.
- `graphify update .` generated the code graph in `graphify-out/` (592 nodes, 1319 edges at this snapshot).

## Next release gates

1. Set provider key locally and run a live extraction on anonymized invoice, bill and receipt fixtures. Do not put credentials in chat or commit them.
2. Evaluate labeled image/DOCX/PDF samples, especially multi-page tables, tax-inclusive totals, low quality OCR and Hindi text. Tune reader routing and review policy from measured errors.
3. Add authentication, file ownership and migrations before exposing the service outside a restricted development network.
