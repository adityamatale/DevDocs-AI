# DevDocs AI

A Retrieval-Augmented Generation (RAG) assistant that answers questions over FastAPI, LlamaIndex, and Python documentation — grounded, source-cited answers instead of generic LLM guesses.

## Why

General-purpose LLMs often hallucinate or go stale on fast-moving library docs. DevDocs AI ingests official documentation directly, chunks and embeds it, and retrieves the most relevant passages before generating an answer — so responses stay grounded in the actual source docs and come with citations back to them.

## Stack

- **Backend:** Python + FastAPI
- **RAG framework:** LlamaIndex
- **Vector DB:** Qdrant (Dockerized, persistent volume)
- **Embeddings:** `Qwen/Qwen3-Embedding-0.6B` (1024-dim, cosine similarity), cached locally via Hugging Face
- **Reranker:** BGE FlagReranker (`BAAI/bge-reranker-v2-m3`)
- **LLM:** Ollama (runs on host machine)
- **Tracing:** Jaeger (Dockerized, OTLP HTTP)
- **Deployment:** Dockerfile + `docker-compose.yml` (`rag-api`, `qdrant`, `jaeger`; Ollama reached via `host.docker.internal`)

## Project Structure

```
DevDocs-AI/
├── app/                        # Core application code (ingestion, RAG, API)
├── download_fastapi_docs.py    # Fetches FastAPI documentation
├── download_llamaindex_docs.py # Fetches LlamaIndex documentation
├── download_python_docs.py     # Fetches Python documentation
├── setup.sh                    # Environment/setup script
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Architecture

```
Documents (MD, HTML, PY, TXT, PDF)
    ↓
Chunking + Embedding (Qwen3-Embedding-0.6B)
    ↓
Qdrant (vector store, collection: devdocs)
    ↓
Retriever (top 30 candidates)
    ↓
BGE Reranker → top 10
    ↓
PromptTemplate (strict, documentation-grounded)
    ↓
Ollama LLM
    ↓
FastAPI
    ├── POST /query          (JSON response)
    └── POST /query/stream   (SSE: token / sources / done / error)
```

## Features

### 📥 Document Ingestion
- Dedicated scripts pull down official documentation for FastAPI, LlamaIndex, and Python (`download_fastapi_docs.py`, `download_llamaindex_docs.py`, `download_python_docs.py`).
- Loads and chunks documentation across multiple formats — Markdown, HTML, Python source, plain text, and PDF.
- Current dataset: **~23,800 source documents → ~37,900 chunks**.
- Batched ingestion (64 chunks/batch) into Qdrant via LlamaIndex's `QdrantVectorStore` + `StorageContext` + `VectorStoreIndex`.
- **Idempotent & resumable:** every chunk gets a deterministic ID (`uuid.uuid5` over source + content), and a pre-run check (`get_existing_ids()`) skips chunks already in Qdrant — so an interrupted ingestion run can simply be restarted without creating duplicate vectors.
- Designed to survive long unattended runs (`systemd-inhibit` used during development to stop the machine sleeping mid-ingestion).

### 🌍 FastAPI Multi-Language Deduplication

FastAPI's docs ship translated copies of every page (`fastapi/docs/en/`, `/fr/`, `/de/`, `/ru/`, `/hi/`, `/es/`, `/pt/`, ...). Ingesting all locales caused retrieval to return near-duplicate, non-English results for a single query (e.g. `first-steps.md` in five different languages before a useful chunk).

**Fix:** updated the loader to keep `fastapi/docs/en/` and `fastapi/examples/`, and exclude every other FastAPI locale. Other datasets (LlamaIndex, Python) unchanged.

**Result:**
```
Total documents loaded: 13293
FastAPI sources:
Counter({'fastapi': 2071})
```

**Note:** an earlier check for `/en/` anywhere in the path wrongly flagged `fastapi/examples/` files as non-English. Fixed by scoping the check to the docs directory:
```python
if "/fastapi/docs/" in path and "/en/" not in path:
    print(path)  # now prints nothing
