# backend/core/paths.py
import os
import re
from pathlib import Path

from backend.core.config import settings


def sanitize_name(name: str) -> str:
    """
    Sanitize names for filesystem use.
    - Lowercase
    - Replace spaces with underscores
    - Remove characters not alphanum, underscore, hyphen
    """
    name = name.strip().lower()
    name = name.replace(" ", "_")
    name = re.sub(r"[^a-z0-9_\-]+", "", name)
    if not name:
        name = "unnamed"
    return name


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def company_root(company_key: str) -> Path:
    root = Path(settings.data_root)
    return ensure_dir(root / sanitize_name(company_key))


def committee_root(company_key: str, committee_key: str) -> Path:
    return ensure_dir(company_root(company_key) / sanitize_name(committee_key))


def meetings_root(company_key: str, committee_key: str) -> Path:
    return ensure_dir(committee_root(company_key, committee_key) / "meetings")


def meeting_root(company_key: str, committee_key: str, meeting_key: str) -> Path:
    return ensure_dir(meetings_root(company_key, committee_key) / sanitize_name(meeting_key))


def meeting_doc_folder(
    company_key: str,
    committee_key: str,
    meeting_key: str,
    doc_type: str,
) -> Path:
    doc_type_map = {
        "Agenda": "agenda",
        "DraftMinutes": "draft_minutes",
        "FinalMinutes": "final_minutes",
        "CircularResolution": "circular_resolution",
        "Extra1": "extra1",
        "Extra2": "extra2",
    }
    folder_name = doc_type_map.get(doc_type, sanitize_name(doc_type))
    return ensure_dir(meeting_root(company_key, committee_key, meeting_key) / folder_name)


def committee_docs_root(company_key: str, committee_key: str) -> Path:
    return ensure_dir(committee_root(company_key, committee_key) / "committee_docs")


def committee_circular_folder(company_key: str, committee_key: str) -> Path:
    return ensure_dir(committee_docs_root(company_key, committee_key) / "circular_resolution")
