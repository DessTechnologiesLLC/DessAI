# backend/routers/semantic_search.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.search import SearchRequest, SearchResponse
from backend.services.semantic_search import semantic_search_committee

router = APIRouter(prefix="/semantic-search", tags=["semantic-search"])


@router.post("/", response_model=SearchResponse)
def semantic_search(req: SearchRequest, db: Session = Depends(get_db)):
    hits = semantic_search_committee(
        db,
        committee_external_id=req.committee_external_id,
        query=req.query,
        meeting_external_id=req.meeting_external_id,
        doc_type=req.doc_type,
    )
    return SearchResponse(results=hits)
