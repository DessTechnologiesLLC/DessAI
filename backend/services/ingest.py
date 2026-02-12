# backend/services/ingest.py
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from backend.models import Document, DocumentChunk
from backend.services.embeddings import embed_texts
from backend.services.vector_index import vector_index

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore

try:
    import docx  # python-docx
except ImportError:
    docx = None  # type: ignore



def _read_pdf_pages(path: Path) -> List[tuple[int, str]]:
    """
    Returns list of (page_number, text) using PyMuPDF.
    """
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is not installed")

    doc = fitz.open(path)
    pages: List[tuple[int, str]] = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        text = text.strip()
        if text:
            pages.append((i + 1, text))
    doc.close()
    return pages


def _read_docx_paragraphs(path: Path) -> List[str]:
    """
    Read DOCX paragraphs as a list of trimmed strings (empty removed).
    """
    if docx is None:
        raise RuntimeError("python-docx is not installed")

    d = docx.Document(str(path))
    paras = [p.text.strip() for p in d.paragraphs if p.text and p.text.strip()]
    return paras


def _read_txt_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")



def _chunk_long_text(text: str, max_chars: int = 1000) -> List[str]:
    """
    Simple text chunker: split on paragraphs/newlines and group into ~max_chars chunks.
    Used for TXT and PDF page text.
    """
    pieces: List[str] = []
    buf: List[str] = []
    current_len = 0

    for para in text.splitlines():
        para = para.strip()
        if not para:
            continue
        if current_len + len(para) + 1 > max_chars and buf:
            pieces.append("\n".join(buf))
            buf = [para]
            current_len = len(para)
        else:
            buf.append(para)
            current_len += len(para) + 1

    if buf:
        pieces.append("\n".join(buf))

    return pieces


def _looks_like_heading(para: str) -> bool:
    """
    Very simple heuristic for board-style headings:
    - short and ALL CAPS
    - or ends with ':' (section title)
    - or starts with a number / agenda item code like '1.' or '79/05'
    """
    p = para.strip()

    if not p:
        return False

    if len(p) <= 80 and p.isupper():
        return True

    if p.endswith(":"):
        return True

    first_token = p.split(" ", 1)[0]
    token = first_token.strip().rstrip(".")
    if token.isdigit():
        return True
    if "/" in token:
        left, _, right = token.partition("/")
        if left.isdigit() and right.replace("-", "").isdigit():
            return True

    return False


def _chunk_paragraphs(paragraphs: List[str], max_chars: int = 800) -> List[str]:
    """
    Chunk a list of paragraphs into ~max_chars chunks,
    keeping paragraph boundaries and using headings as natural split points.

    Ideal for board DOCX documents: each chunk ≈ one agenda item / section.
    """
    pieces: List[str] = []
    buf: List[str] = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        is_heading = _looks_like_heading(para)

        if is_heading and buf:
            pieces.append("\n".join(buf))
            buf = [para]
            current_len = len(para)
            continue

        if current_len + len(para) + 1 > max_chars and buf:
            pieces.append("\n".join(buf))
            buf = [para]
            current_len = len(para)
        else:
            buf.append(para)
            current_len += len(para) + 1

    if buf:
        pieces.append("\n".join(buf))

    return pieces



def ingest_document(db: Session, document: Document) -> None:
    """
    Read the document's file from disk, extract text, create DocumentChunk rows.

    - PDF: per page, further split into ~1200-char chunks.
    - DOCX/DOC: paragraph-aware chunking (~800 chars) with heading detection.
    - TXT: simple ~1000-char chunks.

    NOTE: This still only works for text-based PDFs, not scanned-image PDFs.
    OCR will be added separately.
    """
    path = Path(document.file_path)
    ext = document.file_extension.lower()

    logger.info("Ingesting document %s (%s)", document.id, path)

    db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()

    chunks: List[DocumentChunk] = []
    chunk_index = 0

    try:
        if ext == "pdf":
            if not path.exists():
                raise FileNotFoundError(path)
            pages = _read_pdf_pages(path)
            for page_no, page_text in pages:
                for piece in _chunk_long_text(page_text, max_chars=1200):
                    if not piece.strip():
                        continue
                    chunk = DocumentChunk(
                        document_id=document.id,
                        chunk_index=chunk_index,
                        text=piece,
                        page_start=page_no,
                        page_end=page_no,
                    )
                    chunks.append(chunk)
                    chunk_index += 1

        elif ext in ("docx", "doc"):
            if not path.exists():
                raise FileNotFoundError(path)
            paragraphs = _read_docx_paragraphs(path)
            for piece in _chunk_paragraphs(paragraphs, max_chars=800):
                if not piece.strip():
                    continue
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk_index,
                    text=piece,
                    page_start=None,
                    page_end=None,
                )
                chunks.append(chunk)
                chunk_index += 1

        elif ext in ("txt",):
            if not path.exists():
                raise FileNotFoundError(path)
            full_text = _read_txt_text(path)
            for piece in _chunk_long_text(full_text, max_chars=1000):
                if not piece.strip():
                    continue
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk_index,
                    text=piece,
                    page_start=None,
                    page_end=None,
                )
                chunks.append(chunk)
                chunk_index += 1

        else:
            logger.warning("Unsupported extension %s for document %s", ext, document.id)
            return

        for c in chunks:
            db.add(c)

        db.commit()
        logger.info("Ingested %d chunks for document %s", len(chunks), document.id)

        try:
            chunk_ids = [c.id for c in chunks]
            vector_index.add_chunks(db, chunk_ids, embed_texts)
            logger.info(
                "Added %d chunks to vector index for document %s",
                len(chunk_ids),
                document.id,
            )
        except Exception as e:
            logger.exception(
                "Error adding chunks to vector index for document %s: %s",
                document.id,
                e,
            )

    except Exception as e:
        db.rollback()
        logger.exception("Error ingesting document %s: %s", document.id, e)
