# rag/ingestion.py

from qdrant_client import QdrantClient
from llama_index.core import StorageContext, VectorStoreIndex

from app.rag.vector_store import (
    get_qdrant_client, 
    create_collection, 
    get_vector_store
)

from app.rag.embeddings import get_embedding_model
from app.rag.transformations import chunk_documents
from app.rag.loaders import load_documents

from app.config import settings
from app.utils.logger import logger

import uuid


def generate_node_id(node) -> str:
    """
    Generate a deterministic ID from the node's source + content.
    The same chunk will always get the same ID.
    """
    source = node.metadata.get("file_path", "")
    content = node.get_content()

    raw = f"{source}:{content}"

    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def get_existing_ids(client: QdrantClient, node_ids: list[str], batch_size: int = 256,) -> set[str]:
    """
    Return node IDs that already exist in Qdrant.
    """
    existing = set()

    for start in range(0, len(node_ids), batch_size):
        batch_ids = node_ids[start:start + batch_size]

        points = client.retrieve(
            collection_name=settings.QDRANT_COLLECTION,
            ids=batch_ids,
            with_payload=False,
            with_vectors=False,
        )

        existing.update(point.id for point in points)

    return existing


def ingest_test():

    # 1. Load documents
    documents = load_documents()

    # 2. Take only one document
    documents = documents[:1]

    # 3. Chunk it
    nodes = chunk_documents(documents)

    # 4. Get embedding model
    embed_model = get_embedding_model()

    # 5. Get Qdrant
    client = get_qdrant_client()
    create_collection(client)

    vector_store = get_vector_store(client)

    # 6. Create storage context
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )

    # 7. Create index and insert nodes
    index = VectorStoreIndex(
        nodes=nodes,
        storage_context=storage_context,
        embed_model=embed_model,
    )

    logger.info(f"\nInserted {len(nodes)} nodes into Qdrant.")

    return index


def test_retrieval():

    client = get_qdrant_client()
    vector_store = get_vector_store(client)

    embed_model = get_embedding_model()

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model,
    )

    query_engine = index.as_query_engine(
        similarity_top_k=2
    )

    response = query_engine.query(
        "What is the LlamaIndex documentation about?"
    )

    logger.info("\nResponse:")
    logger.info(response)

    logger.info("\nSources:")
    for source_node in response.source_nodes:
        logger.info(
            f"- score={source_node.score:.4f}"
            f" | {source_node.node.metadata}"
        )


def ingest_documents(batch_size: int = 64):

    # 1. Load documents
    documents = load_documents()

    # 2. Chunk documents
    nodes = chunk_documents(documents)

    logger.info(f"Total chunks to ingest: {len(nodes)}")

    # Generate deterministic IDs
    for node in nodes:
        node.node_id = generate_node_id(node)

    # 3. Get embedding model
    embed_model = get_embedding_model()

    # 4. Get Qdrant
    client = get_qdrant_client()
    create_collection(client)

    # Check which nodes are already stored
    existing_ids = get_existing_ids(
        client,
        [node.node_id for node in nodes],
    )

    logger.info(f"Already in Qdrant: {len(existing_ids)} nodes")

    vector_store = get_vector_store(client)

    # 5. Create storage context
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )

    nodes = [
        node for node in nodes
        if node.node_id not in existing_ids
    ]

    logger.info(f"Remaining to ingest: {len(nodes)} nodes")

    # 6. Insert in batches
    total = len(nodes)

    for start in range(0, total, batch_size):

        batch = nodes[start:start + batch_size]
        end = min(start + batch_size, total)

        logger.info(
            f"Processing nodes {start}/{total} → {end}/{total}"
        )

        VectorStoreIndex(
            nodes=batch,
            storage_context=storage_context,
            embed_model=embed_model,
        )

        logger.info(
            f"Progress: {end}/{total} nodes processed"
        )

    logger.info(f"\nSuccessfully ingested {total} nodes into Qdrant.")


if __name__ == "__main__":
    # client = get_qdrant_client()
    # create_collection(client)
    # logger.info("\nCollections:")
    # for collection in client.get_collections().collections:
    #     logger.info(f"- {collection.name}")
    # ingest_test()
    # test_retrieval()
    ingest_documents()



