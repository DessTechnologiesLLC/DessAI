# backend/schemas/committees.py
from pydantic import BaseModel

from backend.schemas.base import ORMBase


class CommitteeCreate(BaseModel):
    company_external_id: str | None = None
    committee_name: str
    external_committee_id: str | None = None


class CommitteeRead(ORMBase):
    id: int
    name: str
    external_committee_id: str | None = None
