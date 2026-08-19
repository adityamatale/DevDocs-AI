# config/settings.py
import os
from dotenv import load_dotenv
load_dotenv()


# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# HuggingFace
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_DIMENSION = os.getenv("EMBEDDING_DIMENSION")


# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")


# Embedding / Vector Store
VECTOR_DISTANCE = os.getenv("VECTOR_DISTANCE")


# Chunking
CHUNK_SIZE = os.getenv("CHUNK_SIZE")
CHUNK_OVERLAP = os.getenv("CHUNK_OVERLAP")


# Retrieval
CANDIDATE_TOP_K = int(os.getenv("CANDIDATE_TOP_K"))
FINAL_TOP_K = int(os.getenv("FINAL_TOP_K"))

# Reranker
RERANK_MODEL = os.getenv("RERANK_MODEL")

# LLM
OLLAMA_MODEL_NAME=os.getenv("OLLAMA_MODEL_NAME")
OLLAMA_BASE_URL=os.getenv("OLLAMA_BASE_URL")
OLLAMA_REQUEST_TIMEOUT=os.getenv("OLLAMA_REQUEST_TIMEOUT")
OLLAMA_CONTEXT_WINDOW=os.getenv("OLLAMA_CONTEXT_WINDOW")