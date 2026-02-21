# backend/models/committee.py
from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base

if TYPE_CHECKING:
    from .company import Company
    from .meeting import Meeting
    from .document import Document


class Committee(Base):
    __tablename__ = "committees"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_committee_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    company: Mapped[Company] = relationship("Company", back_populates="committees")
    meetings: Mapped[list[Meeting]] = relationship(
        "Meeting", back_populates="committee", cascade="all, delete-orphan"
    )
    documents: Mapped[list[Document]] = relationship(
        "Document", back_populates="committee"
    )
