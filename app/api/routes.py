from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schema import QueryRequest, QueryResponse
from app.rag.generator import generate_answer, generate_answer_stream

import json


router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):

    try:
        answer, sources = generate_answer(request.query)

        return QueryResponse(
            answer=answer,
            sources=sources,
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate answer.",
        )


@router.post("/query/stream")
def query_stream(request: QueryRequest):

    def event_generator():
        try:
            for event in generate_answer_stream(request.query):
                yield f"data: {json.dumps(event)}\n\n"

            yield 'data: {"type":"done"}\n\n'

        except Exception:
            yield (
                'data: {"type":"error",'
                '"message":"Failed to generate answer."}\n\n'
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )