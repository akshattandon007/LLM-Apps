"""Build and manage FAISS indices from chunk embeddings."""

import json
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

from .models import Chunk
from .embedder import Embedder


class IndexerError(Exception):
    """Raised when index operations fail."""


class Indexer:
    """Build, store, and load FAISS indices for per-ticker filing chunks.

    Production mode uses FAISS flat L2 index.
    Simulate mode stores metadata-only (no FAISS dependency).
    """

    def __init__(self, index_dir: Path, simulate: bool = False):
        self.index_dir = Path(index_dir)
        self.simulate = simulate
        self._faiss = None  # Lazy-imported

    def _ensure_index_dir(self) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------

    def build_index(
        self, chunks_with_embeddings: list[tuple[Chunk, list[float]]], ticker: str
    ) -> Path:
        """Build and persist a FAISS index for a ticker.

        Returns the index directory path.
        """
        self._ensure_index_dir()

        ticker_dir = self.index_dir / ticker.upper()
        ticker_dir.mkdir(parents=True, exist_ok=True)

        if self.simulate:
            return self._build_simulated(chunks_with_embeddings, ticker_dir)

        return self._build_faiss(chunks_with_embeddings, ticker_dir)

    def _build_faiss(
        self, chunks_with_embeddings: list[tuple[Chunk, list[float]]], ticker_dir: Path
    ) -> Path:
        """Build a real FAISS flat L2 index."""
        try:
            import faiss  # type: ignore
        except ImportError:
            raise IndexerError(
                "faiss is not installed. "
                "Install with: pip install mintdocs[full]  OR  "
                "pip install faiss-cpu sentence-transformers"
            )

        embeddings = np.array([e for _, e in chunks_with_embeddings]).astype(np.float32)
        dimension = embeddings.shape[1]

        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)

        faiss.write_index(index, str(ticker_dir / "index.faiss"))
        self._write_metadata(chunks_with_embeddings, ticker_dir)

        return ticker_dir

    def _build_simulated(
        self, chunks_with_embeddings: list[tuple[Chunk, list[float]]], ticker_dir: Path
    ) -> Path:
        """In simulated mode, write only metadata (no FAISS file needed)."""
        self._write_metadata(chunks_with_embeddings, ticker_dir)
        return ticker_dir

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _write_metadata(
        self, chunks_with_embeddings: list[tuple[Chunk, list[float]]], ticker_dir: Path
    ) -> None:
        """Write chunk metadata as JSON (embedding-free, for source retrieval)."""
        metadata = [
            {
                "section_header": chunk.section_header,
                "section_text": chunk.section_text,
                "company_name": chunk.metadata.company_name,
                "ticker": chunk.metadata.ticker,
                "cik": chunk.metadata.cik,
                "filing_type": chunk.metadata.filing_type,
                "filing_date": chunk.metadata.filing_date.isoformat(),
                "accession_number": chunk.metadata.accession_number,
                "primary_doc": chunk.metadata.primary_doc,
            }
            for chunk, _ in chunks_with_embeddings
        ]
        meta_path = ticker_dir / "metadata.json"
        meta_path.write_text(json.dumps(metadata, indent=2))

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_index(self, ticker: str) -> tuple["faiss.Index", list[Chunk]]:
        """Load a FAISS index and its metadata for a ticker.

        Returns (faiss_index, chunks).
        """
        import faiss  # type: ignore

        ticker_dir = self.index_dir / ticker.upper()
        if not ticker_dir.exists():
            raise IndexerError(f"No index found for ticker '{ticker}'")

        faiss_path = ticker_dir / "index.faiss"
        if not faiss_path.exists():
            raise IndexerError(
                f"FAISS index file not found at {faiss_path}. "
                "Try re-indexing without --simulate."
            )

        index = faiss.read_index(str(faiss_path))
        chunks = self._load_metadata(ticker_dir)
        return index, chunks

    def load_metadata(self, ticker: str) -> list[Chunk]:
        """Load metadata chunks for a ticker (no FAISS)."""
        ticker_dir = self.index_dir / ticker.upper()
        return self._load_metadata(ticker_dir)

    def _load_metadata(self, ticker_dir: Path) -> list[Chunk]:
        """Load chunk metadata from JSON."""
        meta_path = ticker_dir / "metadata.json"
        if not meta_path.exists():
            raise IndexerError(f"No metadata found at {meta_path}")

        data = json.loads(meta_path.read_text())
        return [Chunk.from_dict(d) for d in data]

    def list_indexed_tickers(self) -> list[str]:
        """Return list of tickers with stored indices."""
        if not self.index_dir.exists():
            return []
        return sorted(
            d.name
            for d in self.index_dir.iterdir()
            if d.is_dir() and (d / "metadata.json").exists()
        )

    def index_exists(self, ticker: str) -> bool:
        """Check if an index exists for a ticker."""
        return (self.index_dir / ticker.upper() / "metadata.json").exists()