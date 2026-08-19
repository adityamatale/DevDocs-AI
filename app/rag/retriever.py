# rag/retriever.py

from llama_index.core import VectorStoreIndex

from app.rag.vector_store import get_vector_store, get_qdrant_client
from app.rag.embeddings import get_embedding_model
from app.config import settings
from app.utils.logger import logger


def get_retriever(top_k: int = 5):

    client = get_qdrant_client()
    vector_store = get_vector_store(client)

    embed_model = get_embedding_model()

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model,
    )

    return index.as_retriever(
        similarity_top_k=top_k
    )


def retrieve(query: str, top_k: int = 5):

    retriever = get_retriever(top_k)
    nodes = retriever.retrieve(query)

    return nodes


if __name__ == "__main__":

    query = "How do I create a FastAPI application?"

    nodes = retrieve(query, top_k=settings.TOP_K_RETRIEVALS)

    logger.info(f"\nQuery: {query}")
    logger.info(f"Retrieved: {len(nodes)} nodes\n")

    for i, node in enumerate(nodes, 1):
        logger.info(f"--- Result {i} ---")
        logger.info(f"Score: {node.score:.4f}")
        logger.info(f"Source: {node.metadata.get('file_path')}")
        logger.info(f"Content:\n{node.get_content()[:500]}")
        logger.info("")