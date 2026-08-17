# config/settings.py
import os
from dotenv import load_dotenv
load_dotenv()


# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_DIMENSION = os.getenv("EMBEDDING_DIMENSION")


# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")


# Embedding / Vector Store
VECTOR_DISTANCE = os.getenv("VECTOR_DISTANCE")


# Chunking
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50