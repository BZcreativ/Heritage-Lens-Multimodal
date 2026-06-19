# Deploying the API alongside the existing stack

Your setup (from `docker-compose.yml`): **Qdrant + Redis run in Docker**, and
**Streamlit runs as a host systemd service** (`heritage-streamlit.service`) to
avoid Docker disk pressure from the PyTorch/CUDA layers. The retriever talks to
Qdrant at `localhost:6333`.

The FastAPI layer should run **the same way as Streamlit** — as a host systemd
service in the same virtualenv — so it shares `localhost:6333` and the heavy ML
deps already installed. Do **not** dockerize it (same reasoning as Streamlit).

## 1. Drop the folder in & install deps
```bash
cd /path/to/Heritage-Lens-Multimodal
git checkout feature/multimodal-video-indexing
git checkout -b feature/web-ui

cp -r /downloaded/api ./api                 # api/ at repo root (sits beside agent/, ui/)

# same venv Streamlit uses:
source .venv/bin/activate                   # adjust to your venv path
pip install "fastapi>=0.110" "uvicorn[standard]>=0.29" "sse-starlette>=2.1"
```

Append to `requirements.txt`:
```
# Web API layer
fastapi>=0.110
uvicorn[standard]>=0.29
sse-starlette>=2.1
```

## 2. Smoke-test by hand
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
# in another shell:
curl localhost:8000/api/status
curl -X POST localhost:8000/api/search \
  -H 'content-type: application/json' \
  -d '{"query":"What was the ritual function of obsidian at olmec ceremonial sites?"}'
```
Unit-test the parsing (no DB needed):
```bash
pytest api/tests/test_parsing.py -q
```

## 3. systemd unit (mirror heritage-streamlit.service)
`/etc/systemd/system/heritage-api.service`:
```ini
[Unit]
Description=Heritage Lens FastAPI
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/Heritage-Lens-Multimodal
Environment=HL_QDRANT_URL=http://localhost:6333
# Lock CORS to wherever the frontend is served from in prod:
Environment=HL_CORS_ORIGINS=http://localhost:5173,https://your-frontend-host
ExecStart=/path/to/Heritage-Lens-Multimodal/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now heritage-api
sudo journalctl -u heritage-api -f
```

## 4. Frontend dev wiring (next step, not this handoff)
In `ui/frontend/` add a Vite dev proxy so `/api/*` hits uvicorn:
```ts
// vite.config.ts
export default defineConfig({
  server: { proxy: { "/api": "http://localhost:8000" } },
});
```
In prod, serve the built frontend (e.g. via nginx) and reverse-proxy `/api` to
:8000. Keep `HL_CORS_ORIGINS` accurate.

## Constraints honored
- `agent/*`, `config/*`, `data/*` untouched — the API only **imports** them.
- `ui/app.py` (Streamlit) untouched; runs independently on 8501.
- Image serving is traversal-guarded to `data/cache/images`, `data/corpus`, `ui/assets`.

## Known gaps to discuss before frontend build
- No numbered citations upstream → the answer renders as text + a separate
  Sources list (built from chunk metadata). Add citation numbering in
  `generator.py` later if you want clickable ¹²³ anchors.
- Confidence bar is heuristic (keyword-derived); the raw CONFIDENCE prose is in
  `epistemic.confidence.note`.
- `/api/ingest` streams `initialize_vector_db()`'s stdout. It's a full rebuild
  (deletes + recreates collections) and can take minutes for video — the SSE
  progress lines are the print() statements from ingest/video_ingest.
