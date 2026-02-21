# backend/models/document.py
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base
if TYPE_CHECKING:
    from .company import Company
    from .committee import Committee
    from .meeting import Meeting
    from .document import Document
    from .document_chunk import DocumentChunk

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    committee_id: Mapped[int] = mapped_column(ForeignKey("committees.id"))
    meeting_id: Mapped[int | None] = mapped_column(ForeignKey("meetings.id"), nullable=True)

    doc_type: Mapped[str] = mapped_column(String(100), nullable=False)

    original_file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(10), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    external_document_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    committee: Mapped["Committee"] = relationship("Committee", back_populates="documents")
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
