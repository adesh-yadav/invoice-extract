# Implementation status against Blueprint V1.0

| Milestone | Current state | Evidence / limitation |
|---|---|---|
| 0 Upload | Implemented and hardened | Existing upload preserved; format/size inspection, atomic write, stale PENDING reconciliation added. Existing and new tests pass. |
| 1 Image reader | Implemented | Pillow decode, Tesseract blocks with normalized boxes, optional bounded vision fallback, CDR status and warnings. Mocked reader and generated receipt OCR smoke tested. |
| 2 DOCX reader | Implemented | Ordered paragraphs/tables, header/footer text and shared OCR for embedded images. Nested/floating layout fidelity needs real fixtures. |
| 3 PDF reader | Implemented | Page-level native/OCR routing, mixed raster handling, table extraction attempt, page warnings. Complex invoice table benchmark still needed. |
| 4 Classification/schema | Implemented baseline | Conservative rules for invoice/bill/receipt and unsupported/unknown. Ambiguous documents route to review. |
| 5 LangChain extraction | Implemented; Claude live smoke verified | Structured `ExtractionPayload`, source citations, optional bounded repair. OpenAI, Claude, Google and Ollama adapters; role-specific provider/model selectors share one key per provider. Only Claude has a configured valid key for live calls. |
| 6 Validation | Implemented baseline | Decimal normalization, evidence checks, GSTIN format, date, line item and totals checks. Needs representative financial document evaluation. |
| 7 LangGraph/API/jobs | Implemented | Upload auto-queues background extraction; durable jobs, ordered DB events, extracted JSON, validation and full CDR in PostgreSQL; worker lease/recovery and one bounded repair. Create/status/retry/CDR endpoints. |
| 8 Production readiness | Open | Authentication/ownership, real migration plan, provider cost and privacy review, benchmark SLOs, backups and operational policy are not finalized. Blueprint explicitly defers some of these decisions. |

## Verification

- `docker compose up -d --build` starts API, worker and PostgreSQL.
- `docker compose run --rm --no-deps api python -m unittest discover -s tests -q` passes 32 tests.
- `GET /health/ready` returns ready with PostgreSQL available.
- The configured Anthropic key returned a live Claude response; structured synthetic receipt extraction returned seller, total and evidence. `.env` currently selects Claude for extraction and vision fallback. Ollama is stopped by user request.
- `scripts/e2e_smoke.py` passed API uploads and automatic jobs for native PDF invoice, DOCX bill, PNG receipt, JPEG bill, scanned PDF invoice, mixed PDF invoice and DOCX with embedded image. Unknown and blank inputs entered review; unsupported document was gated; unsupported, corrupt, empty, oversized and password-protected uploads returned expected 415/422/413 errors. Missing-file, retry and idempotency paths passed. These are synthetic cases, not a labeled real-document accuracy benchmark.
- A low-confidence image triggered Tesseract, optional Claude OCR cleanup, and Claude vision. The raw OCR and both AI candidates were preserved separately; conflict routed the job to `needs_review`. Cleanup was then restored to its disabled default.
- PostgreSQL contains extracted JSON, validation, ordered processing events and full CDR JSON. Existing CDR artifacts were backfilled into `extraction_sources` with no missing artifacts.
- `graphify update .` generates the code graph in `graphify-out/`.

## Next release gates

1. For OpenAI/Claude, set the selected provider key locally; for Ollama, pull the configured model. Run a live extraction on anonymized invoice, bill and receipt fixtures. Do not put credentials in chat or commit them.
2. Evaluate labeled image/DOCX/PDF samples, especially multi-page tables, tax-inclusive totals, low quality OCR and Hindi text. Tune reader routing and review policy from measured errors.
3. Add authentication, file ownership and migrations before exposing the service outside a restricted development network.
