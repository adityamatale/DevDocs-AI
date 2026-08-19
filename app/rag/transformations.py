# rag/transformations.py

from llama_index.core.node_parser import SentenceSplitter

from app.utils.logger import logger
from app.config import settings


splitter = SentenceSplitter(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP,
)


def chunk_documents(documents):

    nodes = splitter.get_nodes_from_documents(documents)

    logger.info(f"Documents : {len(documents)}")
    logger.info(f"Chunks    : {len(nodes)}")

    return nodes


if __name__ == "__main__":
    from app.rag.loaders import load_documents
    import pprint

    documents = load_documents()

    nodes = chunk_documents(documents)
    logger.info(pprint.pp(nodes[0].model_dump()))

    logger.info("\nExample chunk:")
    logger.info("------------------")
    logger.info(nodes[0].text[:1000])

    logger.info("\nMetadata:")
    logger.info(nodes[0].metadata)
