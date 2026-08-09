"""LangChain retrieval chain for Recall.

Combines:
  1. Intent classification
  2. Speaker mention detection
  3. FAISS vector search
  4. Claude generation via langchain-anthropic
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from src.classifier import classify_intent, detect_speaker_mention
from src.embedder import embed_chunks
from src.vector_store import VectorStore
from src.models import Intent, AnswerResponse, ChunkResult

load_dotenv()


# ── Prompt templates ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Recall, an AI assistant that answers questions about meeting transcripts. You have access to retrieved chunks from the meeting transcript.

Each chunk has the format: [SPEAKER] utterance text, with metadata including speaker name, timestamp, and meeting title.

Your task is to answer the user's question based ONLY on the provided chunks. If the chunks don't contain enough information to answer, say so.

For each answer:
1. Give a clear, plain-English answer
2. Attribute statements to speakers
3. Include timestamps
4. Mention which meeting the information came from

Be concise but specific. If the user asks who said something or who disagreed, directly name the speaker."""

HUMAN_TEMPLATE = """Question: {question}

Intent: {intent}
{speaker_hint}

Retrieved chunks:
{context}

Answer the question based on these chunks:"""


def build_rag_chain(
    vector_store: VectorStore,
    model_name: str = "claude-sonnet-4-20250514",
    temperature: float = 0.0,
    api_key: Optional[str] = None,
) -> dict:
    """Build and return RAG components.

    Returns a dict with keys: 'retrieve', 'generate', 'classify', 'answer'
    so the API can compose them flexibly.
    """

    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Set it in .env or pass api_key."
        )

    llm = ChatAnthropic(
        model=model_name,
        temperature=temperature,
        anthropic_api_key=api_key,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_TEMPLATE),
    ])

    chain = prompt | llm

    def retrieve_fn(question: str, top_k: int = 5) -> list[ChunkResult]:
        """Retrieve top-k chunks, optionally filtered by intent or speaker."""
        intent = classify_intent(question)
        speaker_hint = detect_speaker_mention(question)

        # Embed the question
        query_emb = embed_chunks([question])

        # Search
        results = vector_store.search(query_emb, top_k=top_k)

        chunk_results = []
        for chunk, score in results:
            chunk_results.append(ChunkResult(
                speaker=chunk.metadata.get("speaker", "?"),
                text=chunk.metadata.get("text", chunk.text),
                timestamp=chunk.metadata.get("timestamp_start", ""),
                meeting=chunk.metadata.get("meeting_title", "Untitled"),
                score=score,
                intent=intent,
            ))

        return chunk_results

    def generate_answer(question: str, chunk_results: list[ChunkResult]) -> str:
        """Generate an answer from retrieved chunks."""
        speaker_hint = detect_speaker_mention(question)
        intent = classify_intent(question)

        context_lines = []
        for cr in chunk_results:
            context_lines.append(
                f"[{cr.speaker}] ({cr.timestamp}) [{cr.meeting}]: {cr.text}"
            )
        context_str = "\n".join(context_lines)

        speaker_hint_str = (
            f"Speaker mention detected: {speaker_hint} — focus on this speaker's contributions."
            if speaker_hint
            else ""
        )

        result = chain.invoke({
            "question": question,
            "intent": intent,
            "speaker_hint": speaker_hint_str,
            "context": context_str,
        })

        return result.content

    def answer(question: str, top_k: int = 5) -> AnswerResponse:
        """Full RAG pipeline: classify → retrieve → generate."""
        intent_str = classify_intent(question)
        intent = Intent(intent_str)

        chunk_results = retrieve_fn(question, top_k=top_k)
        answer_text = generate_answer(question, chunk_results)

        return AnswerResponse(
            answer=answer_text,
            intent=intent,
            sources=chunk_results,
        )

    return {
        "retrieve": retrieve_fn,
        "generate": generate_answer,
        "classify": classify_intent,
        "answer": answer,
    }