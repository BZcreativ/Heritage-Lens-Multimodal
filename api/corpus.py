"""Corpus statistics for /api/status — Qdrant point counts + filesystem PDFs.

Uses the same Qdrant URL convention as agent/retriever.py (localhost:6333 by
default; override with HL_QDRANT_URL, e.g. http://qdrant:6333 inside compose).
"""
from __future__ import annotations

import os
from pathlib import Path

QDRANT_URL = os.getenv("HL_QDRANT_URL", "http://localhost:6333")
TEXT_COLLECTION = os.getenv("HL_TEXT_COLLECTION", "heritage_lens_text")
IMAGE_COLLECTION = os.getenv("HL_IMAGE_COLLECTION", "heritage_lens_images")

WORKSPACE = Path(__file__).resolve().parent.parent  # repo root (api/ lives at root)
CORPUS_DIR = WORKSPACE / "data" / "corpus"


def _client():
    from qdrant_client import QdrantClient
    return QdrantClient(url=QDRANT_URL)


def text_chunk_count() -> int:
    try:
        return _client().get_collection(TEXT_COLLECTION).points_count or 0
    except Exception:
        return 0


def image_count() -> int:
    try:
        return _client().get_collection(IMAGE_COLLECTION).points_count or 0
    except Exception:
        return 0


def video_chunk_count() -> int:
    try:
        from qdrant_client.http.models import Filter, FieldCondition, MatchAny
        return _client().count(
            collection_name=TEXT_COLLECTION,
            count_filter=Filter(must=[FieldCondition(
                key="modality",
                match=MatchAny(any=["audio_transcript", "visual_caption", "ocr_text"]),
            )]),
        ).count or 0
    except Exception:
        return 0


def corpus_pdf_count() -> int:
    try:
        return len(list(CORPUS_DIR.glob("*.pdf"))) if CORPUS_DIR.is_dir() else 0
    except Exception:
        return 0


def qdrant_ok() -> bool:
    try:
        _client().get_collections()
        return True
    except Exception:
        return False


def gather_status() -> dict:
    return {
        "text_chunks": text_chunk_count(),
        "image_count": image_count(),
        "video_chunks": video_chunk_count(),
        "corpus_pdfs": corpus_pdf_count(),
        "qdrant_ok": qdrant_ok(),
    }


def list_source_payloads(limit: int = 10000) -> list[dict]:
    """Scroll the text collection and return each point's payload.

    Same scroll pattern as agent/retriever.py; the caller
    (parsing.dedup_corpus_sources) collapses these into per-source rows.
    """
    try:
        points, _ = _client().scroll(
            collection_name=TEXT_COLLECTION,
            with_payload=True,
            with_vectors=False,
            limit=limit,
        )
        return [p.payload or {} for p in points]
    except Exception:
        return []
