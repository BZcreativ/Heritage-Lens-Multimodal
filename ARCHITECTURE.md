# Heritage Lens — Architecture (as-built)

> **Living document.** This is the canonical description of how the system actually works
> today, plus a running history of changes. Update it whenever the architecture changes.
> For the product vision see [README.md](README.md); for the original video plan see
> [VIDEO_INDEXING_PLAN.md](VIDEO_INDEXING_PLAN.md); for setup/run steps see
> [VIDEO_RUN_INSTRUCTIONS.md](VIDEO_RUN_INSTRUCTIONS.md).

**Last updated:** 2026-06-13

---

## 1. What it is

Heritage Lens is an **accountable, multimodal RAG agent** for specialised archives
(Mesoamerican/Olmec cultural-heritage corpus). Every answer is returned in three layers:

| Layer | Content |
|-------|---------|
| **1 — Answer** | Grounded response from retrieved sources; general knowledge labelled `[BACKGROUND — not retrieved]` |
| **2 — Source Grounding** | Attribution: source name, author, page **or timestamp**, type, institution, modality |
| **3 — Epistemic Transparency** | Source bias, absences, interpretive limits, confidence — derived from real retrieved metadata |

A **Judge** (second GPT-4o call) checks Layer 3 for specificity and triggers regeneration if it's generic.

---

## 2. Storage model — the important mental model

**Everything searchable is embedded into Qdrant. But Qdrant stores _vectors + metadata_, not raw files.**
Images are binary, so the picture itself lives on disk and Qdrant holds a vector plus an
`image_path` pointer to it.

### Qdrant collections (vectors live here)

| Collection | Dim · Model | Distance | Holds |
|------------|-------------|----------|-------|
| `heritage_lens_text` | 384 · `all-MiniLM-L6-v2` | COSINE | PDF text chunks, video **audio transcripts**, video **visual captions**, **OCR** text |
| `heritage_lens_images` | 768 · `google/siglip2-base-patch16-224` | COSINE | PDF page images, uploaded images, video **keyframes** — each a SigLIP vector + payload (`image_path`, `media_type`, `timestamp_sec`, …) |

Text and images are deliberately in **separate vector spaces** (384 vs 768) — they are not directly comparable; cross-modal search is done by embedding the text query with SigLIP's text tower and searching the image collection.

### Disk (files live here)

- `data/corpus/` — source PDFs and uploaded videos/images (the inputs).
- `data/cache/images/` — extracted/derived **PNG files**: PDF page images, copied uploads, and video keyframes. Qdrant points in `heritage_lens_images` reference these by `image_path`; the UI loads them from disk to display.
- `qdrant_storage/`, `redis_data/` — container-managed state (not written by the app directly).

> **Why a file write can break "indexing to Qdrant":** writing the keyframe/page PNG to
> `data/cache/images/` is a required step of image indexing. If that directory isn't writable
> by the service user, image indexing fails even though the text side is pure-Qdrant. (This is
> exactly the `Permission denied: …monument_t0.png` failure — see History 2026-06-13.)

---

## 3. Ingestion pipeline

Entry point: `agent/ingest.py::initialize_vector_db()` (the UI "Process & Index" button calls this; it
**recreates `heritage_lens_text` and re-indexes the whole `data/corpus/`**). Order:

```
1. PDF text         pypdf → SentenceSplitter(512/50) → MiniLM 384d → heritage_lens_text
2. PDF page images  image_extractor → PNG to data/cache/images/ → SigLIP 768d → heritage_lens_images
3. Standalone imgs  copy to cache → SigLIP → heritage_lens_images
4. Video keyframes  ffmpeg ~1 fps → PNG to data/cache/images/ → SigLIP → heritage_lens_images   (image_ingest.index_video_frames)
5. Video audio      ffmpeg → Parakeet v3 (VAD-segmented, default) or whisper → MiniLM → heritage_lens_text   (video_ingest, Phase A)
6. Video visual     PySceneDetect + frame sampling → GLM-4.5V caption + tesseract OCR → MiniLM → heritage_lens_text   (video_ingest, Phase B — OFF by default)
```

### A video is indexed two ways, on purpose
- **Visually** (step 4): keyframes → image collection → find a moment by *what's on screen* (SigLIP).
- **Textually** (steps 5–6): spoken audio (and optional captions/OCR) → text collection → find by *what's said / written*.

Phase B is disabled in the corpus rebuild by default (`index_visual=False` in `ingest.py`); enable by passing `index_visual=True` to `index_videos_in_corpus`.

