# ntfy

```
Status:     live (since 2026-08-30)
Host:       homelab
Exposure:   tailnet-only (but published on 0.0.0.0:10230, so the home LAN reaches it too; see the LAN incident)
URL:        https://ntfyhub.example.com (health: /v1/health)
Config:     ~/docker/ntfy/ (docker-compose.yml; .env with every NTFY_* setting; cache/cache.db; lib/user.db)
Secrets:    NTFY_AUTH_USERS in ~/docker/ntfy/.env (user:bcrypt-hash:role, written <NTFY_AUTH_USERS>)
Depends on: Caddy (route); Tailscale on the phone; ntfy.sh as the iOS push relay
Per-User:   no; only ShreyasJenner subscribes
Verified:   2026-10-28
```

## What it's for

Push notifications to the iPhone. Today the only sender is [Uptime Kuma](uptime-kuma.md): "Kuma Alert" publishes when a monitor goes down or comes back. bob gets no alerts; they're a User, not an operator.

## Why this one

Self-hostable, with an iOS app, and Uptime Kuma has a built-in provider for it. It was the first suggestion when Kuma needed a notification target. Gotify and Pushover weren't compared.

## How it's set up

- Image `binwiederhier/ntfy` (no tag, so latest), `command: serve`, network `ntfy_default`, port `10230 → 80`, runs as `1000:1000`, `TZ=Etc/UTC`. Healthcheck on `/v1/health`.
- **All config is in `.env`** (no `server.yml`). The values that matter (2026-10-28):

  | Variable | Value | Why |
  |---|---|---|
  | `NTFY_BASE_URL` | `https://ntfyhub.example.com` | links and the iOS app use it |
  | `NTFY_UPSTREAM_BASE_URL` | `https://ntfy.sh` | needed for instant push on iOS (see below) |
  | `NTFY_LISTEN_HTTP` | `:80` | the colon matters ([2026-08-30 incident](../incidents/2026-08-30-ntfy-listen-address-missing-colon.md)) |
  | `NTFY_BEHIND_PROXY` | `true` | behind Caddy |
  | `NTFY_AUTH_DEFAULT_ACCESS` | `deny-all` | anonymous can't read or publish anything |
  | `NTFY_AUTH_USERS` | `<NTFY_AUTH_USERS>` | declares `alice` (role admin). Comma-separated; every `$` in the bcrypt hash written as `$$` |
  | `NTFY_CACHE_FILE` | `/var/cache/ntfy/cache.db` | host: `~/docker/ntfy/cache/cache.db` |
  | `NTFY_CACHE_DURATION` | `12h` | messages older than this are gone |

- **Users:** only `alice`, declared in `.env`. `.env` holds just its bcrypt hash; the plaintext password is in Vaultwarden. Uptime Kuma logs in with it or with a token, stored in Kuma's notification settings.
- **Data:** `cache/` is disposable. `lib/user.db` holds users and tokens. Both are bind mounts inside `~/docker`, so restic backs them up.

### The phone

- The ntfy iOS app has `https://ntfyhub.example.com` added as a server, logged in as the ntfy user, and subscribed to Kuma's topic.
- **Alerts arrive only while the phone is on the tailnet** (tested 2026-10-28: a test message arrives with Tailscale on, and nothing happens with it off). That's accepted: under [ADR 0004](../adr/0004-tailnet-by-default-funnel-for-documents.md), Funnel is for document sharing only.
- **Why `ntfy.sh` is involved:** iOS only delivers pushes through Apple's service, which a self-hosted server can't use directly. With `NTFY_UPSTREAM_BASE_URL` set, the server sends ntfy.sh a "poll request" (per the ntfy docs, it carries the message ID, not the text), ntfy.sh wakes the app through Apple, and the app then fetches the message from `ntfyhub.example.com`. That fetch is the step that needs Tailscale.

### Sending a test message

From the host:

```bash
curl -u alice:<NTFY_ADMIN_PASSWORD> -d "test" https://ntfyhub.example.com/<KUMA_TOPIC>
```

Or press **Test** on the "Kuma Alert" notification in Uptime Kuma, which also checks Kuma's stored credentials. Never paste the output of `ntfy token list` anywhere: it prints the tokens.

## Known gaps

- **Reachable from the home LAN** on `198.51.100.10:10230` (tested 2026-10-28), like every Docker-published port. Anonymous access is `deny-all`, so it's less serious than the unauthenticated monitoring ports. See the open [LAN-exposure incident](../incidents/2026-10-28-services-reachable-from-home-lan.md).
- **Not monitored itself.** If ntfy is down, Kuma's alerts fail silently. A Kuma monitor on `http://localhost:10230/v1/health` would at least show it red on the dashboard.
- Image untagged, so `stacks.sh update` follows every release.

## Runbooks

- [An Uptime Kuma alert is wrong or didn't arrive](../runbooks/uptime-kuma-alert-wrong-or-missing.md)
- [A new container won't start or crash-loops](../runbooks/new-container-crash-loops.md)
- [Updating containers](../runbooks/updating-containers.md)

## Incidents

- [2026-08-30: `auth-users` type mismatch in `server.yml`](../incidents/2026-08-30-ntfy-auth-users-type-mismatch.md)
- [2026-08-30: listen address missing its colon](../incidents/2026-08-30-ntfy-listen-address-missing-colon.md)
