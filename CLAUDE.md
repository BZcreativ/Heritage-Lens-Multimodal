# Heritage Lens — Web UI rebuild (Claude Code working notes)

This repo is replacing the **Streamlit** UI (`ui/app.py`) with a modern web app:
a **FastAPI** layer (`api/`) wrapping the existing agent pipeline, and a
**React + Vite + Tailwind** frontend (`ui/frontend/`).

## Read these first (in order)
1. `docs/design/README.md` — the full frontend design spec (layout, components,
   tokens, interactions, state model). This is the source of truth for the UI.
2. `docs/design/reference/Heritage Lens Sidebar Classic.html` + `app.js` — the
   approved hi-fi prototype. **Recreate this in React; do not transplant the
   raw HTML/JS.**
3. `api/README.md` and `api/DEPLOY.md` — the already-built FastAPI layer and how
   it maps the real pipeline output to JSON the frontend consumes.

## Hard constraints (do not violate)
- **Never modify** `agent/*`, `config/*`, or `data/*`. Only *import* them.
- Keep `ui/app.py` (Streamlit) intact and runnable on :8501.
- Backend = FastAPI in `api/`, importing the EXISTING modules
  (`agent/pipeline.py`, `agent/ingest.py`). Do **not** reimplement the pipeline.
- Frontend = React + Vite + TypeScript + Tailwind CSS 4 in `ui/frontend/`.
  State via React context/hooks only (no Redux). Fonts via `@fontsource`.
- Qdrant lives at `localhost:6333` (Docker). The API + frontend run as host
  processes, like the existing `heritage-streamlit.service`.

## Status
- **`api/` (Step 1) is already written** — review it, install deps
  (`fastapi`, `uvicorn[standard]`, `sse-starlette`), run
  `pytest api/tests/test_parsing.py`, and smoke-test `uvicorn api.main:app`.
  Endpoints: `GET /api/status`, `POST /api/search`, `POST /api/ingest` (SSE),
  `GET /api/images?path=...`, `GET /api/health`.
- **`ui/frontend/` (Step 2) is NOT built yet** — that's the implementation task.

## The real pipeline shape (so you don't trust assumptions)
`run_pipeline(query)` returns a dict of strings:
`layer_1_answer`, `layer_2_sources`, `layer_3_transparency` (one string with 4
emoji sections: ⚠️ SOURCE BIAS / 📄 ABSENCES / 🕵️ INTERPRETIVE LIMITS /
⚠️ CONFIDENCE), `layer_4_image_keyword`, plus `retrieved_chunks` and
`retrieved_images`. The `api/` layer already parses all of this — the frontend
should consume the **API's** JSON (`SearchResult`), not the raw pipeline output.

### Known gaps (decide explicitly)
- No numbered `[1][2]` citations upstream → render answer as text + the Sources
  list (built from chunk metadata). Add numbering in `generator.py` only if asked.
- Confidence bar is heuristic (keyword-derived); raw prose is in
  `epistemic.confidence.note`.
- `POST /api/ingest` is a **full rebuild** (deletes + recreates collections);
  minutes for video. Stream its SSE progress in the Uploads flow.

## Build order (Step 2)
1. Scaffold Vite + React + TS + Tailwind 4 in `ui/frontend/`; add `@fontsource`
   (inter, atkinson-hyperlegible) + OpenDyslexic; port design tokens from
   `docs/design/README.md` into `src/globals.css`.
2. `src/lib/api.ts` — typed client for the endpoints above, incl. an SSE helper
   for `/ingest`. Vite dev proxy `/api` → `http://localhost:8000`.
3. Contexts: `ThemeContext` (dark, persisted, system default), `ReadingContext`
   (reading-comfort vars, persisted), `SearchContext` (query, state machine,
   result, history).
4. Layout shell: 3-col grid, Sidebar, TopBar, Footer, column-collapse.
5. SearchBar + empty/loading/results states (⌘/Ctrl+Enter, `/` to focus).
6. The three panels — Answer (raw text + `[BACKGROUND — not retrieved]` → amber
   tag via regex), Sources (expandable rows from `sources[]`), Epistemic panel
   in the right rail (4 colored cards + confidence bar).
7. Video + Visual galleries + Lightbox; video seek when `video_url` is http(s).
8. Reading Comfort panel, dark mode, session mask, history/share/export,
   keyboard shortcuts.
9. Wire to the live API; test against the real corpus; add a `heritage-api`
   systemd unit (see `api/DEPLOY.md`); build + serve the frontend.

Keep commits small and grouped. After each numbered step, pause and report so a
human can verify before continuing.
