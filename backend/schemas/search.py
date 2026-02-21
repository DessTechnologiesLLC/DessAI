# backend/schemas/search.py
from pydantic import BaseModel


class SearchRequest(BaseModel):
    committee_external_id: str
    query: str
    meeting_external_id: str | None = None
    doc_type: str | None = None


class SearchHit(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    meeting_name: str | None = None
    doc_type: str
    snippet: str
    score: float
    occurrence_count: int
    ddm_url: str | None = None


class SearchResponse(BaseModel):
    results: list[SearchHit]
