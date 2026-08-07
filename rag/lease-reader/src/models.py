"""Pydantic models for Lease Reader API requests/responses."""

from typing import Optional
from pydantic import BaseModel, Field


LEGAL_DOMAINS = [
    "RENT",
    "TERMINATION",
    "ACCESS",
    "MAINTENANCE",
    "PETS",
    "SUBLETTING",
    "DEPOSIT",
    "UTILITIES",
    "GENERAL",
]


class Chunk(BaseModel):
    text: str
    domain: str
    clause_ref: str
    page_number: int


class IngestResponse(BaseModel):
    status: str
    num_chunks: int
    domains_found: list[str]
    message: str


class QueryRequest(BaseModel):
    question: str = Field(
        min_length=1, max_length=2000,
        description="Natural-language question about the lease."
    )
    top_k: int = Field(default=5, ge=1, le=20)


class CitedClause(BaseModel):
    clause_ref: str
    text: str
    page_number: int


class AnswerResponse(BaseModel):
    answer: str
    domain: str
    cited_clauses: list[CitedClause]
    caveat: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None