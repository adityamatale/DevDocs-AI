# rag/retriever.py

from llama_index.core import VectorStoreIndex

from app.rag.vector_store import get_vector_store, get_qdrant_client
from app.rag.embeddings import get_embedding_model
from app.config import settings
from app.utils.logger import logger
from app.models import schema

from FlagEmbedding import FlagReranker


reranker = FlagReranker(
    settings.RERANK_MODEL,
    use_fp16=settings.DEVICE == "cuda",
)


def get_retriever(candidate_k: int = 5):

    client = get_qdrant_client()
    vector_store = get_vector_store(client)

    logger.info(f"embedding model loading ...")
    embed_model = get_embedding_model()
    logger.info(f"embedding model loaded ...")


    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model,
    )

    return index.as_retriever(
        similarity_top_k=candidate_k
    )


def retrieve(query: str, top_k: int = 5, candidate_k: int = 20):

    logger.info(f"get_retriver() started")
    retriever = get_retriever(candidate_k)
    logger.info(f"get_retriver() finished")

    nodes = retriever.retrieve(query)

    #### for source/language-aware deduplication
    # nodes = [
    #     node for node in nodes
    #     if "/en/" in node.metadata.get("file_path", "")
    # ]

    pairs = [
        [query, node.get_content()]
        for node in nodes
    ]

    scores = reranker.compute_score(
        pairs,
        normalize=True,
    )

    # logger.info(f"Reranker scores type: {type(scores)}")
    # logger.info(f"Reranker scores: {scores}")

    ranked_nodes = sorted(
        zip(nodes, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    # logger.info(f"top_k={top_k}, type={type(top_k)}")

    return [
        schema.RetrievalResult(node=node, score=score)
        for node, score in ranked_nodes[:top_k]
    ]

    # return ranked_nodes[:top_k]


if __name__ == "__main__":

    query = "How do I create a FastAPI application?"

    queries = [
        "How do I create a FastAPI application?",
        "How do I create a VectorStoreIndex in LlamaIndex?",
        "How does LlamaIndex handle document chunking?",
        "How can I use Qdrant with LlamaIndex?",
        "How do I install LlamaIndex?",
    ]

    # for query in queries:
    nodes = retrieve(query, top_k=settings.FINAL_TOP_K, candidate_k=settings.CANDIDATE_TOP_K)

    logger.info(f"\nQuery: {query}")
    logger.info(f"Retrieved: {len(nodes)} nodes\n")

    for i, node in enumerate(nodes, 1):
        logger.info(f"--- Result {i} ---")
        logger.info(f"Score: {node.score:.4f}")
        logger.info(f"Source: {node.metadata.get('file_path')}")
        logger.info(f"Content:\n{node.get_content()[:500]}")
        logger.info("")