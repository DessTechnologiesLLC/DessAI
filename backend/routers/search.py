# backend/routers/search.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.search import SearchRequest, SearchResponse
from backend.services.search import search_committee

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
def search_documents(req: SearchRequest, db: Session = Depends(get_db)):
    hits = search_committee(
        db,
        committee_external_id=req.committee_external_id,
        query=req.query,
        meeting_external_id=req.meeting_external_id,
        doc_type=req.doc_type,
    )
    return SearchResponse(results=hits)
