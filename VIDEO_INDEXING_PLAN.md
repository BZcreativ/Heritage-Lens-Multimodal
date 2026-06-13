# Phase 1 Analysis — Video Indexing & Timestamped Search

## 1. Current Pipeline Mapping

### Ingestion
- **Text**: `agent/ingest.py` reads PDFs via `pypdf.PdfReader`, extracts text per page, injects hardcoded metadata (`METADATA_MAPPING`), then chunks with `SentenceSplitter(chunk_size=512, chunk_overlap=50)` via LlamaIndex.
- **Images**: `agent/image_ingest.py` extracts images from PDFs (>10KB), standalone image files, and video frames (via ffmpeg at N fps). All are embedded with **SigLIP 2** (`google/siglip2-base-patch16-224`, 768-dim) into `heritage_lens_images`.
- **Video (current)**: `index_video_frames()` extracts frames at 1 fps, embeds them as images with `media_type="video_frame"` and `timestamp_sec`. No transcription, no captioning, no OCR.

### Embedding Model
- **Text**: `HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")` → **384-dim** vectors.
- **Images**: `SiglipModel` → **768-dim** vectors.
- **These are NOT in the same vector space** — text and images are stored in separate Qdrant collections.

### Qdrant Collections
| Collection | Vector Size | Distance | Content |
|------------|-------------|----------|---------|
| `heritage_lens_text` | 384 | COSINE | PDF text chunks |
| `heritage_lens_images` | 768 | COSINE | PDF images, uploaded images, video frames |

### Retrieval (`agent/retriever.py`)
- `retrieve_chunks()` queries `heritage_lens_text` via LlamaIndex `VectorStoreIndex`. Returns `text`, `metadata`, `score`. Supports balanced retrieval across sources.
- `retrieve_images()` queries `heritage_lens_images` using SigLIP text embedding of the query. Supports `source_filter` and `media_type` filters.

### Generation (`agent/generator.py`)
- Calls OpenAI GPT-4o with a system prompt.
- **Layer 2** reads metadata: `source_name`, `author`, `page_number`, `source_type`, `institution`, `cultural_perspective`.
- **Layer 3** reads metadata aggregates: counts of `source_type`, `institution`, `cultural_perspective`.
- Custom hardcoded knowledge for the two known PDFs is injected.

### Judge (`agent/judge.py`)
- Separate GPT-4o call evaluating Layer 3 specificity.
- Returns `is_valid` + `feedback` for regeneration loop.

### UI (`ui/app.py`)
- Streamlit 3-panel layout: Answer / Sources / Epistemic Transparency.
- Sidebar allows upload of PDFs, images, and videos.
- Shows image gallery with `source_name` + `page_number`.
- Videos uploaded to `data/corpus/` are re-indexed via `initialize_vector_db()` (which calls `index_video_frames`), but this is frame-only.

### Metadata Schema (current text payload)
```json
{
  "source_name": "filename.pdf",
  "source_type": "thesis | book | ...",
  "institution": "...",
  "cultural_perspective": "western_academic | ...",
  "language_of_origin": "italian",
  "author": "...",
  "page_number": "12"
}
```

### Metadata Schema (current image payload)
```json
{
  "source_name": "...",
  "page_number": 0,
  "media_type": "pdf_image | uploaded_image | video_frame",
  "image_path": "...",
  "video_id": "...",
  "timestamp_sec": 42
}
```

---

## 2. Key Findings & Constraints

1. **Video is already partially supported** — frames are extracted and indexed as images, but there is **no audio transcription, no scene captioning, and no OCR**.
2. **Text and images are in separate vector spaces** (384 vs 768). The user's request says "Embed transcript + caption + OCR chunks with the SAME embedder the text pipeline uses, into the SAME Qdrant collection." This is the correct approach — we must **not** use SigLIP for video-derived text. We must use `all-MiniLM-L6-v2` → 384-dim → `heritage_lens_text`.
3. **The generator expects `page_number` for citations**. For video chunks, we should map `start`/`end` seconds into a human-readable timestamp field, but keep `page_number` absent or use it for a fallback. The generator's prompt says "You MUST securely cite the specific 'Page' provided" — for video, we need to adapt the prompt to also cite `timestamp` when `modality` is video-derived.
4. **Layer 3 currently analyzes `source_type`, `institution`, `cultural_perspective`**. Adding `modality` as a new metadata field will let Layer 3 distinguish "narrated, not visually confirmed" — this is a provenance signal. We need to add `modality` to the metadata analysis and the system prompt.
5. **No vision captioning model is currently wired in**. The project has SigLIP for embedding, but not for generating captions. The simplest and most consistent approach is to use the **existing OpenAI GPT-4o client** (already used for synthesis) for frame captioning, since it has vision capabilities. Alternatively, we can use a local VLM if desired. I will note this as a decision point.

---

## 3. Implementation Plan

### Phase A — Audio Transcription Path (Ship First)
**Goal**: Ingest a video, transcribe audio, chunk segments with timestamps, embed into `heritage_lens_text`, verify end-to-end query returns correct timestamp.

1. **Dependencies** (ask before installing):
   - `faster-whisper` ( lighter than WhisperX, still has segment-level timestamps, handles multilingual audio well). Alternative: `whisperx` if word-level alignment is needed.
   - `ffmpeg-python` is already in requirements.txt.

