# backend/schemas/meetings.py
from datetime import date

from pydantic import BaseModel

from backend.schemas.base import ORMBase


class MeetingCreate(BaseModel):
    external_committee_id: str
    meeting_name: str
    meeting_date: date | None = None
    external_meeting_id: str | None = None


class MeetingRead(ORMBase):
    id: int
    name: str
    meeting_date: date | None = None
    external_meeting_id: str | None = None
