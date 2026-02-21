# backend/services/semantic_search.py
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from backend.models import Committee, Meeting, Document, DocumentChunk
from backend.schemas.search import SearchHit
from backend.services.embeddings import embed_texts
from backend.services.vector_index import vector_index


def semantic_search_committee(
    db: Session,
    *,
    committee_external_id: str,
    query: str,
    meeting_external_id: str | None = None,
    doc_type: str | None = None,
    top_k: int = 20,
) -> List[SearchHit]:
    """
    Semantic search over all DocumentChunk embeddings using FAISS.
    - Filters by committee (mandatory)
    - Optional meeting + doc_type filters
    - Uses sentence-transformer embeddings for query & chunks.
    - Returns chunks ranked by cosine similarity.
    """

    query = query.strip()
    if not query:
        return []

    committee = (
        db.query(Committee)
        .filter(Committee.external_committee_id == committee_external_id)
        .first()
    )
    if committee is None:
        return []

    if (not vector_index.is_built) or vector_index.index is None or vector_index.index.ntotal == 0:
        vector_index.rebuild_from_db(db, embed_texts)

    if vector_index.index is None or vector_index.index.ntotal == 0:
        return []

    q_vec = embed_texts([query])
    chunk_ids, scores = vector_index.search(q_vec[0], top_k=top_k * 3)

    if not chunk_ids:
        return []

    chunks = (
        db.query(DocumentChunk, Document, Meeting, Committee)
        .join(Document, DocumentChunk.document_id == Document.id)
        .outerjoin(Meeting, Document.meeting_id == Meeting.id)
        .join(Committee, Document.committee_id == Committee.id)
        .filter(DocumentChunk.id.in_(chunk_ids))
        .all()
    )

    score_map = {cid: s for cid, s in zip(chunk_ids, scores)}

    results: List[SearchHit] = []

    for chunk, doc, meeting, comm in chunks:
        if comm.id != committee.id:
            continue

        if meeting_external_id and (not meeting or meeting.external_meeting_id != meeting_external_id):
            continue

        if doc_type and doc.doc_type != doc_type:
            continue

        text = chunk.text or ""
        snippet = text[:300].replace("\n", " ")

        sim_score = float(score_map.get(chunk.id, 0.0))
        if sim_score <= 0:
            continue

        hit = SearchHit(
            chunk_id=chunk.id,
            document_id=doc.id,
            document_title=doc.original_file_name,
            meeting_name=meeting.name if meeting else None,
            doc_type=doc.doc_type,
            snippet=snippet,
            score=sim_score,
            occurrence_count=0,  
            ddm_url=None,
            file_path=doc.file_path if hasattr(doc, "file_path") else None,
            page_start=chunk.page_start if hasattr(chunk, "page_start") else None,
        )
        results.append(hit)

    results.sort(key=lambda h: h.score, reverse=True)
    return results[:top_k]
