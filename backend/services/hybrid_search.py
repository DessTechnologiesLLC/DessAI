# backend/services/hybrid_search.py
from __future__ import annotations

from typing import List, Dict

from sqlalchemy.orm import Session

from backend.schemas.search import SearchHit
from backend.services.search import search_committee as keyword_search_committee
from backend.services.semantic_search import semantic_search_committee
from backend.services.snippets import best_sentence_snippet   


def hybrid_search_committee(
    db: Session,
    *,
    committee_external_id: str,
    query: str,
    meeting_external_id: str | None = None,
    doc_type: str | None = None,
    top_k: int = 20,
) -> List[SearchHit]:
    """
    Hybrid search:
    - Runs keyword search and semantic search
    - Normalizes their scores
    - Combines into a single ranking using weighted sum.
    """

    query = query.strip()
    if not query:
        return []

    kw_hits = keyword_search_committee(
        db,
        committee_external_id=committee_external_id,
        query=query,
        meeting_external_id=meeting_external_id,
        doc_type=doc_type,
        limit=top_k * 2,
    )

    sem_hits = semantic_search_committee(
        db,
        committee_external_id=committee_external_id,
        query=query,
        meeting_external_id=meeting_external_id,
        doc_type=doc_type,
        top_k=top_k * 2,
    )

    if not kw_hits and not sem_hits:
        return []

    kw_by_chunk: Dict[int, SearchHit] = {h.chunk_id: h for h in kw_hits}
    sem_by_chunk: Dict[int, SearchHit] = {h.chunk_id: h for h in sem_hits}

    all_chunk_ids = set(kw_by_chunk.keys()) | set(sem_by_chunk.keys())

    max_kw = max((h.score for h in kw_hits), default=1.0)
    max_sem = max((h.score for h in sem_hits), default=1.0)

    if max_kw == 0:
        max_kw = 1.0
    if max_sem == 0:
        max_sem = 1.0

    w_sem = 0.6
    w_kw = 0.4

    combined: List[SearchHit] = []

    for cid in all_chunk_ids:
        kw = kw_by_chunk.get(cid)
        sem = sem_by_chunk.get(cid)

        kw_score_norm = (kw.score / max_kw) if kw else 0.0
        sem_score_norm = (sem.score / max_sem) if sem else 0.0

        final_score = w_sem * sem_score_norm + w_kw * kw_score_norm

        base = kw or sem   

       
        chunk_text = kw.snippet if kw else sem.snippet
        smart_snippet = best_sentence_snippet(chunk_text, query, final_score)

        hit = SearchHit(
            chunk_id=cid,
            document_id=base.document_id,
            document_title=base.document_title,
            meeting_name=base.meeting_name,
            doc_type=base.doc_type,
            snippet=smart_snippet,   
            score=final_score,
            occurrence_count=kw.occurrence_count if kw else 0,
            ddm_url=base.ddm_url,
            file_path=base.file_path if hasattr(base, "file_path") else None,
            page_start=base.page_start if hasattr(base, "page_start") else None,
            
        )
        combined.append(hit)

    combined.sort(key=lambda h: h.score, reverse=True)
    return combined[:top_k]
