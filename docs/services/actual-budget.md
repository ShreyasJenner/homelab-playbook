# Actual Budget

```
Status:     live (since about 2026-08-28)
Host:       homelab
Exposure:   tailnet-only (intended); 5006 is published on 0.0.0.0, so also reachable from the home LAN
URL:        https://budget.example.com (health: /health)
Config:     ~/docker/actual-budget/ (docker-compose.yml, .env: HOST_PORT, DOCKER_PORT, DATA_DIR_PATH; data/ → /data)
Depends on: Caddy
Per-User:   no; used by ShreyasJenner only
Verified:   2026-10-28
```

## What it's for

Personal budgeting, with the finance data kept private on the homelab.

## How it's set up

- Image `docker.io/actualbudget/actual-server:latest`, service `actual_server` (container `actual-budget-actual_server-1`), port `5006 → 5006`, `restart: unless-stopped`.
- **Data:** `~/docker/actual-budget/data → /data`, a bind mount, so restic backs it up. The folder is owned by root with mode 777, because Docker created it.
- Healthcheck: the image's own `node scripts/health-check.js` every 60 seconds. Uptime Kuma checks `http://localhost:5006/health`, with ntfy alerts.
- The data folder dates from 2026-08-28; the compose file and `.env` from 2026-09-01. No setup chat exists.