### Modules
| File | Responsibility |
|------|----------------|
| `agent/ingest.py` | Orchestrates the full rebuild; PDF text indexing |
| `agent/image_extractor.py` | Extracts images from PDF pages |
| `agent/image_ingest.py` | SigLIP embedding of PDF/standalone images **and video keyframes** → `heritage_lens_images` |
| `agent/video_ingest.py` | Phase A (audio→transcript) + Phase B (scene caption/OCR) → `heritage_lens_text` |
| `agent/env_loader.py` | Loads `config/.env` by absolute path (shared by all modules) |

---

## 4. Retrieval, generation, judge

- **`agent/retriever.py`**
  - `retrieve_chunks(query)` → `heritage_lens_text` via LlamaIndex; balanced retrieval across sources; returns `text`, `metadata`, `score`.
  - `retrieve_images(query, media_type=…)` → embeds query with SigLIP text tower → `heritage_lens_images`; supports `source_filter` / `media_type` (`pdf_image`, `uploaded_image`, `video_frame`).
- **`agent/generator.py`** — GPT-4o, JSON output. `analyze_metadata()` counts `source_type` / `institution` / `cultural_perspective` / **`modality`**. Video chunks render `Timestamp: {start}s–{end}s` + `Modality:` instead of `Page:`; Layer 3 treats modality as a provenance signal (audio = "narrated, not visually confirmed", etc.).
- **`agent/judge.py`** — GPT-4o evaluates Layer 3 specificity → regenerate loop.
- **`agent/pipeline.py`** — wires retrieve → generate → judge.

---

## 5. UI (`ui/app.py`, Streamlit)

- 3-panel layout: Answer / Sources / Epistemic Transparency.
- Sidebar: upload PDFs/images/videos → "Process & Index" → full rebuild. Shows text + video chunk counts.
- Results: PDF image gallery + a **Video Evidence gallery** with modality badges (`audio_transcript`/`visual_caption`/`ocr_text`), timestamps, and seek links (for `http` `video_url`s).

### 5b. Web UI (`api/` + `ui/frontend/`, 2026-06-19 — branch `feature/web-ui`)

A modern web app that **replaces** Streamlit for day-to-day use (Streamlit stays intact on :8501):

- **`api/`** — a thin **FastAPI** layer that *imports* the existing pipeline (no reimplementation). Endpoints: `GET /api/status`, `POST /api/search {query,mode}`, `GET /api/sources`, `POST /api/upload` (multipart → `data/corpus/`), `POST /api/ingest` (SSE rebuild), `GET /api/images?path=` (traversal-guarded). `api/parsing.py` holds pure string→struct helpers (unit-tested, no DB). The `/api/search` JSON exactly matches `api/models.SearchResult`; if it ever diverges, fix it in `api/parsing.py` — **never** in `agent/*`.
- **`ui/frontend/`** — a **React + Vite + TypeScript + Tailwind 4** SPA recreating the approved "Sidebar Classic" design (`docs/design/`). Nav (Ask / Sources / Uploads / Sessions) each bind to a real endpoint; three-panel results (Answer with `[BACKGROUND]` amber tags, Sources, Epistemic rail), video/image galleries + lightbox, dark mode, and a Reading-Comfort drawer (typeface applies app-wide; spacing/width/cream scoped to the answer). State via React context only.
- **Deploy:** `heritage-api.service` (systemd, host, mirrors `heritage-streamlit.service`) runs `uvicorn api.main:app` and **serves the built SPA + the API from one process** (same-origin, no nginx). Bound **`127.0.0.1:8000`** deliberately — `/api/upload` + `/api/ingest` are unauthenticated; do **not** bind `0.0.0.0` without adding auth. `api/main.py` mounts `ui/frontend/dist/` at `/` when present; rebuild the SPA (`npm run build` as `heritage`) after frontend changes. Requires **Node 20 LTS**.
- **Answer Mode** select is accepted + echoed in `meta` but a **no-op upstream** (pipeline is `run_pipeline(query)` only).

---

## 6. Models & external services

| Role | Model / service |
|------|-----------------|
| Text embeddings | `all-MiniLM-L6-v2` (384d) |
| Image embeddings | `google/siglip2-base-patch16-224` (768d) |
| Speech-to-text (default) | **Parakeet v3** (`nemo-parakeet-tdt-0.6b-v3`, int8 ONNX via `onnx-asr` + Silero VAD) — multilingual incl. it/es, ~1–1.5 GB RAM |
| Speech-to-text (fallback) | `faster-whisper` `large-v3` (auto-used if Parakeet fails; `HL_ASR_BACKEND=whisper` to force) |
| Frame captioning | **GLM-4.5V** via z.ai (`https://api.z.ai/api/paas/v4`), GPT-4o vision fallback |
| OCR | Tesseract (`eng+ita+spa`) |
| Answer / Judge | OpenAI GPT-4o |
| Vector DB | Qdrant (`localhost:6333`, Docker) |
| Cache | Redis (Docker) |

