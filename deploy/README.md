# Deploy / rebuild Heritage Lens on a fresh server

This folder holds the infrastructure artifacts needed to reproduce the live deployment
(public site at a Cloudflare-tunnelled domain + abuse monitoring). It complements the
app-level docs — read those first for architecture and the API:

- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — as-built system design (canonical).
- [`../api/DEPLOY.md`](../api/DEPLOY.md) — running the FastAPI service in the existing stack.

> **Not in git (runtime state):** `data/corpus/`, `data/cache/`, and the Qdrant vector
> store are gitignored. A fresh clone has **no corpus and no vectors** — you must re-ingest
> the corpus (or copy `data/` + the Qdrant storage volume from the old server) after setup.

## Prerequisites
- Docker + Docker Compose (Qdrant + Redis run in containers — see `../docker-compose.yml`)
- Python 3 + a virtualenv
- **Node 20 LTS** (required by the Tailwind 4 frontend toolchain)
- **ffmpeg** system package (`apt install ffmpeg`) — needed by video ingestion
- `cloudflared` binary (for public access; install in step 6)

## 1. Clone + secrets
```bash
git clone https://github.com/BZcreativ/Heritage-Lens-Multimodal.git
cd Heritage-Lens-Multimodal
cp config/.env.example config/.env     # then fill in real API keys (gitignored)
```

## 2. Backing services (Qdrant + Redis)
```bash
docker compose up -d                   # see ../docker-compose.yml
```

## 3. Python deps
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## 4. Build the React SPA (served by FastAPI from ui/frontend/dist)
```bash
cd ui/frontend && npm ci && npm run build && cd ../..
```

## 5. Run the API as a service
```bash
sudo cp deploy/systemd/heritage-api.service /etc/systemd/system/
# edit User/Group, WorkingDirectory, venv path, EnvironmentFile to match this host
sudo systemctl daemon-reload && sudo systemctl enable --now heritage-api
curl -s localhost:8000/api/status      # smoke test
```
The service binds **127.0.0.1:8000** on purpose (`/api/upload` + `/api/ingest` are
unauthenticated — do not bind 0.0.0.0). Re-ingest the corpus before relying on search.

## 6. Public access — Cloudflare Tunnel
Install cloudflared, then:
```bash
cloudflared tunnel login                       # authorize the domain in a browser
cloudflared tunnel create heritagelens-app     # note the printed <TUNNEL_ID>
sudo mkdir -p /etc/cloudflared
sudo cp deploy/cloudflared-config.yml.example /etc/cloudflared/config.yml
# replace <TUNNEL_ID> in that file (tunnel: and credentials-file:)
cloudflared tunnel route dns heritagelens-app <your-domain>
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```
Cloudflare issues TLS automatically. Free tier: ~100 MB request-body cap (large video
uploads must be added server-side, not through the public domain).

## 7. Abuse monitoring (ntfy alerts)
```bash
sudo cp deploy/heritage-watch.py /usr/local/bin/ && sudo chmod +x /usr/local/bin/heritage-watch.py
sudo cp deploy/heritage-watch.env.example /etc/heritage-watch.env
# set NTFY_TOPIC to a private, unguessable value (replace ...-CHANGEME); tune thresholds
sudo cp deploy/systemd/heritage-watch.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now heritage-watch
```
Subscribe to your topic in the ntfy app / `https://ntfy.sh/<your-topic>`. The watcher
follows the `heritage-api` journal and pushes alerts on `/api/*` floods, 4xx scan bursts,
and repeated upload/ingest. It only alerts — blocking is done at Cloudflare (next step).

## 8. Edge rate limiting (Cloudflare)
Recreate the rate-limit rule from `deploy/cloudflare-ratelimit.json` (block >20 req/10s to
`/api/*`, excluding `/api/images` & `/api/media`). With a token scoped to **Zone WAF: Edit**:
```bash
ZONE=<your-zone-id>; TOKEN=<scoped-api-token>
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  --data @deploy/cloudflare-ratelimit.json \
  "https://api.cloudflare.com/client/v4/zones/$ZONE/rulesets/phases/http_ratelimit/entrypoint"
```
Free-tier constraints: period must be `10` and `mitigation_timeout` must equal it (`10`);
the block auto-renews while a flood continues. (Or create the same rule in the dashboard:
Security → WAF → Rate limiting rules.)
