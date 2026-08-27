# DevDocs AI

A Retrieval-Augmented Generation (RAG) assistant that answers questions over FastAPI, LlamaIndex, and Python documentation — grounded, source-cited answers instead of generic LLM guesses.

## Why

General-purpose LLMs often hallucinate or go stale on fast-moving library docs. DevDocs AI ingests official documentation directly, chunks and embeds it, and retrieves the most relevant passages before generating an answer — so responses stay grounded in the actual source docs and come with citations back to them.

## Features

- 📥 Documentation ingestion (FastAPI, LlamaIndex, Python)
- 🔎 Two-stage vector retrieval + reranking
- 🤖 Local LLM inference with Ollama (no external API dependency)
- 🌐 FastAPI backend with streaming support
- 💬 Streamlit frontend with streaming responses
- 📊 OpenTelemetry + Jaeger tracing
- 🐳 Fully containerized deployment
- 💾 Persistent Qdrant storage

## Stack

| Component | Technology |
|---|---|
| Backend | Python + FastAPI |
| RAG framework | LlamaIndex |
| Vector DB | Qdrant (Dockerized, persistent volume) |
| Embeddings | `Qwen/Qwen3-Embedding-0.6B` (1024-dim, cosine similarity) |
| Reranker | BGE FlagReranker (`BAAI/bge-reranker-v2-m3`) |
| LLM | Ollama (runs on host machine) |
| Frontend | Streamlit |
| Tracing | OpenTelemetry + Jaeger |
| Deployment | Docker + Docker Compose |

## Architecture

```text
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
    ↓
Streamlit frontend
```

Current dataset: **~23,800 source documents → ~37,900 chunks**.

## Project Structure

```
DevDocs-AI/
├── app/
│   ├── api/
│   ├── rag/
│   └── ...
├── streamlit_client/
├── download_fastapi_docs.py    # Fetches FastAPI documentation
├── download_llamaindex_docs.py # Fetches LlamaIndex documentation
├── download_python_docs.py     # Fetches Python documentation
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── setup.sh
├── requirements.txt
└── .env.example
```

## Requirements

- Docker
- Docker Compose
- Ollama
- NVIDIA Container Toolkit (optional, for GPU support)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/adityamatale/DevDocs-AI.git
   cd DevDocs-AI
   ```

2. Make the setup script executable:
   ```bash
   chmod +x setup.sh
   ```

3. Run the interactive setup:
   ```bash
   ./setup.sh
   ```
   It lets you choose:
   - `1) Local` → build Docker images locally
   - `2) Production` → pull images from Docker Hub

### Other setup commands

```bash
./setup.sh --local     # build images locally
./setup.sh --prod      # pull published images from Docker Hub
./setup.sh --ingest    # run document ingestion
./setup.sh --all       # setup + ingest
./setup.sh --status    # check running containers
./setup.sh --stop      # stop the stack
./setup.sh --clean     # tear down and clean up
```

## Configuration

Create your environment file:

```bash
cp .env.example .env
```

Configure the required API keys and model settings in `.env`.

For the Streamlit frontend:

```bash
cp streamlit_client/.streamlit/secrets.example.toml \
   streamlit_client/.streamlit/secrets.toml
```

Add the required backend URLs/secrets (`secrets.toml` is excluded from Git).

## Docker Services

Runs on a shared `devdocs_default` network (services talk to each other by name, e.g. `http://qdrant:6333`):

| Service | URL | Notes |
|---|---|---|
| RAG API | http://localhost:8000 | FastAPI + Uvicorn; Swagger at `/docs` |
| Streamlit Frontend | http://localhost:8501 | Chat UI |
| Qdrant | http://localhost:6333 | Persistent named volume (`qdrant_data`) |
| Jaeger | http://localhost:16686 (UI) / :4318 (OTLP HTTP) | Distributed tracing |
| Ollama | `http://host.docker.internal:11434` | Runs on the **host** (via Snap), not in Compose; reconfigured to listen on `*:11434` and reached via `extra_hosts: host-gateway` |

