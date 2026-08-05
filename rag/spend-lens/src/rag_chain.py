"""
src/rag_chain.py
────────────────
Wires together the FAISS retriever and Claude LLM into a
RAG chain for personal finance questions.

Architecture:
  User query ("how much did I spend on coffee?")
      │
      ▼
  Retriever ──→ Top-k relevant transaction chunks
      │
      ▼
  Prompt builder (finance system prompt + context + history + query)
      │
      ▼
  Claude LLM ──→ Grounded answer with transaction citations
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from rich.console import Console

console = Console()

# ─── Default LLM settings ─────────────────────────────────────────────────────

DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.1   # very low temp for financial accuracy


# ─── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are SpendLens, a personal finance assistant with access to the user's \
bank and credit-card transaction data. Your job is to answer questions about \
their spending using ONLY the transaction data provided in the context below.

GUIDELINES
──────────
• Answer ONLY based on the provided transaction context. If the data does not \
  contain enough information to answer, say so clearly — do NOT invent or guess.
• ALWAYS cite specific transactions when making claims. Format citations as:
  `[Date: YYYY-MM-DD | Description | Amount]`
• When asked about totals or aggregates, calculate them from the data provided \
  and show your work (list the relevant transactions, then give the sum).
• Identify suspicious charges, forgotten subscriptions, or unusual spending \
  patterns when relevant.
• Use dollar amounts in $X.XX format.
• Be concise but thorough. Use bullet points for lists of transactions.
• If a category or merchant name is unclear from the data, note that uncertainty.
• Treat the user's financial data as confidential — do not repeat it outside \
  of answering their direct question.

CONTEXT (retrieved transactions)
─────────────────────────────────
{context}
"""


# ─── Chain builder ────────────────────────────────────────────────────────────


def build_rag_chain(
    retriever,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
) -> "SpendLensAgent":
    """Build a stateful RAG agent wrapping Claude + FAISS retriever.

    Parameters
    ----------
    retriever   : LangChain retriever (from vector_store.get_retriever).
    model       : Claude model identifier.
    max_tokens  : Max completion tokens for Claude.
    temperature : Sampling temperature (0.0–1.0).

    Returns
    -------
    SpendLensAgent instance ready for `.ask()` calls.
    """
    model_name = model or os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)
    tokens = max_tokens or int(os.getenv("MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))

    # Validate API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable is required. "
            "Set it in your .env file."
        )

    console.print(
        f"[bold cyan]⚙  Initialising Claude LLM:[/bold cyan] {model_name} "
        f"(max_tokens={tokens}, temperature={temperature})"
    )

    llm = ChatAnthropic(
        model=model_name,
        max_tokens=tokens,
        temperature=temperature,
        anthropic_api_key=api_key,
    )

    # Prompt template: system + chat history + human input
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # Chain: stuff retrieved docs → LLM
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    chain = create_retrieval_chain(retriever, question_answer_chain)

    console.print("[bold green]✔  RAG chain assembled.[/bold green]\n")

    return SpendLensAgent(chain=chain, llm_name=model_name)


# ─── Stateful Agent wrapper ───────────────────────────────────────────────────


class SpendLensAgent:
    """Thin wrapper around the LangChain retrieval chain that manages
    conversation history across multiple turns.
    """

    def __init__(self, chain: Any, llm_name: str) -> None:
        self._chain = chain
        self.llm_name = llm_name
        self._history: List[BaseMessage] = []

    def ask(self, question: str) -> Dict[str, Any]:
        """Submit a question and return a dict with:
            - answer  : str — the LLM's response
            - sources : list[dict] — metadata for each retrieved document
            - context : list[Document] — raw retrieved chunks
        """
        result = self._chain.invoke(
            {
                "input": question,
                "chat_history": list(self._history),
            }
        )

        answer: str = result.get("answer", "")
        context_docs = result.get("context", [])

        # Extract unique source metadata for citations
        sources = []
        seen = set()
        for doc in context_docs:
            meta = doc.metadata
            key = f"{meta.get('date', '')}|{meta.get('description', '')}|{meta.get('amount', '')}"
            if key not in seen:
                seen.add(key)
                sources.append(meta)

        # Update conversation history
        self._history.append(HumanMessage(content=question))
        self._history.append(AIMessage(content=answer))

        # Keep last 10 turns
        if len(self._history) > 20:
            self._history = self._history[-20:]

        return {"answer": answer, "sources": sources, "context": context_docs}

    def reset_history(self) -> None:
        """Clear conversation memory."""
        self._history = []
        console.print("[dim]Conversation history cleared.[/dim]")

    @property
    def turn_count(self) -> int:
        return len(self._history) // 2