### Configuration
- Secrets/config live in **`config/.env`**, loaded in prod by the systemd unit
  `heritage-streamlit.service` (`EnvironmentFile=`) and in code by `agent/env_loader.load_env()`
  (resolves `config/.env` by absolute path — a bare `load_dotenv()` finds nothing since there's no root `.env`).
- Tunable env vars (all have safe defaults):

  | Var | Default | Effect |
  |-----|---------|--------|
  | `HL_TEXT_COLLECTION` | `heritage_lens_text` | Override target collection (tests use a throwaway) |
  | `HL_ASR_BACKEND` | `parakeet` | Speech-to-text backend: `parakeet` or `whisper` |
  | `HL_PARAKEET_MODEL` / `HL_PARAKEET_QUANT` | `nemo-parakeet-tdt-0.6b-v3` / `int8` | Parakeet model + quantization |
  | `HL_WHISPER_MODEL` | `large-v3` | Whisper model size (fallback backend) |
  | `HL_FRAME_INTERVAL` | `90` | Seconds between sampled video frames within a scene |
  | `HL_MAX_FRAMES_PER_SCENE` | `8` | Cap on sampled frames per scene |
  | `HL_OCR_LANG` | `eng+ita+spa` | Tesseract languages (filtered to installed packs) |

---

## 7. Operational notes

- **Run as the `heritage` user** (the Streamlit service user). Running ingest as root creates
  root-owned files under `data/cache/images/` that the service then can't overwrite.
  Manual ingest: `sudo -u heritage ./venv/bin/python agent/ingest.py`.
- **System deps:** `ffmpeg`, `tesseract-ocr` + `tesseract-ocr-ita` + `tesseract-ocr-spa`, `espeak-ng` (tests only).
- **Tests are isolated:** `tests/_util.py` forces `HL_TEXT_COLLECTION` to `heritage_lens_text_pytest`,
  created/torn down per run — tests never touch production data. Video upserts use deterministic
  IDs (`uuid5` of video_id|modality|start|end|text) so re-ingest overwrites instead of duplicating.

---

## 8. Current state

_Verified 2026-06-13 after a clean full re-ingest with Parakeet default (completed exit 0, no OOM):_

| Collection | Points | Contents |
|------------|--------|----------|
| `heritage_lens_text` | **623** | Text chunks from 3 PDFs. (`monument.mp4` has **no speech** → Parakeet returns 0 transcript chunks; Phase B captions/OCR off.) |
| `heritage_lens_images` | **165** | 160 PDF page images + **5 `monument.mp4` keyframes** (`media_type=video_frame`, `image_path` → `data/cache/images/`) |

So the uploaded `monument.mp4` is indexed **visually** (5 keyframes, searchable by what's on screen) and has **no audio** to transcribe. The full ingest now runs end-to-end — the Parakeet default cleared the video-audio stage that previously OOM-killed on whisper `large-v3`.

> **Full-ingest memory:** previously a full `initialize_vector_db()` was OOM-killed on this host
> when whisper `large-v3` (~3 GB) loaded last. **Resolved** by defaulting ASR to **Parakeet v3 int8**
> (~1–1.5 GB). If you force `HL_ASR_BACKEND=whisper`, use `HL_WHISPER_MODEL=medium`/`small` on this box.
> The duplicate SigLIP load (`image_ingest`) is still pending — see §10.

---

## 9. Progress & history

| Date | Change |
|------|--------|
| 2026-04 | Hackathon origin: 3-layer accountable RAG over Mesoamerican corpus (see README). |
| 2026-06-01 | Corpus restored; Qdrant healthcheck fixed; document upload feature shipped. |
| 2026-06-03 | Vector DB switched from hardwired ChromaDB → **Qdrant**; added SigLIP image indexing (`heritage_lens_images`), PDF image extraction, and frame-only video indexing (`image_ingest.index_video_frames`). |
| 2026-06-12 | `VIDEO_INDEXING_PLAN.md` written; knowledge graph built (`graphify-out/`). |
| 2026-06-12/13 | **Video Phase A** (audio → faster-whisper transcript → `heritage_lens_text`) and **Phase B** (PySceneDetect → frame caption → OCR) implemented in `agent/video_ingest.py`; generator/UI made modality-aware. |
| 2026-06-13 | **Review & hardening:** Phase B's GLM call was non-functional — fixed model id `glm-4v` → **`glm-4.5v`** + `thinking disabled` (reasoning model returned empty content); added single-shot **scene fallback**; fixed a latent `torch` ref. |
| 2026-06-13 | **Reliability pass:** shared `env_loader` (loads `config/.env` everywhere); **test isolation** via `HL_TEXT_COLLECTION` + `tests/_util.py`; **deterministic point IDs** (no re-ingest dupes); **error surfacing** in visual indexing (`errors` stat); **multi-frame sampling** for long videos; **multilingual OCR** (`eng+ita+spa`); **model singletons** (whisper/embedder loaded once). |
| 2026-06-13 | Fixed `Permission denied` on `data/cache/images/` (dir was root-owned; chowned to `heritage`). Root cause: a prior ingest ran as root. |
| 2026-06-13 | Knowledge graph updated to reflect the video pipeline (`graphify-out/`). |
| 2026-06-13 | Re-ingested as `heritage` after the permission fix: `heritage_lens_text`=623, `heritage_lens_images`=280 (incl. 5 `monument.mp4` keyframes — permission fix confirmed). Full ingest **OOM-killed** when whisper `large-v3` loaded; monument audio added separately with `HL_WHISPER_MODEL=base` (no speech → 0 chunks). |
| 2026-06-13 | **ASR swapped to Parakeet v3** (`nemo-parakeet-tdt-0.6b-v3` int8 via `onnx-asr` + Silero VAD) behind `HL_ASR_BACKEND` (default `parakeet`, whisper auto-fallback). Multilingual (it/es), ~half the RAM → resolves the full-ingest OOM. Verified end-to-end on both backends; Parakeet transcribed the test phrase more accurately than whisper. Added `onnx-asr[cpu,hub]` to requirements. |
| 2026-06-19 | **Web UI rebuild** (branch `feature/web-ui`): new **FastAPI** layer (`api/`) wrapping the pipeline + a **React/Vite/TS/Tailwind 4** SPA (`ui/frontend/`) recreating the approved design (`docs/design/`). Added `GET /api/sources` and `POST /api/upload` so every nav item is backed by a real endpoint; `SearchRequest.mode` passthrough (no-op). Single-service deploy via `heritage-api.service` (uvicorn serves API + built SPA on `127.0.0.1:8000`, no nginx). Node bumped 18→20 LTS. Streamlit (`ui/app.py`) left intact on :8501; `agent/*` and `config/*` untouched. Verified live against the corpus (Playwright, 0 console errors). See §5b. |
| 2026-06-24 | **Corpus management + media playback** (branch `feature/corpus-management`). **Answer Mode is now functional** (was a no-op passthrough): `run_pipeline(query, mode=...)` maps the mode to retrieval breadth (`MODE_TOP_K`: Strict 8 / Background 15 / Exploratory 25) and `generate_response(..., mode=...)` appends a per-mode strictness block to the system prompt and sets temperature (`MODE_TEMPERATURE` 0.2 / 0.3 / 0.6) — so `agent/pipeline.py` + `agent/generator.py` are now modified (the only post-rebuild changes to `agent/*`). **Source deletion:** `DELETE /api/sources/{name}` → `corpus.delete_source` removes text + image vectors and the retained corpus file; SPA `SourcesView` gains a `ConfirmDialog`. **In-app playback:** `GET /api/media` serves audio/video from the allow-listed dirs with Range support (206 seek); `_video_media_url`/`_video_poster_url` resolve a playable URL + nearest extracted keyframe poster, played inline in `VideoGallery` + `Lightbox`. |

---

## 10. Known limitations / future work

- `video_ingest.py` is large (~660 lines) and low-cohesion per the knowledge graph — candidate for splitting (Phase A / Phase B / helpers).
- Phase B (visual captions/OCR) is implemented and verified but **off by default** in corpus rebuild.
- Full re-index wipes and rebuilds `heritage_lens_text` each run (no incremental text ingest path in the UI).
- Latent path bug noted in `image_extractor.load_or_build_cache` (builds cache from `data/corpus/` but opens via workspace root) — not yet fixed.
- **Memory:** full-ingest OOM is resolved by the Parakeet-v3-int8 default. Still pending: the
  **duplicate SigLIP load** — `image_ingest` loads its own SigLIP in both `index_images_from_corpus`
  and `index_video_frames` instead of reusing one instance. Worth consolidating for headroom.
