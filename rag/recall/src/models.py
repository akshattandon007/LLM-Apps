"""Pydantic models for Recall API."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Intent(str, Enum):
    DECISION = "DECISION"
    ACTION_ITEM = "ACTION_ITEM"
    OPINION = "OPINION"
    FACT = "FACT"
    FOLLOW_UP = "FOLLOW_UP"


class ChunkMetadata(BaseModel):
    """Metadata attached to each chunk stored in the vector index."""

    meeting_title: str = ""
    meeting_date: str = ""
    speaker: str = ""
    timestamp_start: str = ""
    timestamp_end: str = ""
    source_file: str = ""
    text: str = ""


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The user's question about the meeting")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")


class ChunkResult(BaseModel):
    """A single retrieved chunk shown in the debug / extended response."""

    speaker: str
    text: str
    timestamp: str
    meeting: str
    score: float
    intent: str


class AnswerResponse(BaseModel):
    answer: str
    intent: Intent
    sources: list[ChunkResult]


class IngestionResponse(BaseModel):
    status: str
    chunks_created: int
    meeting_title: str
    speakers: list[str]
    message: str


class UploadResponse(BaseModel):
    status: str
    filename: str
    file_path: str
    message: str


class UploadStatusResponse(BaseModel):
    ingested: list[dict]
    waiting: list[str]


class ErrorResponse(BaseModel):
    detail: str