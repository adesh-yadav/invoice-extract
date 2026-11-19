# 📑 Invoice Extract API

## Extraction pipeline

The existing upload API stores the original file. A separate extraction job then reads the stored file through image, DOCX, or PDF adapters, classifies it, extracts typed fields through LangChain, validates source evidence and arithmetic, and persists the result. LangGraph controls stage routing. The API and worker share PostgreSQL plus persistent upload/artifact volumes.

Compose binds the API and PostgreSQL to `127.0.0.1` while authentication is deferred. Configure ownership and authentication before allowing remote access.

Select the AI provider in `.env`; the worker reads the selector when it starts. `OCR_LANGUAGES` defaults to `eng` (the Docker image also includes Hindi OCR data). An API provider without a key still reads and classifies a document, then reports `MODEL_NOT_CONFIGURED`.

| Provider | `.env` values | Model default |
|---|---|---|
| OpenAI | `LLM_PROVIDER=openai`, paste `OPENAI_API_KEY` | `gpt-4.1-mini` |
| Claude | `LLM_PROVIDER=anthropic`, paste `ANTHROPIC_API_KEY` | `claude-haiku-4-5-20251001` |
| Ollama | `LLM_PROVIDER=ollama`; no API key | `gemma3:4b` |

Leave `EXTRACTION_MODEL=` blank for the selected provider default, or set an exact model name. `VISION_PROVIDER=` defaults to `LLM_PROVIDER`; set it to `openai`, `anthropic`, or `ollama` to use a different provider for OCR vision fallback. `VISION_MODEL=` defaults to the extraction model when providers match, or the vision provider's default when they differ. The worker reads the corresponding provider key from `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`; Ollama needs its model pulled locally. For example, use `LLM_PROVIDER=anthropic`, `VISION_PROVIDER=openai`, and both provider keys to extract with Claude and read difficult images with OpenAI vision. If you choose a text-only Ollama extraction model, set `VISION_PROVIDER=ollama`, `VISION_MODEL=gemma3:4b` and pull both models, or set `ENABLE_VISION_FALLBACK=false`. Restart the worker after changing `.env` with `docker compose up -d --force-recreate worker`. Keep API keys in the ignored `.env` file; do not commit them.

For local Ollama, start its Docker service and pull the default model into the persistent `ollama_models` volume:

```bash
./scripts/ollama-model.sh pull gemma3:4b
./scripts/ollama-model.sh list
./scripts/ollama-model.sh run gemma3:4b
docker compose --profile ollama up -d --build
```

The model tag in `EXTRACTION_MODEL` must match the pulled tag. The default Ollama service runs on CPU and is published only to localhost; `OLLAMA_BASE_URL=http://ollama:11434` is the address used by the worker container. Official setup details: [LangChain Claude](https://docs.langchain.com/oss/python/integrations/chat/anthropic), [LangChain Ollama](https://docs.langchain.com/oss/python/integrations/chat/ollama), [Ollama Docker](https://docs.ollama.com/docker).

```bash
docker compose up -d --build
docker compose run --rm --no-deps api python -m unittest discover -s tests -q
```

After upload, use the returned `id` as `file_id`:

```bash
curl -X POST http://localhost:8000/v1/extractions \
  -H 'Content-Type: application/json' \
  -d '{"file_id":"YOUR_FILE_ID"}'
curl http://localhost:8000/v1/extractions/YOUR_JOB_ID
curl http://localhost:8000/v1/extractions/YOUR_JOB_ID/cdr
```

`POST /v1/extractions` returns `202` with a job ID. Poll `GET /v1/extractions/{job_id}` for `completed`, `needs_review`, `unsupported`, or `failed`. The CDR endpoint exposes source text and must only be used in a restricted environment until authentication and ownership checks are added. `POST /v1/extractions/{job_id}/retry` creates a new job for failed or reviewable results.

Repository layout: `src/modules/extraction/domain` owns CDR and financial contracts; `application` owns ports and use cases; `adapters/outbound` owns OCR, readers, LLM, LangGraph, and persistence; `adapters/inbound/rest` owns HTTP; `config/module.py` wires dependencies. New services should depend inward through the ports.

Graphify is installed as a Codex skill. `graphify-out/graph.json`, `graph.html`, and `GRAPH_REPORT.md` document the code relationships. Run `graphify update .` after code edits and `graphify query "<question>"` to navigate the graph. The local `AGENTS.md` records architecture and verification rules.

This is a development MVP using **hexagonal architecture**, **DDD**, PostgreSQL, and Docker persistent volumes. Production deployment still requires authentication, authorization, migrations, provider benchmarking, and representative document evaluation.

---

## 🌐 Swagger UI & Interactive Documentation

Once the server is running, you can access:

- **Swagger UI (Interactive API Explorer)**: [http://localhost:8000/docs](http://localhost:8000/docs)
  - Features live **"Try it out"** on all endpoints.
  - Interactive file upload directly from your browser.
  - Search filter bar enabled.
- **ReDoc (Alternative Clean Documentation)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema (JSON)**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- **Root URL Redirect**: Opening [http://localhost:8000/](http://localhost:8000/) automatically redirects to `/docs`.

---

## 🚀 Running with Docker Compose

1. **Start containers**:
   ```bash
   docker compose up --build
   ```
   *(Or in background: `docker compose up -d --build`)*

2. **Open Swagger UI**:
   Navigate to [http://localhost:8000/docs](http://localhost:8000/docs).

3. **Stop containers**:
   ```bash
   docker compose down
   ```

---

## 📌 Available Endpoints in Swagger UI

| Method | Endpoint | Summary |
|---|---|---|
| `POST` | `/v1/files/upload` | Upload invoice bill (pre-registers PENDING in DB, stores with UUID name to volume, finalizes SUCCESS) |
| `GET` | `/v1/files/{file_id}` | Retrieve file details & lifecycle status by UUID |
| `GET` | `/v1/files` | Paginated listing of uploaded files |
| `GET` | `/v1/files/{file_id}/download` | Download physical binary file from storage volume |
| `GET` | `/health` | Health check endpoint |

---

## 🧪 Testing File Upload via cURL

```bash
curl -X POST "http://localhost:8000/v1/files/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/invoice.pdf"
```
