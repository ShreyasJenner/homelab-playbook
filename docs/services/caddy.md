# Caddy

```
Status:     live (since 2026-10-21)
Host:       homelab
Exposure:   tailnet-only (ufw allows 443 only on tailscale0)
URL:        https://<name>.example.com
Config:     ~/docker/caddy/ (docker-compose.yml, Caddyfile, data/, config/, .env)
Depends on: Tailscale (the only way in); the DNS provider's API token; each backend on localhost
Verified:   2026-10-28
```

## What it's for

The front door for every tailnet-only service. Each one gets a clean `https://<name>.example.com` address on 443, instead of `homelab.tail0000.ts.net:<port>`.

## Why this one

**Why a reverse proxy at all, rather than Tailscale Serve alone:**
- Tailscale gives a node one hostname and no subdomains.
- Path-based Serve (`--set-path`) breaks apps.
- Serve ports drifted away from the notes, with nothing to flag it.
- Bitwarden treated every port on one hostname as the same site.
- Funnel only has three ports.
- Serve commands are imperative and easy to get wrong; a proxy keeps its routes in a file.

**Why Caddy:**
- Automatic HTTPS, a tiny config, and sensible proxy headers by default.
- Caddy with a DNS-provider plugin was the best-documented way to get a wildcard certificate without opening a port.
- Nginx Proxy Manager needs a web UI and a database container. Plain nginx was never installed.

**Rejected alternatives:** a Tailscale sidecar container per service (one extra node per service), Tailscale Services (too new, needs tags and admin setup), and Caddy behind Serve with path routing.

**Why the public services don't go through Caddy:** Funnel only works on the `.ts.net` name, never on a custom domain. And funneling 443 to a proxy that fronts everything would make everything public (ADR 0004).

## How it's set up

- **Domain:** `example.com`, renews automatically. Every Caddy hostname and certificate depends on it.
- **DNS:** `*.example.com` points at the server, and only tailnet devices can reach it.
- **Certificate:** a wildcard Let's Encrypt certificate through a DNS-01 challenge (`acme_dns <provider> {env.DNS_API_TOKEN}`), so no inbound port is needed. The API token is scoped to this one zone.
- **Token:** stored in `~/docker/caddy/.env` as `DNS_TOK`. The compose file maps it with `DNS_API_TOKEN: ${DNS_TOK}`. Compose reads `.env` on every recreate, so Caddy always gets it.
- **Container:** `caddy`, `network_mode: host`, listening on `*:80` and `*:443`. ufw allows only `443/tcp on tailscale0`. The image includes the DNS provider's plugin, built with `xcaddy` from a Dockerfile (unverified, see Gaps).
- **Caddyfile:** one wildcard site block. Each service is an `@name host …` matcher plus `reverse_proxy localhost:<port>`. Unmatched hostnames are aborted. `caddy validate` passes, with a formatting warning only.

### Routes

All are `https://<host>.example.com` → `localhost:<port>`.

| Host | Port | Service |
|---|---|---|
| `drive` | 8080 | Nextcloud (plus CardDAV/CalDAV `.well-known` redirects) |
| `music` | 4533 | Navidrome |
| `task` / `tasksync` | 6301 / 6302 | Mindwtr app / Mindwtr sync server |
| `vault` | 9734 | Vaultwarden (binds `127.0.0.1` only) |
| `movies` | 8167 | Jellyfin |
| `manga` | 5000 | Kavita |
| `uptime` | 3001 | Uptime Kuma (host network) |
| `grafana` | 4710 | Grafana |
| `budget` | 5006 | Actual Budget |
| `journal` | 9418 | Memos |
| `ntfyhub` | 10230 | ntfy |
| `youtube` | 3000 | Invidious |
| `rla` / `rlb` | 8943 / 8941 | Redlib (`redlib-shreyas` / `redlib-bob`) |
| `gitea` | 8310 | Gitea web (SSH goes through Tailscale Serve) |
| `dasha` / `dashb` | 9640 / 9641 | Homepage instances a / b (host network) |

Euro-Office (`9917`) has no Caddy route. It's reached only through Funnel `:8443`.

### Adding or changing a route

```bash
cd ~/docker/caddy
# edit the Caddyfile, then:
sudo docker exec caddy caddy validate --config /etc/caddy/Caddyfile
sudo docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

A change to the compose file (volumes, env) needs `sudo docker compose up -d` instead. A new service also needs:
- its app settings (base URL, allowed hosts, CORS) changed to the new `https://<name>.example.com` address, and
- a Kuma monitor, and a Homepage entry if it's wanted there.

### Gotchas

- **The wildcard covers one label only.** `a.b.example.com` isn't covered, and falls into the `abort`.
- **Caddy only proxies HTTP(S).** Raw TCP needs the `caddy-l4` plugin, which is why Gitea SSH goes through Tailscale Serve instead.
- **A failed certificate attempt can leave a stale `_acme-challenge` TXT record** at the DNS provider that blocks the next one. See the [2026-10-21 incident](../incidents/2026-10-21-caddy-certificate-blocked-by-stale-txt-record.md).
- Back up `~/docker/caddy/data` (certificates and the ACME account). It's inside `~/docker`, so restic covers it.

## Gaps

- **How Caddy gets updated.** If the compose file uses `build: .` (the custom image), `stacks.sh update` only pulls and won't rebuild, so Caddy stays on its old version. To check: `grep -n -E 'image:|build:' ~/docker/caddy/docker-compose.yml; ls ~/docker/caddy`. If it's built, the update is `sudo docker compose build --pull && sudo docker compose up -d`.
- **Uptime Kuma doesn't check Caddy.** Every Kuma monitor uses `localhost`, so a Caddy, certificate or DNS failure wouldn't raise an alert (follow-up 11).

## Runbooks

- [A service URL returns 502 or closes the connection](../runbooks/service-url-returns-502.md)
- [Names don't resolve: MagicDNS and the host's DNS](../runbooks/names-dont-resolve.md)
- [A new container won't start or crash-loops](../runbooks/new-container-crash-loops.md)

## Incidents

- [2026-10-21: Caddy crash-looped on a Caddyfile brace error](../incidents/2026-10-21-caddy-crash-loop-caddyfile-brace.md)
- [2026-10-21: certificate blocked by a stale ACME TXT record](../incidents/2026-10-21-caddy-certificate-blocked-by-stale-txt-record.md)
