# Heritage Lens — FastAPI layer (`api/`)

This is **Step 1** of the web-UI rebuild: a thin REST API that wraps the existing
agent pipeline so the new React frontend can talk to it. It imports the existing
modules and **does not reimplement** anything in `agent/`.

## What it exposes

| Method | Route | Purpose |
|---|---|---|
| GET  | `/api/status` | Corpus stats (text chunks, images, video chunks, corpus PDFs). |
| POST | `/api/search` | `{ "query": "..." }` → calls `run_pipeline`, returns the structured 3-layer result + sources + video chunks + images. |
| POST | `/api/ingest` | Triggers `initialize_vector_db()`, **streams progress over SSE**. |
| GET  | `/api/images?path=...` | Serves an image file (allow-listed dirs only). |
| GET  | `/api/health` | Liveness probe. |

## How to install (in this repo, same venv)

```bash
# from repo root
cp -r path/to/api ./api          # drop this folder at repo root
pip install fastapi "uvicorn[standard]" sse-starlette
# (or add the three lines below to requirements.txt)
```

Add to `requirements.txt`:
```
fastapi>=0.110
uvicorn[standard]>=0.29
sse-starlette>=2.1
```

## How to run

```bash
# Qdrant must be up (docker compose up qdrant), corpus indexed once.
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Then: `curl localhost:8000/api/status` and
`curl -X POST localhost:8000/api/search -H 'content-type: application/json' -d '{"query":"What was the ritual function of obsidian at olmec ceremonial sites?"}'`

The existing Streamlit app (`ui/app.py`) is untouched and still runs on 8501.

## Important design ↔ reality notes (read before building the frontend)

1. **Sources panel** is built from `retrieved_chunks[].metadata` (reliable structured
   data), de-duplicated by `source_name` — *not* by parsing the `layer_2_sources`
   string. The raw string is still returned as `answer_sources_raw` if you want it.
2. **Citations:** the pipeline does **not** emit numbered `[1][2]` anchors in the
   answer text. The design's "click ¹ to jump to source" interaction has nothing to
   bind to yet. Options: (a) drop numbered citations and just render the answer +
   the Sources list; (b) add a post-process step in `generator.py` later to number
   them. The API returns the answer as a raw string with `[BACKGROUND — not
   retrieved]` markers inline — render those as the amber tag via regex.
3. **Confidence bar:** Layer 3's "⚠️ CONFIDENCE" section is prose, not a number.
   The API derives a coarse `level` (low/moderate/high → 1/3/4 segments) by keyword,
   and also returns the raw confidence text. Treat the bar as indicative.
4. **Qdrant URL:** matches the retriever's default (`http://localhost:6333`); override
   with env `HL_QDRANT_URL` (use `http://qdrant:6333` inside docker-compose).
5. `parsing.py` holds all the string→struct logic in pure functions so you can unit
   test it without a running pipeline or DB.

## Files
- `api/main.py` — app factory, CORS, router mount, static image route.
- `api/routes.py` — the four endpoints.
- `api/models.py` — Pydantic response models (mirror the frontend's `SearchResult`).
- `api/parsing.py` — pure functions: layer-3 split, source building, video/image mapping, confidence heuristic.
- `api/corpus.py` — Qdrant + filesystem counts for `/status`.
