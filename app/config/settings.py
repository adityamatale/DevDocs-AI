# config/settings.py
import os
from dotenv import load_dotenv
load_dotenv()


# Device
DEVICE = os.getenv("DEVICE", "cpu")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# HuggingFace
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
EMBEDDING_DIMENSION = os.getenv("EMBEDDING_DIMENSION", "1024")


# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "devdocs_test")


# Embedding / Vector Store
VECTOR_DISTANCE = os.getenv("VECTOR_DISTANCE", "Cosine")


# Chunking
CHUNK_SIZE = os.getenv("CHUNK_SIZE", "512")
CHUNK_OVERLAP = os.getenv("CHUNK_OVERLAP", "50")


# Retrieval
CANDIDATE_TOP_K = int(os.getenv("CANDIDATE_TOP_K", "15"))
FINAL_TOP_K = int(os.getenv("FINAL_TOP_K", "5"))

# Reranker
RERANK_MODEL = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")

# LLM
OLLAMA_MODEL_NAME=os.getenv("OLLAMA_MODEL_NAME", "llama3.2")
OLLAMA_BASE_URL=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_REQUEST_TIMEOUT=os.getenv("OLLAMA_REQUEST_TIMEOUT", "120")
OLLAMA_CONTEXT_WINDOW=os.getenv("OLLAMA_CONTEXT_WINDOW", "8192")

# Opentelemetry
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "devdocs-rag")
OTLP_EXPORTER_PATH = os.getenv("OTLP_EXPORTER_PATH", "http://localhost:4318/v1/traces")