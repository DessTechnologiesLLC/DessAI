# backend/services/vector_index.py
from __future__ import annotations

from typing import List, Callable, Tuple

import faiss
import numpy as np
from sqlalchemy.orm import Session

from backend.models import DocumentChunk


EmbedFn = Callable[[List[str]], np.ndarray]


class VectorIndex:
    """
    Simple FAISS index over DocumentChunk embeddings.
    - Uses IndexFlatIP + L2-normalized vectors (cosine similarity).
    - Stores chunk.id as FAISS IDs (so we can map back).
    """

    def __init__(self) -> None:
        self.index: faiss.IndexIDMap | None = None
        self.dim: int | None = None
        self.is_built: bool = False

    def _ensure_index(self, dim: int) -> None:
        if self.index is None:
            base = faiss.IndexFlatIP(dim)
            self.index = faiss.IndexIDMap(base)
            self.dim = dim

    def reset(self) -> None:
        if self.index is not None:
            self.index.reset()
        self.index = None
        self.dim = None
        self.is_built = False

    def rebuild_from_db(self, db: Session, embed_fn: EmbedFn) -> None:
        """
        Build the index from scratch using all DocumentChunk rows.
        """
        chunks = db.query(DocumentChunk).all()
        texts = [c.text or "" for c in chunks]
        if not texts:
            self.reset()
            self.is_built = True
            return

        vectors = embed_fn(texts)
        ids = np.array([c.id for c in chunks], dtype="int64")

        self._ensure_index(vectors.shape[1])
        self.index.reset()
        self.index.add_with_ids(vectors, ids)
        self.is_built = True

    def add_chunks(self, db: Session, chunk_ids: List[int], embed_fn: EmbedFn) -> None:
        """
        Incrementally add a small set of new chunks into the index.
        """
        if not chunk_ids:
            return
        chunks = db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
        if not chunks:
            return

        texts = [c.text or "" for c in chunks]
        vectors = embed_fn(texts)
        ids = np.array([c.id for c in chunks], dtype="int64")

        self._ensure_index(vectors.shape[1])
        self.index.add_with_ids(vectors, ids)

    def search(self, query_vector: np.ndarray, top_k: int = 50) -> Tuple[List[int], List[float]]:
        """
        Search the index and return (chunk_ids, scores).
        """
        if self.index is None or self.index.ntotal == 0:
            return [], []

        if query_vector.ndim == 1:
            query_vector = query_vector[None, :]

        scores, ids = self.index.search(query_vector, top_k)
        return ids[0].tolist(), scores[0].tolist()


vector_index = VectorIndex()
