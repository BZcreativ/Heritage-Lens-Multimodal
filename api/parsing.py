"""Pure string→struct helpers for the API layer.

These mirror the parsing the Streamlit app does inline, but return structured
data for the React frontend. No DB, no network, no agent imports — so they are
trivially unit-testable.
"""
from __future__ import annotations

import os
from typing import Any

from pathlib import PurePosixPath, PureWindowsPath

from .models import (
    Confidence, CorpusSource, Epistemic, ImageItem, SourceItem, VideoChunk,
)

# The four canonical Layer-3 section headers emitted by agent/generator.py.
L3_TITLES = ["⚠️ SOURCE BIAS", "📄 ABSENCES", "🕵️ INTERPRETIVE LIMITS", "⚠️ CONFIDENCE"]

VIDEO_MODALITIES = {"audio_transcript", "visual_caption", "ocr_text"}

# Upload allow-list — mirrors ui/app.py ACCEPTED_TYPES (PDF · images · video).
ACCEPTED_UPLOAD_EXTS = {
    "pdf",
    "png", "jpg", "jpeg", "tiff", "bmp", "webp",
    "mp4", "mov", "avi", "mkv", "webm",
}


# ----------------------------------------------------------- layer 3 ----

def split_layer3(raw: str) -> dict[str, str]:
    """Split the Layer-3 transparency string into its four sections.

    Returns a dict keyed by the canonical title with the section body as value.
    Tolerates markdown bolding/heading prefixes the model sometimes adds.
    Mirrors the splitting logic in ui/app.py.
    """
    raw = (raw or "").strip()
    for title in L3_TITLES:
        raw = (raw
               .replace(f"**{title}**", title)
               .replace(f"### {title}", title)
               .replace(f"## {title}", title))

    sections: dict[str, str] = {t: "" for t in L3_TITLES}
    current: str | None = None
    buf: list[str] = []

    def flush():
        if current is not None:
            sections[current] = "\n".join(buf).strip()

    for line in raw.split("\n"):
        stripped = line.strip()
        found = next((t for t in L3_TITLES if stripped.startswith(t)), None)
        if found:
            flush()
            current = found
            buf = [stripped[len(found):].strip()]
        else:
            buf.append(line)
    flush()
    return sections


def confidence_from_text(text: str) -> Confidence:
    """Heuristic: derive a coarse confidence level + lit-segment count from prose.

    The model writes the CONFIDENCE section as free text; there is no numeric
    score upstream. We scan for obvious signals. Treat as indicative only.
    """
    t = (text or "").lower()
    level = "moderate"
    # order matters: check the strong signals first
    if any(k in t for k in ("very low", "no confidence", "cannot", "unable", "insufficient")):
        level = "low"
    elif "high" in t or "strong" in t or "robust" in t:
        level = "high"
    elif "low" in t or "weak" in t or "limited" in t:
        level = "low"
    elif "moderate" in t or "medium" in t or "partial" in t:
        level = "moderate"
    segments = {"low": 1, "moderate": 3, "high": 4}[level]
    return Confidence(level=level, segments=segments, note=(text or "").strip())


def build_epistemic(raw: str) -> Epistemic:
    s = split_layer3(raw)
    return Epistemic(
        source_bias=s["⚠️ SOURCE BIAS"],
        absences=s["📄 ABSENCES"],
        interpretive_limits=s["🕵️ INTERPRETIVE LIMITS"],
        confidence=confidence_from_text(s["⚠️ CONFIDENCE"]),
        raw=(raw or "").strip(),
    )


# ----------------------------------------------------------- sources ----

def _source_type(meta: dict[str, Any]) -> str:
    """Map a chunk's metadata to one of the frontend's three badge types."""
    if meta.get("modality") in VIDEO_MODALITIES or meta.get("media_type") == "video_frame":
        return "vid"
    mt = (meta.get("media_type") or "").lower()
    st = (meta.get("source_type") or "").lower()
    if "image" in mt or st in {"image", "photograph", "figure"}:
        return "img"
    return "pdf"


def _locator(meta: dict[str, Any]) -> str:
    if meta.get("start") is not None and meta.get("end") is not None:
        return f"{meta['start']}s – {meta['end']}s"
    page = meta.get("page_number")
    return f"p.{page}" if page not in (None, "", "Unknown") else ""


