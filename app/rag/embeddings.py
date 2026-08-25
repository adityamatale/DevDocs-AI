# rag/embeddings.py

# to cache and load it only once
from functools import lru_cache

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from app.config.settings import EMBEDDING_MODEL, DEVICE


@lru_cache(maxsize=1)
def get_embedding_model():
    return HuggingFaceEmbedding(
        model_name=EMBEDDING_MODEL,
        trust_remote_code=True,
        device=DEVICE,
    )