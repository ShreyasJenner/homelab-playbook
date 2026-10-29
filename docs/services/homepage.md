# Homepage

```
Status:     live (since 2026-10-22; two instances since 2026-10-24)
Host:       homelab
Exposure:   tailnet-only (host network, so ufw filters it; not reachable from the LAN, user-tested)
URL:        https://dasha.example.com (ShreyasJenner), https://dashb.example.com (bob)
Config:     ~/docker/homepage/ (docker-compose.yml, .env; config_a/ and config_b/ → /app/config:
            services.yaml, settings.yaml, widgets.yaml, bookmarks.yaml)
Depends on: Caddy (routes); the services it links to
Per-User:   yes: config_a for ShreyasJenner, config_b for bob
Verified:   2026-10-28
```

## What it's for

One bookmark per person: a dashboard with a tile for every service they use, with a status dot for each.

## Why this one

It came out of the Authentik dead end (2026-10-11). The wish was "a sort of homepage that will store the credentials for all my services". That splits into a password manager ([Vaultwarden](vaultwarden.md)) and a dashboard. Homepage is configured in plain YAML and doesn't need the Docker socket, which would be root-equivalent.

## How it's set up

- Image `ghcr.io/gethomepage/homepage:latest`, `network_mode: host`, one compose project with two services. The containers are **`homepage-homepage-a-1`** and **`homepage-homepage-b-1`**.
- A YAML anchor holds the shared settings, and a second anchor holds `PUID`/`PGID`/`TZ`, merged into each service's `environment`. Don't put `container_name` in a shared anchor, and remember `<<:` is a shallow merge.

| | Instance a | Instance b |
|---|---|---|
| `PORT` (host network, so this is the host port) | 9640 | 9641 |
| `HOMEPAGE_ALLOWED_HOSTS` | `dasha.example.com` | `dashb.example.com` |
| Config | `config_a/` | `config_b/` |
| Tiles | Grafana, Uptime Kuma, ntfy, Nextcloud, Mindwtr, Actual Budget, Memos, Gitea, Navidrome, Jellyfin, Invidious, Redlib (rla) | Nextcloud, Gitea, Navidrome, Jellyfin, Invidious, Kavita, Redlib (rlb) |

- Every tile's `href` is `https://<name>.example.com`, and every `siteMonitor` is `http://localhost:<port>`. Because Homepage is on the host network, it checks the same ports Caddy uses. Nextcloud's monitor uses `/status.php`, because `/` returns 500 to a check.
- No widgets, so no API keys in the config.
- YAML edits apply on a page refresh. Compose or `.env` changes need `sudo docker compose up -d`.
- `services.yaml` layout: groups at column 0, services indented 4 spaces, fields 8. Spaces only.

## Gaps

- Uptime Kuma doesn't monitor Homepage. A crashed instance is noticed only when someone opens it.

## Runbooks

- [Homepage is blank, or a tile is red](../runbooks/homepage-blank-or-tile-red.md)
- [A service's address changed](../runbooks/service-address-changed.md)
- [Connection reset after choosing or changing a port](../runbooks/connection-reset-after-port-change.md)

## Incidents

- [2026-10-22: Homepage couldn't bind port 3000](../incidents/2026-10-22-homepage-port-3000-in-use.md)
- [2026-10-22: blank page from a YAML indentation error](../incidents/2026-10-22-homepage-blank-yaml-indentation.md)
- [2026-10-22: Nextcloud tile showed 500](../incidents/2026-10-22-homepage-nextcloud-tile-500.md)
