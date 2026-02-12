# backend/routers/documents.py
from __future__ import annotations

from pathlib import Path
import shutil
import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.db.session import get_db
from backend.models import Committee, Meeting, Document
from backend.schemas.documents import DocumentRead
from backend.core.paths import (
    meeting_doc_folder,
    committee_circular_folder,
    committee_docs_root,
    sanitize_name,
)
from backend.services.ingest import ingest_document_langchain
from backend.core.auth import require_ddm_token

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger("documents")


@router.post("/upload", response_model=DocumentRead)
async def upload_document(
    # _auth: None = Depends(require_ddm_token),
    external_committee_id: str = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    external_meeting_id: str | None = Form(None),
    external_document_id: str | None = Form(None),
    company_external_id: str | None = Form(None),  
    db: Session = Depends(get_db),
):
    """
    DDM calls this endpoint when a document is uploaded.

    - Resolves committee & optional meeting
    - Chooses folder based on doc_type
    - Saves the file to that folder
    - Upserts Document row by external_document_id (if provided)
    - Runs ingestion (best-effort)
    """

    cleaned_external_document_id = (external_document_id or "").strip() or None
    logger.info(
        "DDM upload: committee=%s meeting=%s doc_type=%s external_document_id=%s filename=%s",
        external_committee_id,
        external_meeting_id,
        doc_type,
        cleaned_external_document_id,
        getattr(file, "filename", None),
    )

    try:
        committee = (
            db.query(Committee)
            .filter(Committee.external_committee_id == external_committee_id)
            .first()
        )
        if committee is None:
            raise HTTPException(status_code=404, detail="Committee not found")

        allowed = {"Agenda", "DraftMinutes", "FinalMinutes", "CircularResolution", "Extra1", "Extra2"}
        if doc_type not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid doc_type: {doc_type}")

        meeting = None
        if external_meeting_id:
            meeting = (
                db.query(Meeting)
                .filter(Meeting.external_meeting_id == external_meeting_id)
                .first()
            )
            if meeting is None:
                raise HTTPException(status_code=404, detail="Meeting not found")

        company = committee.company
        if company is None:
            raise HTTPException(status_code=500, detail="Committee has no linked company")
        
        company_key = company.external_company_id or company.name
        committee_key = committee.name
        meeting_key = (meeting.external_meeting_id or meeting.name) if meeting else ""

        if meeting:
            target_dir = meeting_doc_folder(
                company_key=company_key,
                committee_key=committee_key,
                meeting_key=meeting_key,
                doc_type=doc_type,
            )
        else:
            if doc_type == "CircularResolution":
                target_dir = committee_circular_folder(company_key, committee_key)
            else:
                target_dir = committee_docs_root(company_key, committee_key) / sanitize_name(doc_type)
                target_dir.mkdir(parents=True, exist_ok=True)

        original_file_name = file.filename or "upload.bin"
        file_extension = Path(original_file_name).suffix.lstrip(".").lower()

        safe_name = original_file_name.replace(" ", "_")
        if cleaned_external_document_id:
            safe_name = f"{cleaned_external_document_id}_{safe_name}"

        target_path = target_dir / safe_name

        with target_path.open("wb") as out_f:
            shutil.copyfileobj(file.file, out_f)
        try:
            await file.close()
        except Exception:
            pass
        if cleaned_external_document_id:
            existing = (
                db.query(Document)
                .filter(Document.external_document_id == cleaned_external_document_id)
                .first()
            )
            if existing:
                try:
                    old_path = Path(existing.file_path)
                    if old_path.exists():
                        old_path.unlink()
                except Exception:
                    pass

                db.delete(existing)
                db.commit()

        document = Document(
            committee_id=committee.id,
            meeting_id=meeting.id if meeting else None,
            doc_type=doc_type,
            original_file_name=original_file_name,
            file_extension=file_extension,
            file_path=str(target_path),
            external_document_id=cleaned_external_document_id,
        )

        try:
            db.add(document)
            db.commit()
            db.refresh(document)
        except IntegrityError:
            db.rollback()

            if cleaned_external_document_id:
                existing = (
                    db.query(Document)
                    .filter(Document.external_document_id == cleaned_external_document_id)
                    .first()
                )
                if not existing:
                    raise HTTPException(status_code=409, detail="Document already exists (integrity error)")

                try:
                    old = Path(existing.file_path)
                    if old.exists():
                        old.unlink()
                except Exception:
                    pass

                existing.committee_id = committee.id
                existing.meeting_id = meeting.id if meeting else None
                existing.doc_type = doc_type
                existing.original_file_name = original_file_name
                existing.file_extension = file_extension
                existing.file_path = str(target_path)

                db.add(existing)
                db.commit()
                db.refresh(existing)
                document = existing
            else:
                raise HTTPException(
                    status_code=409,
                    detail="Duplicate document constraint. Provide unique external_document_id.",
                )

        try:
            ingest_document_langchain(db, document)
        except Exception:
            traceback.print_exc()
            logger.exception("Ingest failed for document_id=%s file_path=%s", document.id, document.file_path)

        return document

    except HTTPException:
        raise

    except Exception:
        traceback.print_exc()
        logger.exception(
            "Upload failed: committee=%s meeting=%s doc_type=%s file=%s external_document_id=%s",
            external_committee_id,
            external_meeting_id,
            doc_type,
            getattr(file, "filename", None),
            cleaned_external_document_id,
        )
        raise HTTPException(status_code=500, detail=traceback.format_exc())