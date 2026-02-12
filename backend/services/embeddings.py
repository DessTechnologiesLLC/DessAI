# backend/services/embeddings.py
from __future__ import annotations

from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"  


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Encode a list of texts into L2-normalized embeddings (float32).
    """
    if not texts:
        return np.zeros((0, 384), dtype="float32")

    model = get_model()
    emb = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,  
    )
    return emb.astype("float32")
