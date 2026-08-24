# DevDocs AI

A Retrieval-Augmented Generation (RAG) assistant that answers questions over FastAPI, LlamaIndex, and Python documentation — grounded, source-cited answers instead of generic LLM guesses.

## Why

General-purpose LLMs often hallucinate or go stale on fast-moving library docs. DevDocs AI ingests official documentation directly, chunks and embeds it, and retrieves the most relevant passages before generating an answer — so responses stay grounded in the actual source docs and come with citations back to them.

## Stack

- **Backend:** Python + FastAPI
- **RAG framework:** LlamaIndex
- **Vector DB:** Qdrant (local, Docker-managed)
- **Embeddings:** `Qwen/Qwen3-Embedding-0.6B` (1024-dim, cosine similarity), cached locally via Hugging Face
- **Reranker:** BGE FlagReranker
- **LLM:** Ollama (local)
- **Deployment:** Dockerfile + `docker-compose.yml`

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
- Containerized with a `Dockerfile` and `docker-compose.yml` for running the API and Qdrant together.
- `setup.sh` for local environment bootstrap.

## Known Limitations

- Retrieval quality is still a work in progress — queries can surface off-topic results (e.g., a FastAPI-specific question returning LlamaIndex pages), which points to a retrieval/ranking gap rather than a generation problem.

## Roadmap

- [ ] Source/language-aware metadata filtering and deduplication at retrieval time
- [ ] Improved chunking strategy to boost retrieval precision
- [ ] Query rewriting to better handle ambiguous or underspecified questions
- [ ] Frontend UI

## Status

🔄 Actively in development — ingestion and core pipeline (retrieval → rerank → generation → API) are functional; retrieval-quality improvements and a frontend are next.