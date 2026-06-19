"""FastAPI app factory for Heritage Lens.

Run:  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

Ensures the repo root is importable so `agent.*` resolves the same way the
existing scripts expect (they sys.path-insert the repo root themselves, but we
also add it here for safety when launched via uvicorn).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make the repo root importable (api/ lives at the repo root).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import router

# Built React SPA (ui/frontend/dist). Served at "/" in production so one service
# (heritage-api on :8000) hosts both the API and the UI, same-origin — no nginx,
# no CORS. Absent in dev (Vite serves :5173 and proxies /api), so the mount is
# added only when the build exists.
_FRONTEND_DIST = _REPO_ROOT / "ui" / "frontend" / "dist"

# Comma-separated allow-list; default permissive for local dev (Vite on :5173).
_ALLOWED_ORIGINS = os.getenv(
    "HL_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
).split(",")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Heritage Lens API",
        version="1.0.0",
        description="REST wrapper around the Heritage Lens multimodal RAG pipeline.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _ALLOWED_ORIGINS if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    # Mount the SPA last so /api/* routes (registered above) take precedence.
    if _FRONTEND_DIST.is_dir():
        app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="spa")
    return app


app = create_app()
