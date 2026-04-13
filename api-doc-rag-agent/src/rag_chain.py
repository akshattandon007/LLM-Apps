"""
src/rag_chain.py
────────────────
Wires together the FAISS retriever and Claude LLM into a
Retrieval-Augmented Generation (RAG) chain with conversation memory.

Architecture:
  User query
      │
      ▼
  Retriever  ──→  Top-k relevant chunks
      │
      ▼
  Prompt builder  (system prompt + context + history + user query)
      │
      ▼
  Claude LLM  ──→  Grounded, natural-language answer
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.vectorstores import VectorStoreRetriever
from rich.console import Console

console = Console()

# ─── Default LLM settings ─────────────────────────────────────────────────────

DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.2   # low temp = more factual, less hallucination


# ─── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert technical documentation assistant specialising in API documentation.
Your role is to help developers and non-technical users understand API concepts, \
endpoints, parameters, authentication flows, and use cases.

GUIDELINES
──────────
• Answer ONLY based on the provided context (retrieved documentation chunks).
• If the context does not contain enough information to answer confidently, say so \
  clearly — do NOT hallucinate details.
• Translate technical jargon into plain English when the user's question appears \
  non-technical.
• Use concrete examples where helpful.
• Keep answers concise but complete; use bullet points or numbered steps for \
  multi-part answers.
• When referencing specific API endpoints, parameters, or code, format them as \
  inline code (e.g. `POST /messages`).
• Cite the source URL at the end of your answer when relevant.

CONTEXT (retrieved documentation)
──────────────────────────────────
{context}
"""


# ─── Chain builder ────────────────────────────────────────────────────────────

def build_rag_chain(
    retriever: VectorStoreRetriever,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
) -> "RAGAgent":
    """
    Build a stateful RAG agent wrapping Claude + FAISS retriever.

    Parameters
    ----------
    retriever   : LangChain VectorStoreRetriever.
    model       : Claude model identifier.
    max_tokens  : Max completion tokens for Claude.
    temperature : Sampling temperature (0.0–1.0).

    Returns
    -------
    RAGAgent instance ready for `.ask()` calls.
    """
    model_name = model or os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)
    tokens = max_tokens or int(os.getenv("MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))

    console.print(
        f"[bold cyan]⚙  Initialising Claude LLM:[/bold cyan] {model_name} "
        f"(max_tokens={tokens}, temperature={temperature})"
    )

    llm = ChatAnthropic(
        model=model_name,
        max_tokens=tokens,
        temperature=temperature,
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
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

    return RAGAgent(chain=chain, llm_name=model_name)


# ─── Stateful Agent wrapper ───────────────────────────────────────────────────

class RAGAgent:
    """
    Thin wrapper around the LangChain retrieval chain that manages
    conversation history across multiple turns.
    """

    def __init__(self, chain: Any, llm_name: str) -> None:
        self._chain = chain
        self.llm_name = llm_name
        self._history: List[BaseMessage] = []

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Submit a question and return a dict with:
            - answer  : str — the LLM's response
            - sources : list[str] — unique source URLs used
            - context : list[Document] — raw retrieved chunks
        """
        result = self._chain.invoke(
            {
                "input": question,
                "chat_history": list(self._history),  # snapshot — avoid reference mutation
            }
        )

        answer: str = result.get("answer", "")
        context_docs = result.get("context", [])
        sources = list(
            dict.fromkeys(
                doc.metadata.get("source", "unknown")
                for doc in context_docs
            )
        )

        # Update conversation history
        self._history.append(HumanMessage(content=question))
        self._history.append(AIMessage(content=answer))

        # Keep last 10 turns to avoid exceeding context window
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
