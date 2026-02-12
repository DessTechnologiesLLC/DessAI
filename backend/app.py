# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from backend.core.config import settings
from backend.db.session import engine
from backend.db.base import Base
from backend.routers import health, committees, meetings, documents, search, semantic_search, hybrid_search, ddm_sync

Base.metadata.create_all(bind=engine)
logger = logging.getLogger("smartsearch")
logging.basicConfig(level=logging.DEBUG)

app = FastAPI(title=settings.app_name, debug=(settings.app_env == "dev"))
logger.warning("DDM token loaded? %s", bool(settings.ddm_sync_token))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(committees.router)
app.include_router(meetings.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(semantic_search.router)
app.include_router(hybrid_search.router)
app.include_router(ddm_sync.router)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("UNHANDLED ERROR on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "path": request.url.path,
            "method": request.method,
        },
    )

