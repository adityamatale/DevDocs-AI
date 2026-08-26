from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.observability import telemetry
from app.rag.embeddings import get_embedding_model
from app.rag.retriever import reranker
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading embedding model...")
    get_embedding_model()
    logger.info("Embedding model loaded!")

    logger.info("Loading reranker...")
    _ = reranker
    logger.info("Reranker loaded!")

    logger.info("All RAG models loaded. API is ready.")

    yield


app = FastAPI(
    title="DevDocs AI",
    description="RAG-powered software documentation assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://0.0.0.0:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)