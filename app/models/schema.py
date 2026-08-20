from pydantic import BaseModel, Field
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    node: object
    score: float


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]