2. **New module: `agent/video_ingest.py`**
   - `extract_audio(video_path) -> audio_path` using ffmpeg.
   - `transcribe_audio(audio_path, model="large-v3") -> segments` using faster-whisper.
   - `chunk_transcript_segments(segments, video_id, video_url, source_name) -> list[dict]` where each chunk has:
     - `text`: segment text
     - `metadata`: `source_name`, `source_type="video"`, `institution="unknown"`, `cultural_perspective="unknown"`, `language_of_origin=detected_lang`, `modality="audio_transcript"`, `video_id`, `video_url`, `start`, `end`
   - `embed_and_upsert_chunks(chunks, qdrant_client)` using `HuggingFaceEmbedding("all-MiniLM-L6-v2")` → 384-dim vectors into `heritage_lens_text`.

3. **Update `agent/ingest.py`**:
   - In `initialize_vector_db()`, after PDF indexing, detect video files in `data/corpus/` and call `agent/video_ingest.index_video(video_path, qdrant_client)` for each.
   - Keep existing frame indexing from `image_ingest` as-is (it runs in parallel and feeds the image collection).

4. **Update `agent/generator.py`**:
   - Extend `analyze_metadata()` to count `modality` types.
   - In the context formatting loop, if `start` and `end` are present (video chunk), format as `Timestamp: {start}s – {end}s` instead of `Page: ...`.
   - Add `modality` to the metadata fields shown in the prompt.
   - Update the Layer 3 prompt to mention that `modality` counts should be analyzed (e.g., "narrated, not visually confirmed").

5. **Update `agent/retriever.py`**:
   - No structural changes needed — metadata already flows through. Optionally add a `modality_filter` parameter for future use.

6. **Update `ui/app.py`**:
   - In the image gallery section, also check for video-derived chunks in `retrieved_chunks`. If a chunk has `start`/`end`, show a timestamp badge and a "seek to {start}s" link/button.
   - The sidebar corpus status already shows image count; add a count for video chunks (query Qdrant `heritage_lens_text` with `modality` filter).

7. **Test script: `tests/test_video_ingest.py`**
   - Ingest a small sample video (or create a synthetic one with ffmpeg).
   - Query a known phrase.
   - Assert the returned chunk has the correct `start`, `end`, `modality="audio_transcript"`, and `source_name`.

### Phase B — Visual Scene Captions + OCR (After Phase A is verified)
**Goal**: Add scene-based captions and OCR text as additional chunks in the same collection.

1. **Dependencies** (ask before installing):
   - `scenedetect` (PySceneDetect) for scene splitting.
   - `pytesseract` is already in requirements.txt for OCR.

2. **Extend `agent/video_ingest.py`**:
   - `detect_scenes(video_path) -> list[(start_sec, end_sec)]` using PySceneDetect.
   - `extract_frame_at(video_path, timestamp_sec) -> image_path`.
   - `caption_frame(image_path) -> caption` using GPT-4o vision (reuses existing OpenAI client) or a local VLM.
   - `ocr_frame(image_path) -> text` using pytesseract.
   - Create chunks for each scene:
     - `modality="visual_caption"` with the caption text
     - `modality="ocr_text"` with the OCR text
   - Both carry `start`, `end`, `video_id`, `video_url`, `source_name`.
   - Embed and upsert into `heritage_lens_text` with the same `all-MiniLM-L6-v2` embedder.

3. **Update `generator.py`**:
   - Ensure `modality="visual_caption"` and `modality="ocr_text"` are handled in metadata display.
   - Layer 3 prompt should now analyze all three modalities: audio vs visual vs OCR provenance.

4. **Update `ui/app.py`**:
   - Show scene thumbnails alongside captions in the gallery.
   - Timestamp badges for all video-derived results.

### Phase C — Retrieval & UI Polish
1. **Deep-link / seek support**:
   - If the UI is running in a browser context, generate `<a href="#t={start}">` style links for video results. Streamlit can't directly seek a video player, but we can show the timestamp and offer a copy-to-clipboard or display a small video player with `start` parameter if the video file is accessible via URL.
   - Since the user said "video file is stored in object storage", the `video_url` field can be used to construct a playable link.

2. **requirements.txt updates**:
   - Add `faster-whisper>=1.0.0` (or `whisperx>=3.0.0` if chosen).
   - Add `scenedetect>=0.6.0` (for Phase B).
   - `ffmpeg-python` and `pytesseract` are already present.

---

## 4. Open Questions / Decisions Needed

1. **Transcription library**: `faster-whisper` is lighter and sufficient for segment-level timestamps. `whisperx` adds word-level alignment and speaker diarization but is heavier and requires `torchaudio` + `pytorch`. Recommend `faster-whisper` for Phase A. **Ask user before installing.**
2. **Vision captioning**: The project does not currently have a local VLM for captioning. Options:
   - **A**: Use existing OpenAI GPT-4o vision API (simplest, consistent with current stack, no new deps).
   - **B**: Add a local model like `Salesforce/blip-image-captioning-base` or a small Llava variant (adds dependencies, runs offline).
   Recommend **A** for Phase B, but will ask.
3. **Qdrant collection**: `heritage_lens_text` is already 384-dim COSINE. No collection config changes needed. **No action required.**
4. **Video URL / object storage**: The plan assumes `video_url` will be populated. If the video is just a local file in `data/corpus/`, the URL can be a relative or file path. If there's a real object storage endpoint (S3, MinIO, etc.), we need the base URL. I will assume local file path for now and make `video_url` configurable.

---

## 5. Deliverables Checklist

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | Analysis + Plan (this doc) | ✅ Done |
| 2 | Video ingestion module (`agent/video_ingest.py`) | Pending Phase A |
| 3 | Retrieval + UI changes for timestamps | Pending Phase A/C |
| 4 | `requirements.txt` updates + run instructions | Pending Phase A |

---

*Generated: 2026-06-12*
*Analyst: Agent*
