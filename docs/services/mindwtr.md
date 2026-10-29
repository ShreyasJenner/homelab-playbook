# Mindwtr

```
Status:     live (since 2026-08-18)
Host:       homelab
Exposure:   tailnet-only (intended); 6301 and 6302 are published on 0.0.0.0, so also reachable from the home LAN
URL:        https://task.example.com (web app), https://tasksync.example.com (sync server, health /health)
Config:     ~/docker/mindwtr/ (docker-compose.yml; .env: AUTH_TOKEN, MINDWTR_CLOUD_CORS_ORIGIN, CLOUD_*/APP_* ports;
            data/ → /app/cloud_data)
Depends on: Caddy (two routes); Tailscale on every syncing device
Per-User:   no
Verified:   2026-10-28
```

## What it's for

The task manager: reminders, scheduling and repeating tasks, synced between the native apps on every device.

## Why this one

Donetick's UI wasn't good enough. Mindwtr was picked over tududi (which Claude leaned towards for its CalDAV reminders). It has native apps everywhere (desktop, mobile, PWA), GTD structure, separate start and due reminders, and works offline. The trade-off: reminders only fire from Mindwtr's own apps, and there's no CalDAV. Kaneo and Kanboard were rejected (no reminders or recurrence).

## How it's set up

| Container | Image | Port | Notes |
|---|---|---|---|
| `mindwtr-cloud` | `ghcr.io/dongdongbh/mindwtr-cloud:latest` | `6302 → 8787` | sync server; data in `./data`, one JSON file per token; healthcheck on `/health` |
| `mindwtr-app` | `ghcr.io/dongdongbh/mindwtr-app:latest` | `6301 → 5173` | web app; waits for the cloud to be healthy |

- Prebuilt images, so `stacks.sh update` updates them.
- **Clients:** Settings → Sync → Self-Hosted, with the sync server's base URL (`https://tasksync.example.com`; the app adds `/v1/data`) and the token from `.env`. The native app is what's used.
- Sync is last-write-wins per item: if the same task is edited on two offline devices, one edit is lost. Each device keeps a full local copy.
- Uptime Kuma checks the web app (`http://localhost:6301`) only, not the sync server.

## Known issues

- **`MINDWTR_CLOUD_CORS_ORIGIN` is still the old `https://homelab.tail0000.ts.net:6390`.** It only affects syncing from the browser app; the native apps ignore CORS. Set it to `https://task.example.com` if the browser app is ever used (follow-up 17).
- A Kuma monitor on `http://localhost:6302/health` would catch the sync server going down.

## Runbooks

- [A service's address changed](../runbooks/service-address-changed.md)

## Incidents

- [2026-08-19: browser sync blocked by CORS](../incidents/2026-08-19-mindwtr-browser-sync-blocked-by-cors.md)
