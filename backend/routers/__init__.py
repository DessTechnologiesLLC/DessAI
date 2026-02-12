# backend/routers/__init__.py
from backend.routers import health, committees, meetings, documents, search, semantic_search, hybrid_search, ddm_sync

__all__ = ["health", "committees", "meetings", "documents", "search", "semantic_search", "hybrid_search", "ddm_sync"]
