"""Query engine: embed question, retrieve top-k, format answer."""

from pathlib import Path

from .models import Chunk, QueryResult
from .embedder import Embedder
from .indexer import Indexer


class QueryEngine:
    """Answer natural-language questions against a ticker's index.

    Flow:
      1. Embed the question text.
      2. Search FAISS for top-k nearest chunks.
      3. Format the result with source citations.
    """

    def __init__(
        self,
        index_dir: Path,
        simulate: bool = False,
        top_k: int = 5,
    ):
        self.index_dir = Path(index_dir)
        self.simulate = simulate
        self.top_k = top_k
        self._embedder = Embedder(simulate=simulate)
        self._indexer = Indexer(index_dir, simulate=simulate)

    # ------------------------------------------------------------------
    # Simulated query (no FAISS needed)
    # ------------------------------------------------------------------

    def _simulate_query(self, question: str, ticker: str) -> QueryResult:
        """Return a hardcoded but realistic-looking answer about SEC filings."""
        ticker_up = ticker.upper()

        # Fabricate some realistic source chunks for the demo
        chunks = [
            self._make_chunk(
                ticker_up,
                "Apple Inc.",
                "0000320193",
                "10-K",
                "2024-10-31",
                "Item 1A: Risk Factors",
                (
                    "The Company relies on a complex global supply chain network "
                    "concentrated in Asia, particularly China. Any disruption to "
                    "this supply chain, including trade disputes, natural disasters, "
                    "or public health crises, could materially impact the Company's "
                    "ability to manufacture products."
                ),
            ),
            self._make_chunk(
                ticker_up,
                "Apple Inc.",
                "0000320193",
                "10-K",
                "2024-10-31",
                "Item 1: Business",
                (
                    "The Company designs, manufactures, and markets smartphones, "
                    "personal computers, tablets, wearables, and accessories worldwide. "
                    "The Company operates through geographic segments: Americas, Europe, "
                    "Greater China, Japan, and Rest of Asia Pacific."
                ),
            ),
            self._make_chunk(
                ticker_up,
                "Apple Inc.",
                "0000320193",
                "10-Q",
                "2024-07-27",
                "Item 2: MD&A",
                (
                    "Revenue increased 5% year over year driven by strong Services "
                    "growth and iPhone sales in emerging markets. Supply chain "
                    "conditions have improved compared to the prior year period."
                ),
            ),
        ]

        # Build a context-aware answer based on the question keywords
        answer = self._build_simulated_answer(question, ticker_up, chunks)

        return QueryResult(answer=answer, sources=chunks)

    def _build_simulated_answer(
        self, question: str, ticker: str, chunks: list[Chunk]
    ) -> str:
        """Generate a context-aware simulated answer."""
        q_lower = question.lower()

        if "risk" in q_lower or "china" in q_lower or "supply chain" in q_lower:
            return (
                f"Based on {ticker}'s most recent 10-K filing, the Company identifies "
                f"its concentrated supply chain in Asia as a key risk factor. The Company "
                f"relies on a complex global supply chain network concentrated in China. "
                f"Trade disputes, natural disasters, or public health crises affecting "
                f"this region could materially impact manufacturing capabilities. "
                f"The Q2 2024 10-Q notes that supply chain conditions have improved "
                f"compared to the prior year period."
            )
        elif "revenue" in q_lower or "financial" in q_lower:
            return (
                f"Based on {ticker}'s filings, the Company reported total revenue of "
                f"$391.0 billion for fiscal year 2024, a 3% decrease from the prior year. "
                f"Products revenue declined 4% to $298.0 billion, while Services revenue "
                f"grew 6% to $93.0 billion. Gross margin improved to 44.1%. In the most "
                f"recent quarter, revenue was $94.8 billion with net income of $24.2 billion."
            )
        elif "competition" in q_lower or "market" in q_lower:
            return (
                f"Based on {ticker}'s filings, the Company faces intense competition "
                f"in all markets. The Company's common stock trades on Nasdaq. "
                f"As disclosed in the risk factors, failure to innovate could reduce "
                f"market share. The Company's geographic segments include Americas, "
                f"Europe, Greater China, Japan, and Rest of Asia Pacific."
            )
        else:
            return (
                f"Based on {ticker}'s SEC filings, the Company files annual 10-K "
                f"and quarterly 10-Q reports. Key sections include Item 1 (Business), "
                f"Item 1A (Risk Factors), Item 7 (MD&A), and Item 8 (Financial Statements). "
                f"For specific information, please ask about risk factors, revenue, "
                f"competition, or supply chain."
            )

    def _make_chunk(
        self,
        ticker: str,
        company: str,
        cik: str,
        filing_type: str,
        filing_date: str,
        section_header: str,
        text: str,
    ) -> Chunk:
        """Helper to build a Chunk for simulated mode."""
        from datetime import date
        from .models import FilingMetadata

        return Chunk(
            section_header=section_header,
            section_text=text,
            metadata=FilingMetadata(
                company_name=company,
                ticker=ticker,
                cik=cik,
                filing_type=filing_type,
                filing_date=date.fromisoformat(filing_date),
                accession_number="0000320193-24-000001",
                primary_doc=(
                    f"https://www.sec.gov/Archives/edgar/data/{cik}/"
                    f"000032019324000001/aapl-20240928.htm"
                ),
            ),
        )

    # ------------------------------------------------------------------
    # Production query
    # ------------------------------------------------------------------

    def _production_query(self, question: str, ticker: str) -> QueryResult:
        """Run a real FAISS + embedding query."""
        import numpy as np  # type: ignore
        import faiss  # type: ignore

        # Load index and chunks
        faiss_index, chunks = self._indexer.load_index(ticker)

        # Embed the question
        question_vector = self._embedder.embed_text(question)
        qv_array = np.array([question_vector]).astype(np.float32)

        # Search
        distances, indices = faiss_index.search(qv_array, self.top_k)

        # Collect results
        results: list[Chunk] = []
        for idx in indices[0]:
            if 0 <= idx < len(chunks):
                results.append(chunks[idx])

        # Format answer
        answer = self._format_answer(question, results)
        return QueryResult(answer=answer, sources=results)

    def _format_answer(self, question: str, chunks: list[Chunk]) -> str:
        """Build a concise summary from retrieved chunks."""
        if not chunks:
            return "No relevant sections found for your question."

        # Simple extractive summary: concatenate key info
        sources_seen: set[str] = set()
        facts: list[str] = []

        for chunk in chunks:
            key = (
                f"{chunk.metadata.company_name}|{chunk.metadata.filing_type}|"
                f"{chunk.metadata.filing_date}|{chunk.section_header}"
            )
            if key not in sources_seen:
                sources_seen.add(key)
            # Extract first sentence or key phrase
            text = chunk.section_text.strip()
            first_sentence = text.split(". ")[0] if ". " in text else text[:200]
            facts.append(first_sentence)

        if facts:
            return (
                "Based on the retrieved SEC filings:\n\n"
                + "\n".join(f"- {f}" for f in facts)
            )
        return "No relevant information found."

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query(self, question: str, ticker: str) -> QueryResult:
        """Ask a natural-language question about a company's SEC filings.

        In simulate mode (--simulate), returns hardcoded answers without
        requiring FAISS or sentence-transformers.
        """
        if self.simulate:
            return self._simulate_query(question, ticker)
        return self._production_query(question, ticker)