# backend/routers/ddm_sync.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.security import require_ddm_token
from backend.core.paths import company_root, committee_root, meetings_root, committee_docs_root, committee_circular_folder
from backend.db.session import get_db
from backend.models import Company, Committee, Meeting
from datetime import date
from backend.core.paths import meeting_root, meeting_doc_folder

router = APIRouter(prefix="/ddm-sync", tags=["ddm-sync"])


class CompanyUpsertRequest(BaseModel):
    company_external_id: str
    company_name: str | None = None


@router.post("/company")
def upsert_company(
    payload: CompanyUpsertRequest,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_ddm_token),
):
    """
    Idempotent company upsert (DDM -> Smart Search):
    - Upsert by external_company_id
    - Ensure company folder exists in DATA_ROOT
    """
    ext_id = (payload.company_external_id or "").strip()
    if not ext_id:
        return {"status": "error", "detail": "company_external_id is required"}

    name = (payload.company_name or ext_id).strip()

    company = db.query(Company).filter(Company.external_company_id == ext_id).first()

    if company:
        if name and company.name != name:
            company.name = name
            db.commit()
            db.refresh(company)

        company_key = company.external_company_id or company.name
        company_root(company_key)

        return {
            "status": "updated",
            "id": company.id,
            "external_company_id": company.external_company_id,
            "name": company.name,
        }

    company = Company(name=name, external_company_id=ext_id)
    db.add(company)
    db.commit()
    db.refresh(company)

    company_key = company.external_company_id or company.name
    company_root(company_key)

    return {
        "status": "created",
        "id": company.id,
        "external_company_id": company.external_company_id,
        "name": company.name,
    }


class CommitteeUpsertRequest(BaseModel):
    company_external_id: str
    external_committee_id: str
    committee_name: str


@router.post("/committee")
def upsert_committee(
    payload: CommitteeUpsertRequest,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_ddm_token),
):
    """
    Idempotent committee upsert (DDM -> Smart Search):
    - company_external_id = DDM LCID
    - external_committee_id = DDM FolderId (committee folder)
    - committee_name stored EXACTLY (so UI matches DDM)
    - ensure filesystem structure exists
    """
    company_ext = (payload.company_external_id or "").strip()
    committee_ext = (payload.external_committee_id or "").strip()
    committee_name = (payload.committee_name or "").strip()

    if not company_ext or not committee_ext or not committee_name:
        return {"status": "error", "detail": "company_external_id, external_committee_id, committee_name are required"}

    company = db.query(Company).filter(Company.external_company_id == company_ext).first()
    if company is None:
        company = Company(name=company_ext, external_company_id=company_ext)
        db.add(company)
        db.commit()
        db.refresh(company)

    committee = db.query(Committee).filter(Committee.external_committee_id == committee_ext).first()

    if committee:
        changed = False
        if committee.name != committee_name:
            committee.name = committee_name
            changed = True
        if committee.company_id != company.id:
            committee.company_id = company.id
            changed = True

        if changed:
            db.commit()
            db.refresh(committee)

        company_key = company.external_company_id or company.name
        committee_key = committee.external_committee_id or committee.name

        committee_root(company_key, committee_key)
        meetings_root(company_key, committee_key)
        committee_docs_root(company_key, committee_key)
        committee_circular_folder(company_key, committee_key)

        return {
            "status": "updated",
            "id": committee.id,
            "external_committee_id": committee.external_committee_id,
            "name": committee.name,
            "company_external_id": company.external_company_id,
        }

    committee = Committee(
        name=committee_name,                 
        external_committee_id=committee_ext,
        company_id=company.id,
    )
    db.add(committee)
    db.commit()
    db.refresh(committee)

    # Ensure folders
    company_key = company.external_company_id or company.name
    committee_key = committee.external_committee_id or committee.name

    committee_root(company_key, committee_key)
    meetings_root(company_key, committee_key)
    committee_docs_root(company_key, committee_key)
    committee_circular_folder(company_key, committee_key)

    return {
        "status": "created",
        "id": committee.id,
        "external_committee_id": committee.external_committee_id,
        "name": committee.name,
        "company_external_id": company.external_company_id,
    }

