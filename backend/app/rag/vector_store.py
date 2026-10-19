"""ChromaDB Vector Store wrapper with fast offline embedding support for Project Atlas."""
import hashlib
import logging
import math
import re
from pathlib import Path
from typing import List, Optional
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.config import Settings as ChromaSettings

from backend.app.config import get_settings

logger = logging.getLogger("atlas.vector_store")
settings = get_settings()

_chroma_client: Optional[chromadb.ClientAPI] = None
COLLECTION_NAME = "market_reports"
EMBEDDING_DIM = 384


class LightweightDenseEmbeddingFunction(EmbeddingFunction[Documents]):
    """Self-contained, deterministic 384-dimensional dense embedding function.

    Provides fast, offline, zero-network embedding generation using token & character
    n-gram hashing with subword weights and L2 normalization.
    Ensures 100% reproducibility in any Linux/Windows/Docker environment without
    external network dependencies.
    """

    def __init__(self, dimension: int = EMBEDDING_DIM):
        self.dimension = dimension

    def name(self) -> str:
        return "lightweight_dense"

    def get_config(self) -> dict:
        return {"dimension": self.dimension}

    def _embed_single(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        cleaned = text.lower()
        # Extract word tokens and alphanumeric strings
        tokens = re.findall(r"\b\w+\b", cleaned)

        if not tokens:
            return vector

        # Token hashing with frequency weights
        for token in tokens:
            token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = token_hash % self.dimension
            sign = 1.0 if (token_hash >> 8) % 2 == 0 else -1.0
            vector[idx] += sign * 1.5

            # Sub-word 3-grams for typo & morphological matching
            if len(token) >= 3:
                for j in range(len(token) - 2):
                    sub = token[j : j + 3]
                    sub_hash = int(hashlib.md5(sub.encode("utf-8")).hexdigest(), 16)
                    sub_idx = sub_hash % self.dimension
                    sub_sign = 1.0 if (sub_hash >> 8) % 2 == 0 else -1.0
                    vector[sub_idx] += sub_sign * 0.35

        # L2-normalization to unit sphere
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 1e-9:
            vector = [round(v / norm, 6) for v in vector]
        return vector

    def __call__(self, input: Documents) -> Embeddings:
        return [self._embed_single(doc) for doc in input]


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or initialize singleton Chroma persistent client."""
    global _chroma_client
    if _chroma_client is None:
        persist_dir = Path(settings.chroma_persist_directory).resolve()
        persist_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing ChromaDB client at: {persist_dir}")
        _chroma_client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


_semantic_ef: Optional[EmbeddingFunction[Documents]] = None


def get_embedding_function() -> EmbeddingFunction[Documents]:
    """Return semantic transformer embedding function (all-MiniLM-L6-v2 via ONNX, 384 dim)."""
    global _semantic_ef
    if _semantic_ef is None:
        try:
            from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
            _semantic_ef = ONNXMiniLM_L6_V2()
            logger.info("Using ONNX all-MiniLM-L6-v2 semantic embedding model for vector store.")
        except Exception as exc:
            logger.warning(f"Could not initialize ONNXMiniLM_L6_V2 ({exc}). Using lightweight dense fallback.")
            _semantic_ef = LightweightDenseEmbeddingFunction(dimension=EMBEDDING_DIM)
    return _semantic_ef


def get_reports_collection():
    """Get or create the market_reports vector collection with cosine distance."""
    client = get_chroma_client()
    emb_fn = get_embedding_function()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=emb_fn,
        metadata={
            "description": "Project Atlas Market Research Reports",
            "hnsw:space": "cosine",
            "dimension": EMBEDDING_DIM,
        },
    )
