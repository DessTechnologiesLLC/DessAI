# backend/models/meeting.py
from datetime import date
from typing import TYPE_CHECKING


from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from .company import Company
    from .committee import Committee
    from .meeting import Meeting
    from .document import Document
    from .document_chunk import DocumentChunk

class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    committee_id: Mapped[int] = mapped_column(ForeignKey("committees.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    meeting_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    external_meeting_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    committee: Mapped["Committee"] = relationship("Committee", back_populates="meetings")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="meeting")
