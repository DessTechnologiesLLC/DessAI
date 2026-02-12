# backend/models/company.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from backend.db.base import Base
if TYPE_CHECKING:
    from .company import Company
    from .committee import Committee
    from .meeting import Meeting
    from .document import Document
    from .document_chunk import DocumentChunk

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_company_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    committees: Mapped[list["Committee"]] = relationship(
        "Committee", back_populates="company", cascade="all, delete-orphan"
    )
