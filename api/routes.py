"""API routes for Heritage Lens."""
from __future__ import annotations

import asyncio
import io
import time
import threading
import queue
from contextlib import redirect_stdout
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from . import parsing
from .corpus import WORKSPACE, gather_status
from .models import (
    SearchMeta, SearchRequest, SearchResult, StatusResponse,
)

router = APIRouter(prefix="/api")

# Directories the image route is allowed to serve from (traversal-guarded).
_ALLOWED_IMAGE_DIRS = [
    (WORKSPACE / "data" / "cache" / "images").resolve(),
    (WORKSPACE / "data" / "corpus").resolve(),
    (WORKSPACE / "ui" / "assets").resolve(),
]


# ----------------------------------------------------------- status ----

@router.get("/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    # Qdrant calls are blocking; run them off the event loop.
    data = await asyncio.to_thread(gather_status)
    return StatusResponse(**data)


@router.get("/health")
async def health() -> dict:
    return {"ok": True}


# ----------------------------------------------------------- search ----

def _image_url(path: str) -> str:
    return f"/api/images?path={quote(path)}"


def _run_search(query: str) -> SearchResult:
    """Blocking: call the existing pipeline and shape its output."""
    from agent.pipeline import run_pipeline  # imported lazily (heavy deps)

    t0 = time.perf_counter()
    payload = run_pipeline(query)
    elapsed = time.perf_counter() - t0

    chunks = payload.get("retrieved_chunks", []) or []
    images = payload.get("retrieved_images", []) or []

    sources = parsing.build_sources(chunks)
    video_chunks = parsing.build_video_chunks(chunks)
    image_items = parsing.build_images(images, _image_url)
    epistemic = parsing.build_epistemic(payload.get("layer_3_transparency", ""))

    answer = payload.get("layer_1_answer", "") or ""
    grounded = len(chunks) > 0 and not answer.lower().startswith("error")

    return SearchResult(
        query=query,
        answer=answer,
        answer_sources_raw=payload.get("layer_2_sources", "") or "",
        grounded=grounded,
        sources=sources,
        epistemic=epistemic,
        video_chunks=video_chunks,
        images=image_items,
        meta=SearchMeta(
            source_count=len(sources),
            video_count=len(video_chunks),
            image_count=len(image_items),
            elapsed_seconds=round(elapsed, 2),
            image_keyword=payload.get("layer_4_image_keyword"),
        ),
    )


@router.post("/search", response_model=SearchResult)
async def search(req: SearchRequest) -> SearchResult:
    query = (req.query or "").strip()
    if not query:
        raise HTTPException(status_code=422, detail="query must not be empty")
    try:
        return await asyncio.to_thread(_run_search, query)
    except Exception as e:  # surface pipeline errors as 500 with a message
        raise HTTPException(status_code=500, detail=f"pipeline error: {e}") from e


# ----------------------------------------------------------- ingest (SSE) ----

class _QueueWriter(io.TextIOBase):
    """Capture print() output line-by-line into a queue for SSE streaming."""
    def __init__(self, q: "queue.Queue[str]"):
        self._q = q
        self._buf = ""

    def write(self, s: str) -> int:
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line.strip():
                self._q.put(line.rstrip())
        return len(s)

    def flush(self) -> None:
        if self._buf.strip():
            self._q.put(self._buf.rstrip())
            self._buf = ""


@router.post("/ingest")
async def ingest(request: Request) -> EventSourceResponse:
    """Trigger a full vector-DB rebuild, streaming progress lines as SSE events.

    Events: {event: "progress", data: <line>} … then {event: "done"} or
    {event: "error", data: <msg>}.
    """
    q: "queue.Queue[str]" = queue.Queue()
    done = threading.Event()
    error: dict[str, str] = {}

    def worker():
        from agent.ingest import initialize_vector_db
        writer = _QueueWriter(q)
        try:
            with redirect_stdout(writer):
                initialize_vector_db()
            writer.flush()
        except Exception as e:  # noqa: BLE001 — report any failure to the client
            error["msg"] = str(e)
        finally:
            done.set()

    threading.Thread(target=worker, daemon=True).start()

    async def event_stream():
        yield {"event": "progress", "data": "Starting ingestion…"}
        while not (done.is_set() and q.empty()):
            if await request.is_disconnected():
                return
            try:
                line = q.get_nowait()
                yield {"event": "progress", "data": line}
            except queue.Empty:
                await asyncio.sleep(0.25)
        if error:
            yield {"event": "error", "data": error["msg"]}
        else:
            yield {"event": "done", "data": "Ingestion complete."}

    return EventSourceResponse(event_stream())


# ----------------------------------------------------------- images ----

@router.get("/images")
async def serve_image(path: str = Query(..., description="absolute or repo-relative image path")) -> FileResponse:
    """Serve an image file, restricted to the allow-listed directories."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (WORKSPACE / candidate)
    try:
        resolved = candidate.resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="bad path")

    if not any(str(resolved).startswith(str(base)) for base in _ALLOWED_IMAGE_DIRS):
        raise HTTPException(status_code=403, detail="path not allowed")
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(str(resolved))
