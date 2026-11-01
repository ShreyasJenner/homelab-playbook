# Uptime Kuma

```
Status:     live (since about 2026-08-19)
Host:       homelab
Exposure:   tailnet-only (host network on *:3001; ufw filters it, so the home LAN can't reach it)
URL:        https://uptime.example.com (302 to /dashboard is normal)
Config:     ~/docker/uptime-kuma/ (docker-compose.yml; data/ → /app/data: kuma.db holds monitors,
            notifications and their credentials)
Depends on: ntfy (alerts); Caddy (route); Tailscale
Per-User:   no; only ShreyasJenner gets alerts
Verified:   2026-10-28
```

## What it's for

The monitoring that's actually relied on. It checks every minute that each service answers, and sends a push to the iPhone through [ntfy](ntfy.md) when one goes down or comes back. The [monitoring stack](monitoring.md) (Grafana and friends) answers "how is it doing?"; Kuma answers "is it up?".

## Why this one

It was the cheapest first step when monitoring was added (August 2026): one container, a web UI, many notification providers. No alternative was compared.

## How it's set up

- Image `louislam/uptime-kuma:2`, `network_mode: host`, listens on `3001`. `restart: always`. Its compose sets its own log limit (3 × 10 MB).
- **Why host network:** in a bridge network, `localhost` is Kuma's own container, so it couldn't probe services on their host ports, and `host.docker.internal` tripped Nextcloud's `trusted_domains`. Changing Nextcloud was ruled out, so Kuma moved to the host network instead ([2026-08-19 incident](../incidents/2026-08-19-uptime-kuma-nextcloud-false-down.md)). A side effect: it isn't a Docker-published port, so ufw filters it, and it's **not** reachable from the home LAN (tested 2026-10-28).
- **Data** is a bind mount, `~/docker/uptime-kuma/data`, so restic backs it up (a cold copy at 02:30).

### Monitors (2026-10-28)

All HTTP, all every 60 s, all against `localhost`, all with the "Kuma Alert" ntfy notification.

| Monitor | URL |
|---|---|
| Nextcloud | `http://localhost:8080/status.php` |
| Navidrome | `http://localhost:4533/ping` |
| Kavita | `http://localhost:5000/api/health` |
| Mindwtr | `http://localhost:6301` |
| Actual Budget | `http://localhost:5006/health` |
| Jellyfin | `http://localhost:8167/health` |
| Vaultwarden | `http://localhost:9734/alive` |
| Healthcheck | `<HEALTHCHECKS_PING_URL>` (an `hc-ping.com` URL) |

- **"Healthcheck"** is a dead-man's switch. Kuma pings healthchecks.io, and if the pings stop (the host, Kuma or the home internet is down), healthchecks.io **emails** the user. It's the one alert that needs neither ntfy nor Tailscale. Kuma pings every 60 s (`kuma.db`, 2026-10-28). Per the user, healthchecks.io waits through 2 more missed 3-minute periods before it mails, so the nightly 3–4 minute backup stop doesn't set it off. The 3 minutes is presumably the period set on healthchecks.io; check there before relying on the exact timing. On 2026-11-01 the "down" email came at 02:40, only about 3 minutes after Kuma stopped (02:37:16), which suggests a shorter grace than that (follow-up 41). **A long backup does set it off:** the email then means the stacks are still stopped for the backup, not that the host is down ([incident](../incidents/2026-11-01-backup-downtime-after-hardlink-conversion.md)). The ping URL is a credential; the real value is in the monitor's settings in Kuma (`kuma.db`).
- There's also an empty **"Homelab"** group (URL placeholder `https://`).

**Adding a monitor:** use the service's health endpoint on its host port, not `/` (which often redirects to a login page). Known endpoints for services not yet monitored: Memos `/healthz` (9418), ntfy `/v1/health` (10230), Euro-Office `/healthcheck` (9917). For others, the image's Dockerfile `HEALTHCHECK` usually names one. Then tick "Kuma Alert" under Notifications. It isn't the default, so a new monitor has **no alert until you tick it**. (On 2026-10-28 Vaultwarden turned out to be unticked, and was fixed.)

### Alerts

One notification provider, **"Kuma Alert"** (type ntfy), publishes to the ntfy server at `https://ntfyhub.example.com`. Its topic and credentials are in Kuma's notification settings (stored in `kuma.db`). Never query the `notification.config` column: it holds them in plain text. The ntfy page covers the phone side.

## Known gaps

- **It only checks `localhost`** (follow-up 11). A broken Caddy route, an expired certificate, or Tailscale or DNS failures all leave every monitor green. And Gitea, Memos, Homepage, Euro-Office, Redlib, Invidious, ntfy itself and the monitoring stack aren't monitored at all. Consider monitors on the real `https://<name>.example.com` URLs (the host can reach them).
- **Nothing is checked from 02:30 to about 02:34** every night, or until the backup finishes when it runs long. The backup stops Kuma and ntfy along with everything else. Nothing is caught in that window, and a long backup sets off the healthchecks.io email.
- **Backup failures don't reach Kuma** (follow-up 28).

## Runbooks

- [An Uptime Kuma alert is wrong or didn't arrive](../runbooks/uptime-kuma-alert-wrong-or-missing.md)
- [Updating containers](../runbooks/updating-containers.md)

## Incidents

- [2026-08-19: Nextcloud monitor down although Nextcloud worked](../incidents/2026-08-19-uptime-kuma-nextcloud-false-down.md)
- [2026-11-01: healthcheck "down" for 1 h 12 min while the backup ran](../incidents/2026-11-01-backup-downtime-after-hardlink-conversion.md)