Two host-side resources are mounted in rather than baked into the image:
- `~/.cache/huggingface` → `/root/.cache/huggingface` (~33 GB) — avoids re-downloading embedding/reranker models on every rebuild
- `qdrant_data` Docker volume → `/qdrant/storage` (~1.6 GB) — persistent vector storage; existing collections (37.9k points, 1024-dim, cosine) were migrated from an ephemeral container and verified intact

Common commands:

```bash
docker compose up --build -d      # build & start all services
docker compose logs -f rag-api    # tail a service's logs
docker compose ps                 # check running containers
docker compose down               # stop the stack
```

## API

### `POST /query`
Synchronous request, returns a complete JSON response.

### `POST /query/stream`
Server-Sent Events (SSE) stream, emitting:
- `token`
- `sources`
- `done`
- `error`

Pydantic-validated request bodies (query length constrained to 1–2000 characters), with basic structured error handling across both endpoints.

## RAG Pipeline

Two-stage retrieval for precision:

1. Embed the query with `Qwen3-Embedding-0.6B`
2. Retrieve the top 30 candidates from Qdrant (cosine similarity)
3. Rerank candidates with the BGE FlagReranker
4. Keep the top 10 results
5. Generate an answer with Ollama, constrained by a strict documentation-grounded `PromptTemplate`
6. Return the answer together with its source document paths (streaming supported)

The ingestion pipeline is deterministic and resumable: every chunk gets a UUID5-based ID (derived from source + content), and a pre-run check skips chunks already in Qdrant — so an interrupted ingestion run can simply be restarted without creating duplicate vectors. Ingestion is batched (64 chunks/batch).

### FastAPI multi-language deduplication

FastAPI's docs ship translated copies of every page (`docs/en/`, `/fr/`, `/de/`, `/ru/`, `/hi/`, `/es/`, `/pt/`, ...). Ingesting every locale caused near-duplicate, non-English results to crowd out useful chunks. Fixed by scoping ingestion to `fastapi/docs/en/` and `fastapi/examples/`, excluding all other locales (LlamaIndex and Python datasets unaffected).

## Observability

Instrumented with **OpenTelemetry**, using LlamaIndex's built-in OTel instrumentation to automatically trace retrieval, embedding, and LLM calls. Traces are exported via OTLP HTTP to **Jaeger**.

A custom top-level `rag.query` span wraps the full RAG flow (used in both the standard and streaming code paths), with four custom attributes for at-a-glance query insight:
- `rag.query`
- `rag.retrieved_count`
- `rag.top_score`
- `rag.response_length`

Typical trace shape:

```
rag.query
├── VectorIndexRetriever.retrieve
│   └── HuggingFaceEmbedding.get_query_embedding
└── Ollama.complete
    └── Ollama.chat
```

## Frontend (Streamlit)

A lightweight Streamlit UI, streaming answers with source citations.

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

Run standalone (backend must already be running via `uvicorn app.main:app`):

```bash
cd streamlit_app
pip install streamlit requests
streamlit run app.py
```

## Docker Images

Published to Docker Hub:
- `mattyisback/devdocs-rag-api`
- `mattyisback/devdocs-frontend`

`docker-compose.prod.yml` pulls these instead of building locally.

## Known Limitations

- Retrieval quality is still a work in progress — queries can surface off-topic results (e.g. a FastAPI-specific question returning LlamaIndex pages), pointing to a retrieval/ranking gap rather than a generation problem.
- Embedding and reranking currently run on CPU inside the container (`torch.cuda.is_available()` → `False`); GPU passthrough isn't enabled yet.
- Ollama currently runs separately on the host rather than in Compose.

## Roadmap

- [ ] Improve retrieval precision
- [ ] Source/language-aware metadata filtering and deduplication at retrieval time
- [ ] Improved chunking strategy
- [ ] Query rewriting for ambiguous/underspecified questions
- [ ] GPU passthrough (NVIDIA Container Toolkit + CUDA-enabled PyTorch)
- [ ] Further evaluation of retrieval quality

## Status

🔄 **Actively in development.** The core RAG pipeline, API, Streamlit frontend, Qdrant persistence, Docker deployment, Docker Hub publishing, and Jaeger tracing are all functional. GPU passthrough and further retrieval-quality improvements are next.