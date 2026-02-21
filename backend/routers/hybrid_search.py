# backend/routers/hybrid_search.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.search import SearchRequest, SearchResponse
from backend.services.hybrid_search import hybrid_search_committee

router = APIRouter(prefix="/hybrid-search", tags=["hybrid-search"])


@router.post("/", response_model=SearchResponse)
def hybrid_search(req: SearchRequest, db: Session = Depends(get_db)):
    hits = hybrid_search_committee(
        db,
        committee_external_id=req.committee_external_id,
        query=req.query,
        meeting_external_id=req.meeting_external_id,
        doc_type=req.doc_type,
    )
    return SearchResponse(results=hits)