class MeetingUpsertRequest(BaseModel):
    company_external_id: str
    external_committee_id: str
    external_meeting_id: str
    meeting_name: str
    meeting_date: date | None = None  

@router.post("/meeting")
def upsert_meeting(
    payload: MeetingUpsertRequest,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_ddm_token),
):
    """
    Idempotent meeting upsert:
    - company_external_id = DDM LCID
    - external_committee_id = DDM committee FolderId
    - external_meeting_id = DDM meeting FolderId (unique)
    - meeting_name must match DDM (dd/MM/yyyy as you store in FolderName)
    """
    company_ext = (payload.company_external_id or "").strip()
    committee_ext = (payload.external_committee_id or "").strip()
    meeting_ext = (payload.external_meeting_id or "").strip()
    meeting_name = (payload.meeting_name or "").strip()

    if not company_ext or not committee_ext or not meeting_ext or not meeting_name:
        return {"status": "error", "detail": "company_external_id, external_committee_id, external_meeting_id, meeting_name are required"}

    company = db.query(Company).filter(Company.external_company_id == company_ext).first()
    if company is None:
        company = Company(name=company_ext, external_company_id=company_ext)
        db.add(company)
        db.commit()
        db.refresh(company)

    committee = db.query(Committee).filter(Committee.external_committee_id == committee_ext).first()
    if committee is None:
        committee = Committee(name=committee_ext, external_committee_id=committee_ext, company_id=company.id)
        db.add(committee)
        db.commit()
        db.refresh(committee)
    else:
        if committee.company_id != company.id:
            committee.company_id = company.id
            db.commit()
            db.refresh(committee)

    meeting = db.query(Meeting).filter(Meeting.external_meeting_id == meeting_ext).first()

    if meeting:
        changed = False
        if meeting.name != meeting_name:
            meeting.name = meeting_name
            changed = True
        if meeting.meeting_date != payload.meeting_date:
            meeting.meeting_date = payload.meeting_date
            changed = True
        if meeting.committee_id != committee.id:
            meeting.committee_id = committee.id
            changed = True

        if changed:
            db.commit()
            db.refresh(meeting)

        company_key = company.external_company_id or company.name
        committee_key = committee.external_committee_id or committee.name
        meeting_key = meeting.external_meeting_id or meeting.name  # stable on disk

        meeting_root(company_key, committee_key, meeting_key)

        for dt in ["Agenda", "DraftMinutes", "FinalMinutes", "CircularResolution", "Extra1", "Extra2"]:
            meeting_doc_folder(company_key, committee_key, meeting_key, dt)

        return {
            "status": "updated",
            "id": meeting.id,
            "external_meeting_id": meeting.external_meeting_id,
            "name": meeting.name,
            "meeting_date": str(meeting.meeting_date) if meeting.meeting_date else None,
            "external_committee_id": committee.external_committee_id,
            "company_external_id": company.external_company_id,
        }

    meeting = Meeting(
        committee_id=committee.id,
        name=meeting_name,
        meeting_date=payload.meeting_date,
        external_meeting_id=meeting_ext,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    company_key = company.external_company_id or company.name
    committee_key = committee.external_committee_id or committee.name
    meeting_key = meeting.external_meeting_id or meeting.name

    meeting_root(company_key, committee_key, meeting_key)
    for dt in ["Agenda", "DraftMinutes", "FinalMinutes", "CircularResolution", "Extra1", "Extra2"]:
        meeting_doc_folder(company_key, committee_key, meeting_key, dt)

    return {
        "status": "created",
        "id": meeting.id,
        "external_meeting_id": meeting.external_meeting_id,
        "name": meeting.name,
        "meeting_date": str(meeting.meeting_date) if meeting.meeting_date else None,
        "external_committee_id": committee.external_committee_id,
        "company_external_id": company.external_company_id,
    }
