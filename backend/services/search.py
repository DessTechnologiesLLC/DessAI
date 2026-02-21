# backend/services/search.py
from __future__ import annotations

import re
from typing import List

from sqlalchemy.orm import Session

from backend.models import Committee, Meeting, Document, DocumentChunk
from backend.schemas.search import SearchHit


def _make_snippet(text: str, query: str, window: int = 80) -> str:
    """
    Make a small snippet around the first occurrence of query.
    """
    t_lower = text.lower()
    q_lower = query.lower()
    idx = t_lower.find(q_lower)
    if idx == -1:
        return text[: 2 * window].replace("\n", " ")
    start = max(0, idx - window)
    end = min(len(text), idx + len(query) + window)
    snippet = text[start:end]
    return snippet.replace("\n", " ")


def _highlight_all(text: str, query: str) -> str:
    """
    Highlight all occurrences of query with Markdown **bold**.
    Case-insensitive.
    """
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    def repl(match: re.Match) -> str:
        return f"**{match.group(0)}**"

    return pattern.sub(repl, text)


def search_committee(
    db: Session,
    *,
    committee_external_id: str,
    query: str,
    meeting_external_id: str | None = None,
    doc_type: str | None = None,
    limit: int = 20,
) -> List[SearchHit]:
    """
    Keyword search over DocumentChunk.text tailored for board docs.

    - Filters by committee (mandatory)
    - Optional meeting and doc_type filters
    - Uses SQL ILIKE for initial candidate selection
    - For each chunk:
        * counts all occurrences of the query
        * builds a highlighted snippet
    - Returns one hit per chunk, not per occurrence (board-friendly)
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

    q = (
        db.query(DocumentChunk, Document, Meeting)
        .join(Document, DocumentChunk.document_id == Document.id)
        .outerjoin(Meeting, Document.meeting_id == Meeting.id)
        .filter(Document.committee_id == committee.id)
        .filter(DocumentChunk.text.ilike(f"%{query}%"))
    )

    if meeting_external_id:
        q = q.filter(Meeting.external_meeting_id == meeting_external_id)

    if doc_type:
        q = q.filter(Document.doc_type == doc_type)

    rows = q.limit(limit * 5).all()

    results: List[SearchHit] = []
    q_lower = query.lower()

    for chunk, doc, meeting in rows:
        text = chunk.text or ""
        t_lower = text.lower()

        occurrence_count = t_lower.count(q_lower)
        if occurrence_count <= 0:
            continue

        score = float(occurrence_count)

        snippet_raw = _make_snippet(text, query)
        snippet_marked = _highlight_all(snippet_raw, query)

        hit = SearchHit(
            chunk_id=chunk.id,
            document_id=doc.id,
            document_title=doc.original_file_name,
            meeting_name=meeting.name if meeting else None,
            doc_type=doc.doc_type,
            snippet=snippet_marked,
            score=score,
            occurrence_count=occurrence_count,
            ddm_url=None,
            file_path=doc.file_path if hasattr(doc, "file_path") else None,
            page_start=chunk.page_start if hasattr(chunk, "page_start") else None,
        )
        results.append(hit)

    results.sort(key=lambda h: h.score, reverse=True)
    return results[:limit]
