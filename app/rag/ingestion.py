# rag/ingestion.py

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import StorageContext, VectorStoreIndex

from app.rag.embeddings import get_embedding_model
from app.rag.transformations import chunk_documents
from app.rag.loaders import load_documents

from app.config import settings
from app.utils.logger import logger


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)


def create_collection(client: QdrantClient) -> None:

    collections = client.get_collections().collections

    if settings.QDRANT_COLLECTION in [c.name for c in collections]:
        logger.info(f"Collection {settings.QDRANT_COLLECTION} already exists")
        return

    client.create_collection(
        collection_name=settings.QDRANT_COLLECTION,
        vectors_config=VectorParams(
            size=settings.EMBEDDING_DIMENSION,
            distance=settings.VECTOR_DISTANCE,
        ),
    )

    logger.info(f"Collection {settings.QDRANT_COLLECTION} created successfully")


def get_vector_store(client: QdrantClient):

    return QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_COLLECTION,
    )


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

    print("\nResponse:")
    print(response)

    print("\nSources:")
    for source_node in response.source_nodes:
        print(
            f"- score={source_node.score:.4f}"
            f" | {source_node.node.metadata}"
        )


def ingest_documents(batch_size: int = 64):

    # 1. Load documents
    documents = load_documents()

    # 2. Chunk documents
    nodes = chunk_documents(documents)

    logger.info(f"Total chunks to ingest: {len(nodes)}")

    # 3. Get embedding model
    embed_model = get_embedding_model()

    # 4. Get Qdrant
    client = get_qdrant_client()
    create_collection(client)

    vector_store = get_vector_store(client)

    # 5. Create storage context
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )

    # 6. Insert in batches
    total = len(nodes)

    for start in range(0, total, batch_size):

        batch = nodes[start:start + batch_size]

        VectorStoreIndex(
            nodes=batch,
            storage_context=storage_context,
            embed_model=embed_model,
        )

        end = min(start + batch_size, total)

        logger.info(
            f"Ingested {end}/{total} nodes"
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



