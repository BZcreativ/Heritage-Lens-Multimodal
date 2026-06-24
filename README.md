# Heritage Lens Agent
> "Most AI systems optimise for answers. This one makes the construction of those answers visible and accountable."

An **accountable, multimodal RAG agent** for specialised cultural-heritage archives (a
Mesoamerican / Olmec corpus). Unlike standard RAG that optimises for confident answers, it
makes the *construction* of those answers visible.

> 📐 Full as-built architecture + change log: **[ARCHITECTURE.md](ARCHITECTURE.md)** · setup & run: **[VIDEO_RUN_INSTRUCTIONS.md](VIDEO_RUN_INSTRUCTIONS.md)**

Every response contains three layers:

| Layer | What it does |
|-------|-------------|
| **1 — Answer** | Grounded response using only retrieved sources. General knowledge is labelled `[BACKGROUND — not retrieved]` |
| **2 — Source Grounding** | Full attribution: source name, author, page **or timestamp**, type, institution, modality |
| **3 — Epistemic Transparency** | Source bias, knowledge absences, interpretive limits, confidence — tied to the actual retrieved metadata, not generic disclaimers |

A **Judge** (second GPT-4o call) checks Layer 3 for specificity and regenerates it if it's generic. When retrieval is weak, the system says so and expands the absences section rather than confabulating. **Failure is a feature.**

---

## What works today

- **Text RAG** over the PDF corpus → `heritage_lens_text` (384-dim, all-MiniLM-L6-v2), 3-layer answers + Judge loop.
- **Image search** → `heritage_lens_images` (768-dim, SigLIP 2): PDF page images, uploaded images, and video keyframes; cross-modal text→image query.
- **Video indexing**, two ways in parallel:
  - *Visual* — keyframes embedded with SigLIP (`media_type=video_frame`).
  - *Audio* — transcription via **Parakeet v3** (`onnx-asr`, default) with **faster-whisper fallback**; optional **GLM-4.5V** scene captions + **Tesseract OCR** (Phase B). All timestamped and modality-tagged into `heritage_lens_text`.
- **Streamlit 3-panel UI** with upload→index, a Video Evidence gallery, and modality badges.
- **Web UI (new, branch `feature/web-ui`)** — a **FastAPI** layer (`api/`) wrapping the pipeline + a **React/Vite/TS/Tailwind 4** SPA (`ui/frontend/`) recreating the approved design. Every nav item (Ask / Sources / Uploads / Sessions) binds to a real endpoint; three-panel results, galleries + lightbox, dark mode, reading-comfort. Served by one host service (`heritage-api`, `127.0.0.1:8000`) alongside Streamlit (:8501). See [ARCHITECTURE.md §5b](ARCHITECTURE.md).
  - **Functional Answer Mode** — Strict Corpus-Only / Corpus + Background / Exploratory now actually change behaviour: retrieval breadth (`top_k`), generation strictness, and temperature, not just an echoed label.
  - **Source management** — delete a source from the Sources view (confirm dialog) → removes its text + image vectors **and** its files on disk via `DELETE /api/sources/{name}`.
  - **In-app media playback** — video/audio chunks play inline in the gallery + lightbox, with keyframe posters, served range-aware by `GET /api/media`.
- **Verified state (2026-06-13):** `heritage_lens_text` = 623 chunks · `heritage_lens_images` = 165 (incl. video keyframes).

> **Note on storage:** everything searchable is embedded into Qdrant, but Qdrant stores *vectors + metadata*, not raw files. Image **files** live on disk (`data/cache/images/`); Qdrant holds the vector + an `image_path` pointer. See ARCHITECTURE.md §2.

---

## Technical stack (as-built)

| Component | Tool |
|-----------|------|
| Answers + Judge | OpenAI GPT-4o |
| Text embeddings | `all-MiniLM-L6-v2` (384-dim) |
| Image embeddings | `google/siglip2-base-patch16-224` (768-dim) |
| Speech-to-text | **Parakeet v3** (`nemo-parakeet-tdt-0.6b-v3` int8, via `onnx-asr` + Silero VAD) — default; `faster-whisper` fallback (`HL_ASR_BACKEND`) |
| Frame captioning | **GLM-4.5V** via z.ai (GPT-4o vision fallback) |
| OCR | Tesseract (`eng+ita+spa`) |
| RAG pipeline | LlamaIndex |
| Vector DB | Qdrant (Docker, `localhost:6333`) |
| Cache | Redis (Docker) |
| UI | Streamlit (3-panel) · **Web UI:** FastAPI (`api/`) + React/Vite/TS/Tailwind 4 (`ui/frontend/`) |
| Web serving | `heritage-api.service` (uvicorn serves API + built SPA on `127.0.0.1:8000`) |
| Config | `config/.env` (loaded by systemd in prod / `agent/env_loader.py` on host) |

---

## Metadata schema

Text chunk payload (drives Layer 2/3):

