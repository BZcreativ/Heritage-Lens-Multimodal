"""Pydantic response models — mirror the frontend's `SearchResult` interface.

Kept intentionally permissive (Optional / default) because the upstream LLM
output is best-effort and fields can be missing.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------- search ----

class SourceItem(BaseModel):
    n: int
    title: str                       # source_name
    subtitle: str = ""               # "Author · p.12"  /  "Author · 02:14–04:09"
    type: Literal["pdf", "img", "vid"] = "pdf"
    meta: dict[str, str] = Field(default_factory=dict)  # expandable key/value detail


class Confidence(BaseModel):
    level: Literal["low", "moderate", "high"] = "moderate"
    segments: int = 3                # how many of the 4 bar segments are lit
    note: str = ""                   # raw prose from the CONFIDENCE section


class Epistemic(BaseModel):
    source_bias: str = ""
    absences: str = ""
    interpretive_limits: str = ""
    confidence: Confidence = Field(default_factory=Confidence)
    raw: str = ""                    # full unparsed layer-3 string (fallback)


class VideoChunk(BaseModel):
    modality: Literal["audio_transcript", "visual_caption", "ocr_text"]
    timestamp: str = ""              # "120s – 249s"
    start: Optional[float] = None
    end: Optional[float] = None
    caption: str = ""                # chunk text (trimmed)
    source_name: str = ""
    video_url: Optional[str] = None  # seekable only if http(s)


class ImageItem(BaseModel):
    url: str                         # /api/images?path=...
    caption: str = ""
    alt: str = ""
    source_name: str = ""
    page_number: str = ""


class SearchMeta(BaseModel):
    source_count: int = 0
    video_count: int = 0
    image_count: int = 0
    elapsed_seconds: float = 0.0
    image_keyword: Optional[str] = None


class SearchResult(BaseModel):
    query: str
    answer: str = ""                 # layer_1, raw (with [BACKGROUND] markers inline)
    answer_sources_raw: str = ""     # layer_2 string, as-is (optional use)
    grounded: bool = True
    sources: list[SourceItem] = Field(default_factory=list)
    epistemic: Epistemic = Field(default_factory=Epistemic)
    video_chunks: list[VideoChunk] = Field(default_factory=list)
    images: list[ImageItem] = Field(default_factory=list)
    meta: SearchMeta = Field(default_factory=SearchMeta)


class SearchRequest(BaseModel):
    query: str


# ---------------------------------------------------------------- status ----

class StatusResponse(BaseModel):
    text_chunks: int = 0
    image_count: int = 0
    video_chunks: int = 0
    corpus_pdfs: int = 0
    qdrant_ok: bool = False
