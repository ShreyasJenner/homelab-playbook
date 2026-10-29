# Memos

```
Status:     live (since 2026-10-21)
Host:       homelab
Exposure:   tailnet-only (intended); 9418 is published on 0.0.0.0, so also reachable from the home LAN
URL:        https://journal.example.com (health: /healthz)
Config:     ~/docker/memos/ (docker-compose.yml; .env: LOCAL_PORT=9418, DRIVER, TZ; data/ → /var/opt/memos)
Depends on: Caddy
Per-User:   no; accounts alice (ADMIN) and ShreyasJenner (USER)
Verified:   2026-10-28
```

## What it's for

A quick journal: timestamped notes, browsable by day.

## Why this one

The needs were an automatic timestamp on every entry and a way to see one day's entries. Memos stamps each memo and has a calendar heatmap; clicking a day shows that day. Also considered: jrnl (CLI only), Journiv, Joplin, TriliumNext, Obsidian/Logseq and Nextcloud Notes (no per-day view).

## How it's set up

- Image `neosmemo/memos:stable` (0.31.0 on 2026-10-28), port `9418 → 5230`.
- **`MEMOS_PORT=5230`.** An app's own port setting is the port *inside* the container, so it must match the right-hand side of `ports:` ([2026-10-21](../incidents/2026-10-21-memos-connection-reset-port-mismatch.md)).
- `MEMOS_DRIVER=sqlite`. Data: `~/docker/memos/data` (`memos_prod.db` plus WAL files), owned by uid 10001. Attachments are stored on the local file system.
- **Hardening:** access mode private; in Settings → System, everything is off (no sign-ups, no public visibility). Memos has no 2FA, so it must stay off Funnel.
- Health: `/healthz` (not `/health`).
- The per-user "Export" ZIP isn't a full backup. The restic copy of `data/` is.

## Gaps

- Uptime Kuma doesn't monitor Memos.

## Runbooks

- [Connection reset after choosing or changing a port](../runbooks/connection-reset-after-port-change.md)

## Incidents

- [2026-10-21: connection reset from a port mismatch](../incidents/2026-10-21-memos-connection-reset-port-mismatch.md)
