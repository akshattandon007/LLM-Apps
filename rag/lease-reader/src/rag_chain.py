"""RAG chain: retrieve, generate, and attach caveats.

This module wires together the vector store, classifier, and Claude via
langchain-anthropic to produce answers with clause citations and caveats.
"""

import os
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.models import AnswerResponse, CitedClause, Chunk
from src.vector_store import get_store
from src.classifier import classify_query


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a lease-analysis assistant. You answer tenant questions
about their lease agreement in plain, clear English.

You ALWAYS follow these rules:

1. **Answer in plain English** — no legalese, no jargon. Assume the user is a
   tenant who may not be familiar with legal terms.

2. **Cite the exact clause** — tell the user which section of the lease supports
   your answer. Quote the relevant part.

3. **Include a caveat when needed** — you MUST add a caveat (marked **Caveat**)
   in the following situations:
   - The answer depends on state or city law (e.g., "Check your local tenant
     laws — state law may give you additional rights.")
   - The clauses are ambiguous or conflicting
   - The answer is not a definitive yes/no ("It depends on ...")
   - The lease is silent on the issue

4. **Format your answer clearly**:
   - **Answer:** [plain-English answer]
   - **Clause:** [section reference]
   - **Caveat:** [caveat if applicable, or omit this section]

Here are the relevant lease clauses the user's question touches on:

{context}"""


HUMAN_TEMPLATE = """Question: {question}

Answer the question based ONLY on the lease clauses provided above. If the
lease clauses don't cover the question, say so — don't make up terms."""


CAVEAT_RULES = [
    "If the answer depends on state or city law, add: 'Check your local tenant laws — state law may give you additional rights.'",
    "If clauses are ambiguous or conflicting, flag the ambiguity.",
    "If the answer is not a definitive yes/no, explain why it depends.",
    "If the lease is silent on the issue, say so clearly.",
]


# ---------------------------------------------------------------------------
# LLM setup
# ---------------------------------------------------------------------------

def _get_llm():
    """Get the Claude LLM instance. Uses ANTHROPIC_API_KEY from environment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Set it in your .env file or environment."
        )
    return ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0.2,
        max_tokens=2048,
        api_key=api_key,
    )


def _build_caveat_instruction(chunks: list[Chunk]) -> str:
    """Build a caveat-specific instruction based on the retrieved chunks."""
    instructions = []
    # Check if chunks reference external laws
    texts = " ".join(c.text.lower() for c in chunks)
    if any(kw in texts for kw in ["state law", "local law", "ordinance", "statute"]):
        instructions.append(
            "- The lease references external laws. Warn the user to check their "
            "local tenant laws."
        )
    if len(chunks) >= 3:
        # Multiple chunks may indicate complexity
        instructions.append(
            "- Multiple clauses apply. Check for consistency and flag any ambiguity."
        )
    return "\n".join(instructions)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def answer_question(question: str, top_k: int = 5) -> AnswerResponse:
    """Full RAG pipeline: classify -> retrieve -> generate -> answer with caveats.

    Args:
        question: The user's natural-language question.
        top_k: Number of chunks to retrieve per domain.

    Returns:
        An AnswerResponse with plain-English answer, cited clauses, and caveat.
    """
    # 1. Classify the query into a legal domain
    domain = classify_query(question)

    # 2. Retrieve from the vector store filtered by domain
    store = get_store()
    chunks = store.search(question, domain=domain, top_k=top_k)

    if not chunks:
        # Fallback: try GENERAL domain
        chunks = store.search(question, domain="GENERAL", top_k=top_k)

    if not chunks:
        return AnswerResponse(
            answer="No lease has been uploaded yet. Please upload a lease PDF first.",
            domain=domain,
            cited_clauses=[],
            caveat=None,
        )

    # 3. Build context from chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Clause {chunk.clause_ref} — Page {chunk.page_number}]\n{chunk.text}"
        )
    context = "\n\n".join(context_parts)

    # 4. Build the prompt
    caveat_instruction = _build_caveat_instruction(chunks)
    if caveat_instruction:
        user_prompt = (
            f"{HUMAN_TEMPLATE}\n\n"
            f"**Caveat checklist:**\n{caveat_instruction}"
        )
    else:
        user_prompt = HUMAN_TEMPLATE

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", user_prompt),
    ])

    # 5. Generate the answer
    llm = _get_llm()
    chain = prompt | llm | StrOutputParser()
    answer_text = chain.invoke({"context": context, "question": question})

    # 6. Extract cited clauses for the response
    cited = [
        CitedClause(
            clause_ref=c.clause_ref,
            text=c.text[:300] + ("..." if len(c.text) > 300 else ""),
            page_number=c.page_number,
        )
        for c in chunks[:3]  # top 3 citations
    ]

    # 7. Extract caveat from the answer
    caveat = None
    if "**Caveat**" in answer_text or "*Caveat*" in answer_text:
        # Find the caveat section
        import re
        m = re.search(r"\*{0,2}Caveat\*{0,2}:?\s*(.+?)(?:\n\n|\Z)", answer_text, re.DOTALL)
        if m:
            caveat = m.group(1).strip()
        else:
            caveat = "See caveat in the answer above."

    return AnswerResponse(
        answer=answer_text,
        domain=domain,
        cited_clauses=cited,
        caveat=caveat,
    )