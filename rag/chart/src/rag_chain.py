"""RAG chain — retrieval + generation with temporal reasoning and privacy warning."""
from __future__ import annotations

import os
import re
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from src.models import Chunk, Citation, DocumentType, Intent, QueryResponse
from src.vector_store import VectorStore
from src.embedder import embed_query
from src.classifier import classify_intent


# ----- Prompt template for Claude -----

RAG_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a medical records assistant called Chart. You answer questions based on the user's uploaded medical record chunks.\n\n"
        "Rules:\n"
        "1. Answer in plain English using only the provided context.\n"
        "2. Include the specific document name and date for each fact you cite.\n"
        "3. If the information is not in the context, say 'I could not find this information in your records.'\n"
        "4. For temporal trend questions, compare values across dates and describe the change.\n"
        "5. Always end with: 'This answer is generated from your uploaded medical records and is not a substitute for professional medical advice.'\n\n"
        "Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    ),
])


# ----- Local fallback answer generator -----

def _fmt_val(v: dict[str, Any]) -> str:
    return f"{v.get('value', '')} {v.get('unit', '')}".strip()


def _extract_lab_value_from_text(text: str, lab_name: str) -> str | None:
    """Extract a specific lab value from chunk text using regex on the raw text.

    Handles formats like:
      'LDL Cholesterol         130 mg/dL'
      'Hemoglobin A1c (HbA1c)  5.7 %'
      'Vitamin D, 25-Hydroxy   22 ng/mL'
      'eGFR                    > 60 mL/min'
    """
    # Build a pattern that matches the lab name followed by optional text and a value
    # The value can be >, <, or a number, followed by a unit
    escaped = re.escape(lab_name)
    # Try exact match first (e.g., 'ldl' matches 'LDL Cholesterol')
    pat = re.compile(
        r"(?i)" + escaped + r".{0,50}?([><]?\s*\d+\.?\d*)\s*(mg/dL|ng/mL|pg/mL|mmol/L|%|g/dL|mEq/L|IU/L|U/L|mm3|cells/µL)",
        re.DOTALL,
    )
    m = pat.search(text)
    if m:
        return f"{m.group(1).strip()} {m.group(2)}".strip()
    return None


def _find_lab_value(chunks: list[Chunk], lab_name: str) -> str:
    """Search chunks for a specific lab value using text regex."""
    for chunk in chunks:
        val = _extract_lab_value_from_text(chunk.text, lab_name)
        if val:
            date = f" (date: {chunk.date_range})" if chunk.date_range else ""
            return f"{chunk.doc_name} — {lab_name}: {val}{date}"
    return ""


def _generate_local_answer(question: str, chunks: list[Chunk], intent: Intent) -> str:
    """Generate answer from retrieved chunks without an LLM."""
    q_lower = question.lower()

    if intent == Intent.VACCINATION or "tetanus" in q_lower or "shot" in q_lower:
        # Look for vaccination records
        for chunk in chunks:
            text_lower = chunk.text.lower()
            if "tetanus" in text_lower or "vaccine" in text_lower or "shot" in text_lower or "immunization" in text_lower:
                # Extract date
                date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", chunk.text)
                if date_match:
                    return f"Your tetanus shot was administered on {date_match.group(1)} (source: {chunk.doc_name})."
                # Try month format
                date_match = re.search(r"(?i)((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{4})", chunk.text)
                if date_match:
                    return f"Your tetanus shot was administered on {date_match.group(1)} (source: {chunk.doc_name})."
                date_match = re.search(r"(?i)((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4})", chunk.text)
                if date_match:
                    return f"Your tetanus shot was administered around {date_match.group(1)} (source: {chunk.doc_name})."
                return f"Your records indicate a tetanus shot was given (source: {chunk.doc_name})."

    if intent == Intent.LAB_VALUE:
        # Search for specific lab values
        lab_names = ["hba1c", "a1c", "ldl", "hdl", "cholesterol", "vitamin d", "glucose"]
        for lab in lab_names:
            if lab in q_lower:
                result = _find_lab_value(chunks, lab)
                if result:
                    return result

    if intent == Intent.TEMPORAL_TREND:
        # Compare values across dates
        lab_names = ["hba1c", "a1c", "ldl", "hdl", "cholesterol", "glucose", "vitamin d"]
        target_lab = ""
        for lab in lab_names:
            if lab in q_lower:
                target_lab = lab
                break

        if target_lab:
            values_by_date: list[tuple[str, str]] = []
            seen: set[tuple[str, str]] = set()
            for chunk in chunks:
                val = _extract_lab_value_from_text(chunk.text, target_lab)
                if val:
                    # Use date from chunk or from dates in the text
                    date_str = chunk.date_range or ""
                    key = (date_str, val)
                    if key not in seen:
                        seen.add(key)
                        values_by_date.append((date_str, val))
            if len(values_by_date) >= 2:
                lines = [f"  {d}: {v}" for d, v in sorted(values_by_date)]
                return f"Here is how your {target_lab} changed over time:\n" + "\n".join(lines)
            elif len(values_by_date) == 1:
                d, v = values_by_date[0]
                return f"Your {target_lab} was {v} on {d if d else 'the recorded date'}. Only one data point was found, so a trend cannot be determined."
            else:
                return f"I could not find values for {target_lab} in your records."

    if intent == Intent.MEDICATION_HISTORY:
        meds: set[str] = set()
        sources: set[str] = set()
        for chunk in chunks:
            for m in chunk.medications:
                meds.add(m)
            if chunk.doc_name:
                sources.add(chunk.doc_name)
        if meds:
            return f"Your records mention the following medications: {', '.join(sorted(meds))}. (source: {', '.join(sorted(sources))})"

    # Fallback: summarize the best chunk
    if chunks:
        best = chunks[0]
        snippet = best.text[:500]
        return f"Based on your records (source: {best.doc_name}):\n{snippet}\n\n(Note: This is a direct excerpt. For a more precise answer, set ANTHROPIC_API_KEY to use Claude.)"

    return "I could not find this information in your uploaded records."


