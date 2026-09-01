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
CACHE_IMAGES_DIR = WORKSPACE / "data" / "cache" / "images"


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


def distinct_source_count() -> int:
    """Number of distinct ingested sources — matches the Sources nav view.

    Derived from the same text-collection payloads as /api/sources, so the
    'N sources' badge can never disagree with the list the user sees.
    """
    names = {(p or {}).get("source_name") for p in list_source_payloads()}
    names.discard(None)
    names.discard("")
    return len(names)


def gather_status() -> dict:
    return {
        "text_chunks": text_chunk_count(),
        "image_count": image_count(),
        "video_chunks": video_chunk_count(),
        "corpus_pdfs": corpus_pdf_count(),
        "source_count": distinct_source_count(),
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


def _source_filter(source_name: str):
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue
    return Filter(must=[FieldCondition(key="source_name", match=MatchValue(value=source_name))])


def delete_source(source_name: str) -> dict:
    """Fully remove one source: its vectors (text + image collections), its
    uploaded file in data/corpus/, and its extracted images in data/cache/images/.

    Vectors are deleted first so a later filesystem error can't leave the live
    index pointing at files that are gone. Each step is best-effort: a missing
    collection counts as zero deletions rather than raising.
    """
    from qdrant_client.http.models import FilterSelector

    client = _client()
    flt = _source_filter(source_name)
    result = {
        "source_name": source_name,
        "text_points_deleted": 0,
        "image_points_deleted": 0,
        "cache_images_deleted": 0,
        "file_removed": False,
    }

    # Count points up front (delete-by-filter doesn't report how many it removed).
    try:
        result["text_points_deleted"] = client.count(
            collection_name=TEXT_COLLECTION, count_filter=flt
        ).count or 0
    except Exception:
        pass

    # Collect the on-disk extracted-image paths before the image points vanish.
    cache_image_paths: list[str] = []
    try:
        result["image_points_deleted"] = client.count(
            collection_name=IMAGE_COLLECTION, count_filter=flt
        ).count or 0
        offset = None
        while True:
            points, offset = client.scroll(
                collection_name=IMAGE_COLLECTION,
                scroll_filter=flt,
                with_payload=True,
                with_vectors=False,
                limit=256,
                offset=offset,
            )
            for p in points:
                path = (p.payload or {}).get("image_path")
                if path:
                    cache_image_paths.append(path)
            if offset is None:
                break
    except Exception:
        pass

    # Delete the vectors.
    for collection in (TEXT_COLLECTION, IMAGE_COLLECTION):
        try:
            client.delete(collection_name=collection, points_selector=FilterSelector(filter=flt))
        except Exception:
            pass

    # Delete extracted images, guarded to the cache dir.
    cache_root = CACHE_IMAGES_DIR.resolve()
    for path in cache_image_paths:
        try:
            resolved = Path(path).resolve()
        except Exception:
            continue
        if not str(resolved).startswith(str(cache_root)):
            continue
        try:
            if resolved.is_file():
                resolved.unlink()
                result["cache_images_deleted"] += 1
        except Exception:
            pass

    # Delete the uploaded corpus file, guarded to the corpus dir.
    corpus_root = CORPUS_DIR.resolve()
    try:
        dest = (CORPUS_DIR / source_name).resolve()
        if str(dest).startswith(str(corpus_root)) and dest.is_file():
            dest.unlink()
            result["file_removed"] = True
    except Exception:
        pass

    return result
