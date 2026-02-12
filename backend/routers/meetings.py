# backend/routers/meetings.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.models import Committee, Meeting
from backend.schemas.meetings import MeetingCreate, MeetingRead

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/", response_model=MeetingRead)
def create_meeting(payload: MeetingCreate, db: Session = Depends(get_db)):
    committee = (
        db.query(Committee)
        .filter(Committee.external_committee_id == payload.external_committee_id)
        .first()
    )
    if committee is None:
        raise HTTPException(status_code=404, detail="Committee not found")

    meeting = Meeting(
        committee_id=committee.id,
        name=payload.meeting_name,
        meeting_date=payload.meeting_date,
        external_meeting_id=payload.external_meeting_id,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("/", response_model=list[MeetingRead])
def list_meetings(
    committee_external_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    List meetings, optionally filtered by committee_external_id.
    """
    query = db.query(Meeting)

    if committee_external_id:
        query = (
            query.join(Committee, Committee.id == Meeting.committee_id)
            .filter(Committee.external_committee_id == committee_external_id)
        )

    meetings = query.order_by(Meeting.meeting_date.desc().nullslast()).all()
    return meetings
