# backend/core/security.py
from fastapi import Header, HTTPException
from backend.core.config import settings


def require_ddm_token(x_ddm_token: str | None = Header(default=None)):
    """
    Auth for DDM -> Smart Search sync calls.
    In dev, if DDM_SYNC_TOKEN isn't set, allow calls.
    In prod, require exact token match.
    """
    if not settings.ddm_sync_token:
        return True

    if not x_ddm_token or x_ddm_token != settings.ddm_sync_token:
        raise HTTPException(status_code=401, detail="Invalid DDM token")

    return True