```json
{
  "source_name": "filename.pdf | video.mp4",
  "source_type": "thesis | book | video | ...",
  "institution": "", "cultural_perspective": "", "language_of_origin": "", "author": "",
  "page_number": "12",                 // PDFs
  "modality": "audio_transcript | visual_caption | ocr_text",   // video-derived
  "video_id": "", "video_url": "", "start": 12.5, "end": 18.3   // video-derived
}
```

Layer 3 only works if this metadata is injected into the retrieved context — raw text chunks are insufficient.

---

## Pipeline

```
User query
  → retrieve top-k chunks (with metadata, balanced across sources)
  → GPT-4o generates 3-layer response
  → Judge evaluates Layer 3 (VALID / WEAK) → regenerate if WEAK
  → Streamlit 3-panel UI  (+ Video Evidence gallery for video-derived results)
```

Ingestion entry point: `agent/ingest.py::initialize_vector_db()` (rebuilds text collection, re-indexes `data/corpus/`).

---

## Repo structure

```
heritage-lens-multimodal/
├── ARCHITECTURE.md              <- canonical as-built doc + change log
├── VIDEO_INDEXING_PLAN.md       <- video feature analysis/plan
├── VIDEO_RUN_INSTRUCTIONS.md    <- setup & run guide
├── agent/
│   ├── ingest.py  image_extractor.py  image_ingest.py  video_ingest.py
│   ├── retriever.py  generator.py  judge.py  pipeline.py  env_loader.py
├── api/           <- FastAPI layer (main, routes, models, parsing, corpus) + tests
├── config/        <- settings.yaml, prompts.yaml, .env (gitignored)
├── data/          <- corpus/ + cache/ (gitignored)
├── docs/design/   <- web UI design spec + approved prototype
├── tests/         <- isolated-collection video tests
├── ui/
│   ├── app.py     <- Streamlit 3-panel UI (:8501)
│   └── frontend/  <- React/Vite/TS/Tailwind 4 SPA (served by heritage-api :8000)
└── docker-compose.yml   <- Qdrant + Redis
```

Run/setup details (deps, ingest, env knobs `HL_ASR_BACKEND` / `HL_WHISPER_MODEL` / `HL_FRAME_INTERVAL` / `HL_OCR_LANG`) are in [VIDEO_RUN_INSTRUCTIONS.md](VIDEO_RUN_INSTRUCTIONS.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

---

## History

| Date | Milestone |
|------|-----------|
| 2026-04 | Origin: 3-layer accountable RAG over the Mesoamerican corpus (KXSB AR26 HackXelerator — Ethics, Agency & Societal Impact). |
| 2026-06-01 | Corpus restored; document-upload feature; Qdrant healthcheck fixed. |
| 2026-06-03 | Vector DB migrated ChromaDB → **Qdrant**; SigLIP image indexing + PDF image extraction + frame-only video indexing. |
| 2026-06-12/13 | **Video Phase A** (audio transcription) + **Phase B** (GLM-4.5V captions + OCR); modality-aware generator/UI; isolated-collection tests; `ARCHITECTURE.md`. |
| 2026-06-13 | Hardening: shared `env_loader`, deterministic point IDs, multilingual OCR, frame sampling, model singletons; fixed GLM model id (`glm-4.5v` + thinking-disabled) and an image-cache permission bug. |
| 2026-06-13 | **ASR swapped to Parakeet v3** (multilingual, lighter) behind `HL_ASR_BACKEND`, whisper fallback — resolves the full-ingest OOM. |
| 2026-06-19 | **Web UI rebuild** (branch `feature/web-ui`): **FastAPI** layer (`api/`) wrapping the pipeline + a **React/Vite/TS/Tailwind 4** SPA (`ui/frontend/`) recreating the approved design; new `/api/sources` + `/api/upload` endpoints so every nav item is backed; single-service deploy (`heritage-api`, uvicorn serves API + SPA on `127.0.0.1:8000`). Node 18→20. Streamlit + `agent/*`/`config/*` untouched. |
| 2026-06-24 | **Corpus management + playback** (branch `feature/corpus-management`): **Answer Mode made functional** — `agent/pipeline.py` + `agent/generator.py` now thread `mode` to set retrieval breadth (`top_k`), corpus-grounding strictness, and temperature (supersedes the 2026-06-19 "`agent/*` untouched" note). **Source deletion** via `DELETE /api/sources/{name}` (removes text + image vectors and on-disk files; confirm-dialog UI). **In-app audio/video playback** via range-aware `GET /api/media` + keyframe posters, played inline in the gallery + lightbox. |

Full detail in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Team

| Person | Role |
|--------|------|
| **[Lara](https://github.com/AidanandMe)** | Project Lead & Project Owner |
| **buzman** | Lead Engineer — pipeline, infra, orchestration |

## Demo query

> "What was the ritual function of obsidian at Olmec ceremonial sites?"

A query where corpus coverage is thin — demonstrating failure handling as a feature.
