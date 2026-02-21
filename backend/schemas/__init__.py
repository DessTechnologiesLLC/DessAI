# backend/schemas/__init__.py
from backend.schemas.committees import CommitteeCreate, CommitteeRead
from backend.schemas.meetings import MeetingCreate, MeetingRead
from backend.schemas.documents import DocumentCreate, DocumentRead
from backend.schemas.search import SearchRequest, SearchResponse, SearchHit

__all__ = [
    "CommitteeCreate",
    "CommitteeRead",
    "MeetingCreate",
    "MeetingRead",
    "DocumentCreate",
    "DocumentRead",
    "SearchRequest",
    "SearchResponse",
    "SearchHit",
]
