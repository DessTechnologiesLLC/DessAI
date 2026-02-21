# backend/schemas/documents.py
from pydantic import BaseModel

from backend.schemas.base import ORMBase


class DocumentCreate(BaseModel):
    external_committee_id: str
    external_meeting_id: str | None = None
    doc_type: str
    original_file_name: str
    file_extension: str
    file_path: str | None = None
    external_document_id: str | None = None


class DocumentRead(ORMBase):
    id: int
    doc_type: str
    original_file_name: str
    file_extension: str
    file_path: str
    external_document_id: str | None = None
