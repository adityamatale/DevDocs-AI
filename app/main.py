from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="DevDocs AI",
    description="RAG-powered software documentation assistant",
    version="1.0.0",
)

app.include_router(router)