def _format_context(chunks: list[Chunk]) -> str:
    """Format chunks into a context string for the LLM."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"[Document {i}: {chunk.doc_name} | Type: {chunk.doc_type.value} | "
            f"Section: {chunk.section} | Date: {chunk.date_range}]\n{chunk.text[:1500]}"
        )
    return "\n\n---\n\n".join(parts)


def _build_citations(chunks: list[Chunk]) -> list[Citation]:
    return [
        Citation(
            doc_name=c.doc_name,
            doc_type=c.doc_type,
            section=c.section,
            snippet=c.text[:300],
        )
        for c in chunks
    ]


def _compute_confidence(chunks: list[Chunk], scores: list[float]) -> str:
    if not chunks or not scores:
        return "LOW"
    avg_score = sum(scores) / len(scores)
    if avg_score > 0.6:
        return "HIGH"
    elif avg_score > 0.3:
        return "MEDIUM"
    return "LOW"


def _compute_date_range(chunks: list[Chunk]) -> str:
    dates: set[str] = set()
    for c in chunks:
        if c.date_range:
            for d in c.date_range.split(", "):
                dates.add(d)
    return ", ".join(sorted(dates)) if dates else ""


def answer_question(
    question: str,
    vector_store: VectorStore,
    top_k: int = 5,
    api_key: str = "",
) -> QueryResponse:
    """Run the full RAG pipeline: classify → retrieve → generate."""
    # 1. Classify intent
    intent = classify_intent(question)

    # 2. Retrieve
    query_emb = embed_query(question)
    results = vector_store.search(query_emb, top_k=top_k)
    if not results:
        return QueryResponse(
            question=question,
            answer="No documents have been ingested yet. Please upload medical records first.",
            intent=intent,
            confidence="LOW",
        )

    chunks = [r[0] for r in results]
    scores = [r[1] for r in results]
    citations = _build_citations(chunks)
    date_range = _compute_date_range(chunks)
    confidence = _compute_confidence(chunks, scores)

    # 3. Generate answer
    if api_key:
        try:
            llm = ChatAnthropic(api_key=api_key, model="claude-sonnet-4-20250514", temperature=0)
            context = _format_context(chunks)
            chain = (
                {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
                | RAG_PROMPT
                | llm
            )
            answer = chain.invoke({"context": context, "question": question}).content
        except Exception as e:
            answer = f"(Claude generation failed: {e}. Using local fallback.)\n\n"
            answer += _generate_local_answer(question, chunks, intent)
    else:
        answer = _generate_local_answer(question, chunks, intent)

    return QueryResponse(
        question=question,
        answer=answer,
        intent=intent,
        citations=citations,
        date_range=date_range,
        confidence=confidence,
    )