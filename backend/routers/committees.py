# backend/routers/committees.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.models import Company, Committee
from backend.schemas.committees import CommitteeCreate, CommitteeRead

router = APIRouter(prefix="/committees", tags=["committees"])


@router.post("/", response_model=CommitteeRead)
def create_committee(payload: CommitteeCreate, db: Session = Depends(get_db)):
    if payload.company_external_id:
        company = (
            db.query(Company)
            .filter(Company.external_company_id == payload.company_external_id)
            .first()
        )
        if company is None:
            company = Company(
                name=payload.company_external_id,
                external_company_id=payload.company_external_id,
            )
            db.add(company)
            db.flush()
    else:
        company = db.query(Company).first()
        if company is None:
            company = Company(name="Default Company", external_company_id=None)
            db.add(company)
            db.flush()

    committee = Committee(
        name=payload.committee_name,
        external_committee_id=payload.external_committee_id,
        company_id=company.id,
    )
    db.add(committee)
    db.commit()
    db.refresh(committee)

    return committee


@router.get("/", response_model=list[CommitteeRead])
def list_committees(db: Session = Depends(get_db)):
    """
    List all committees (for now we don't filter by company).
    Useful for dropdowns in the UI.
    """
    committees = db.query(Committee).all()
    return committees