def build_sources(chunks: list[dict]) -> list[SourceItem]:
    """De-duplicate retrieved chunks by source_name into structured source rows.

    Keeps the highest-scoring representative of each source and records a count
    of contributing chunks.
    """
    best: dict[str, dict] = {}
    counts: dict[str, int] = {}
    for ch in chunks or []:
        meta = ch.get("metadata", {}) or {}
        name = meta.get("source_name") or "Unknown source"
        counts[name] = counts.get(name, 0) + 1
        score = ch.get("score") or 0.0
        if name not in best or score > (best[name].get("score") or 0.0):
            best[name] = {"meta": meta, "score": score}

    items: list[SourceItem] = []
    for i, (name, rec) in enumerate(
        sorted(best.items(), key=lambda kv: kv[1]["score"] or 0.0, reverse=True), start=1
    ):
        meta = rec["meta"]
        author = meta.get("author") or "Unknown"
        loc = _locator(meta)
        subtitle = author + (f" · {loc}" if loc else "")
        detail: dict[str, str] = {}
        if author and author != "Unknown":
            detail["Author"] = author
        for label, key in (
            ("Type", "source_type"), ("Institution", "institution"),
            ("Perspective", "cultural_perspective"), ("Language", "language_of_origin"),
            ("Modality", "modality"),
        ):
            v = meta.get(key)
            if v and v != "unknown":
                detail[label] = str(v)
        if loc:
            detail["Location"] = loc
        detail["Chunks used"] = str(counts[name])
        items.append(SourceItem(
            n=i, title=name, subtitle=subtitle, type=_source_type(meta), meta=detail,
        ))
    return items


# ----------------------------------------------------------- video ----

def build_video_chunks(chunks: list[dict], media_url_for, poster_url_for, limit: int = 6) -> list[VideoChunk]:
    """Map Qdrant video-derived chunks to frontend items.

    `media_url_for(meta) -> str | None` yields a playable URL (external http(s) or
    a local /api/media URL); `poster_url_for(video_id, start) -> str | None` yields
    a thumbnail URL from the extracted keyframes. Both injected by the API layer so
    this module stays filesystem-agnostic.
    """
    out: list[VideoChunk] = []
    for ch in chunks or []:
        meta = ch.get("metadata", {}) or {}
        modality = meta.get("modality")
        if modality not in VIDEO_MODALITIES:
            continue
        text = (ch.get("text") or "").replace("\n", " ").strip()
        if len(text) > 160:
            text = text[:160] + "…"
        start, end = meta.get("start"), meta.get("end")
        ts = f"{start}s – {end}s" if start is not None and end is not None else ""
        out.append(VideoChunk(
            modality=modality, timestamp=ts, start=start, end=end,
            caption=text, source_name=meta.get("source_name", ""),
            video_url=media_url_for(meta),
            poster_url=poster_url_for(meta.get("video_id"), start),
        ))
        if len(out) >= limit:
            break
    return out


# ----------------------------------------------------------- images ----

def build_images(image_hits: list[dict], url_builder) -> list[ImageItem]:
    """Map Qdrant image hits to frontend image items.

    `url_builder(path) -> str` turns an on-disk image path into an /api/images URL.
    Skips files that no longer exist on disk.
    """
    out: list[ImageItem] = []
    for hit in image_hits or []:
        path = hit.get("image_path")
        if not path or not os.path.exists(path):
            continue
        meta = hit.get("metadata", {}) or {}
        name = meta.get("source_name", "")
        page = str(meta.get("page_number", "") or "")
        cap = meta.get("caption") or (f"{name} · p.{page}" if page else name)
        out.append(ImageItem(
            url=url_builder(path), caption=cap, alt=cap or "Retrieved corpus image",
            source_name=name, page_number=page,
        ))
    return out


# ----------------------------------------------------------- corpus sources ----

def dedup_corpus_sources(payloads: list[dict]) -> list[CorpusSource]:
    """Collapse raw Qdrant text-point payloads into one row per source_name.

    Counts contributing chunks and keeps the first non-empty value seen for each
    metadata field. Sorted by chunk_count desc, then name, for a stable list.
    """
    rows: dict[str, dict] = {}
    for p in payloads or []:
        name = (p or {}).get("source_name")
        if not name:
            continue
        row = rows.setdefault(name, {"count": 0})
        row["count"] += 1
        for key in ("author", "source_type", "institution",
                    "cultural_perspective", "language_of_origin", "modality"):
            v = p.get(key)
            if v and v not in ("unknown", "Unknown") and not row.get(key):
                row[key] = str(v)

    items = [
        CorpusSource(
            source_name=name,
            author=r.get("author", "Unknown"),
            source_type=r.get("source_type", ""),
            institution=r.get("institution", ""),
            cultural_perspective=r.get("cultural_perspective", ""),
            language_of_origin=r.get("language_of_origin", ""),
            modality=r.get("modality", ""),
            chunk_count=r["count"],
        )
        for name, r in rows.items()
    ]
    items.sort(key=lambda s: (-s.chunk_count, s.source_name.lower()))
    return items


# ----------------------------------------------------------- upload names ----

def safe_corpus_filename(filename: str | None) -> str | None:
    """Return a safe basename for a corpus upload, or None if it must be rejected.

    Strips any path component (defends against traversal on both posix/windows
    separators) and enforces the ACCEPTED_UPLOAD_EXTS allow-list. Returns None for
    empty names, missing/disallowed extensions, or names that resolve to nothing.
    """
    if not filename:
        return None
    # Take the last path segment regardless of separator style in the upload name.
    base = PureWindowsPath(PurePosixPath(filename).name).name.strip()
    if not base or base in (".", ".."):
        return None
    ext = base.rsplit(".", 1)[-1].lower() if "." in base else ""
    if ext not in ACCEPTED_UPLOAD_EXTS:
        return None
    return base
