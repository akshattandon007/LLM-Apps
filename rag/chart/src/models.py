"""Pydantic models for the Chart RAG API."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    LAB_RESULT = "LAB_RESULT"
    DOCTOR_NOTE = "DOCTOR_NOTE"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    IMMUNIZATION = "IMMUNIZATION"
    OTHER = "OTHER"


class Intent(str, Enum):
    LAB_VALUE = "LAB_VALUE"
    MEDICATION_HISTORY = "MEDICATION_HISTORY"
    TEMPORAL_TREND = "TEMPORAL_TREND"
    VACCINATION = "VACCINATION"
    GENERAL_INFO = "GENERAL_INFO"


class Chunk(BaseModel):
    text: str
    doc_id: str
    doc_type: DocumentType = DocumentType.OTHER
    doc_name: str = ""
    date_range: str = ""
    medications: list[str] = Field(default_factory=list)
    labs: list[str] = Field(default_factory=list)
    values: list[dict[str, Any]] = Field(default_factory=list)
    section: str = ""


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class Citation(BaseModel):
    doc_name: str
    doc_type: DocumentType
    section: str
    snippet: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    intent: Intent
    citations: list[Citation] = Field(default_factory=list)
    date_range: str = ""
    confidence: str = ""  # HIGH, MEDIUM, LOW
    privacy_warning: str = "This answer is generated from your uploaded medical records. It is not a substitute for professional medical advice. Consult your healthcare provider for medical decisions."


class IngestRequest(BaseModel):
    file_path: str


class IngestResponse(BaseModel):
    doc_id: str
    doc_name: str
    doc_type: DocumentType
    chunk_count: int
    message: str


class HealthResponse(BaseModel):
    status: str
    documents_loaded: int
    chunks_indexed: int
    model_loaded: bool