```

### 🔎 Retrieval & Reranking
- Query embedding via the same Qwen3 embedding model, matched against Qdrant using cosine similarity.
- Two-stage retrieval for precision: an initial pull of the **top 30** candidates, narrowed to a **final top 10** by a BGE FlagReranker.
- Retrieval results are returned as deterministic node + score objects for consistent downstream ranking.

### ✍️ Generation
- Local LLM inference via **Ollama** — no external API dependency for generation.
- A strict, documentation-grounded `PromptTemplate` constrains answers to the retrieved context, reducing hallucination.
- Returns both the generated answer and the source document paths it was grounded in.
- Supports token-by-token **streaming** generation in addition to standard single-shot responses.

### 🌐 API
- Built with FastAPI:
  - `POST /query` — synchronous JSON request/response.
  - `POST /query/stream` — Server-Sent Events (SSE) stream, emitting `token`, `sources`, `done`, and `error` events.
- Pydantic-validated request bodies (query length constrained to 1–2000 characters).
- Basic structured error handling across both endpoints.

### 📊 Observability
- Instrumented with **OpenTelemetry**, using LlamaIndex's built-in OTel instrumentation to automatically trace retrieval, embedding, and LLM calls.
- Traces exported via **OTLP HTTP** to **Jaeger** (run in Docker, UI on `localhost:16686`).
- A custom top-level `rag.query` span wraps the full RAG flow, applied consistently to both `generate_answer()` and `generate_answer_stream()`.
- Four custom span attributes for at-a-glance query insight: `rag.query`, `rag.retrieved_count`, `rag.top_score`, `rag.response_length`.
- Typical trace shape:
  ```
  rag.query
  ├── VectorIndexRetriever.retrieve
  │   └── HuggingFaceEmbedding.get_query_embedding
  └── Ollama.complete
      └── Ollama.chat
  ```
- `Ollama.complete → Ollama.chat` are nested LlamaIndex spans for a single call, not two separate LLM requests.

## Frontend (Streamlit)

A lightweight Streamlit UI for DevDocs AI, streaming answers with source citations.

**Structure**

```
streamlit_app/
├── .streamlit/
│   ├── config.toml     # theme
│   └── secrets.toml    # API endpoints
├── app.py               # entry point
├── styles.py            # CSS
├── api.py               # backend calls
└── chat.py              # session state + rendering
```

**Setup**

```bash
cd streamlit_app
pip install streamlit requests
streamlit run app.py
```

Make sure the FastAPI backend is running (`uvicorn app.main:app`) before starting the frontend. Backend URLs are configured in `.streamlit/secrets.toml`.

### 🐳 Deployment

Fully containerized via Docker Compose, running three services on a shared `devdocs_default` network (services talk to each other by name, e.g. `http://qdrant:6333`, `http://jaeger:4318`):

- **rag-api** (`:8000`) — FastAPI + Uvicorn, LlamaIndex, Qdrant client, embedding + reranker models
- **qdrant** (`:6333`) — vector DB, backed by a persistent named volume (`qdrant_data`) so collections survive container recreation. Existing collections (37.9k points, 1024-dim, cosine) were migrated from an ephemeral container into this volume and verified intact.
- **jaeger** (`:16686` UI / `:4318` OTLP) — distributed tracing (Jaeger 2.20.0)

Two host-side resources are mounted in rather than baked into the image:
- `~/.cache/huggingface` → `/root/.cache/huggingface`, so embedding/reranker models aren't re-downloaded on every rebuild (~33 GB cache)
- `qdrant_data` Docker volume → `/qdrant/storage`, for persistent vector storage (~1.6 GB)

**Ollama runs on the host** (via Snap), not in Compose. It was reconfigured to listen on `*:11434` (was `127.0.0.1` only) so the container can reach it at `http://host.docker.internal:11434`, enabled via `extra_hosts: host-gateway`.

Common commands:
```bash
docker compose up --build -d      # build & start all services
docker compose logs -f rag-api    # tail a service's logs
docker compose ps                 # check running containers
docker compose down               # stop the stack
```

**Current limitation:** the RAG image installs CPU-only PyTorch, so embedding/reranking run on CPU (`torch.cuda.is_available()` → `False`); the host NVIDIA GPU isn't passed through yet. Next step is adding the NVIDIA Container Toolkit and a CUDA-enabled PyTorch build to move embedding/reranking onto GPU.

- `setup.sh` for local (non-Docker) environment bootstrap.

## Known Limitations

- Retrieval quality is still a work in progress — queries can surface off-topic results (e.g., a FastAPI-specific question returning LlamaIndex pages), which points to a retrieval/ranking gap rather than a generation problem.
- Embedding/reranking currently run on CPU inside the container; GPU passthrough not yet enabled.

## Roadmap

- [ ] Source/language-aware metadata filtering and deduplication at retrieval time
- [ ] Improved chunking strategy to boost retrieval precision
- [ ] Query rewriting to better handle ambiguous or underspecified questions
- [ ] Frontend UI
- [ ] GPU passthrough for the RAG container (NVIDIA Container Toolkit + CUDA PyTorch)

## Status

🔄 Actively in development — ingestion and core pipeline (retrieval → rerank → generation → API) are functional, the full stack (RAG API, Qdrant, Jaeger) is containerized with persistent storage; GPU passthrough and further retrieval-quality improvements are next.