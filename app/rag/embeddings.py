# rag/embeddings.py

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from app.config.settings import EMBEDDING_MODEL


def get_embedding_model():
    return HuggingFaceEmbedding(
        model_name=EMBEDDING_MODEL,
        trust_remote_code=True,
    )