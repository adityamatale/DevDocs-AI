# rag/vector_store.py

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams
from llama_index.vector_stores.qdrant import QdrantVectorStore

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