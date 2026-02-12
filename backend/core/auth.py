# backend/core/auth.py
from fastapi import Header, HTTPException

from backend.core.config import settings


def require_ddm_token(x_ddm_token: str | None = Header(default=None, alias="X-DDM-TOKEN")) -> None:
    """
    Protect DDM sync endpoints (or /documents/upload) with a shared token.
    """
    expected = settings.ddm_sync_token

    if not expected:
        raise HTTPException(status_code=500, detail="DDM_SYNC_TOKEN not configured on server")

    if not x_ddm_token or x_ddm_token != expected:
        raise HTTPException(status_code=401, detail="Invalid X-DDM-TOKEN")
