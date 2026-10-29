# Invidious

```
Status:     live (since 2026-09-23), used seldom
Host:       homelab
Exposure:   tailnet-only (intended); 3000 is published on 0.0.0.0, so also reachable from the home LAN.
            The companion binds 127.0.0.1:8282 only.
URL:        https://youtube.example.com
Config:     ~/docker/invidious/ (docker-compose.yml, .env, config/sql, docker/init-invidious-db.sh)
Depends on: invidious-db (Postgres 14, named volume invidious_postgresdata); invidious-companion;
            the hourly restart timer
Per-User:   no; one instance, an account per person
Verified:   2026-10-28
```

## What it's for

A private YouTube frontend, in the browser. The iOS app Yattee can use it too.

## How it's set up

**Three containers:**

| Container | Image | Notes |
|---|---|---|
| `invidious-invidious-1` | `quay.io/invidious/invidious:latest` | port 3000; its healthcheck calls `/api/v1/stats` |
| `invidious-companion-1` | `quay.io/invidious/invidious-companion:latest` | `127.0.0.1:8282`; volume `invidious_companioncache`; `read_only`, `cap_drop: ALL` |
| `invidious-invidious-db-1` | `postgres:14` | **named volume `invidious_postgresdata`** |

**Config in compose** (secrets come from `.env`):
- `domain: ${DOMAIN}`, `https_only: true`, `registration_enabled: true`, `popular_enabled: true`
- Companion: `private_url: http://companion:8282/companion`, `public_url: https://youtube.example.com/companion`
- `hmac_key` and the companion key (`SERVER_SECRET_KEY` must equal `invidious_companion_key`, exactly 16 characters) are in `.env`.

**The database service must take its user and password from the same `.env` variables as `INVIDIOUS_CONFIG`.** Upstream's example file hard-codes its own ([2026-09-23](../incidents/2026-09-23-invidious-database-login-failed.md)). Postgres reads `POSTGRES_*` only when it first initialises; changing them later needs a new volume.

**Hourly restart:** upstream says Invidious degrades over time and should be restarted at least daily. `invidous-restart.timer` (spelled that way) runs `invidous-restart.service` every hour, which restarts the `invidious` container. Check it with `systemctl list-timers | grep invid`.

## Known gaps

- **The database isn't backed up.** It's a named volume in `/var/lib/docker/volumes`, outside `~/docker`, so restic doesn't see it. Losing it loses accounts and subscriptions. The fixes are a bind mount under `~/docker/invidious`, or a `pg_dump` before the backup.
- **`public_url` points at `youtube.example.com/companion`, but Caddy sends that hostname only to port 3000.** If playback ever depends on the public companion URL, it won't reach the companion. Playback hasn't been reported broken.
- **Registration is open** to anyone who can reach it (the tailnet, and the LAN until the exposure fix). It was meant to be open only while creating accounts.
- `popular_enabled: true` mixes everyone's subscriptions into one "Popular" feed. Use each account's Subscriptions feed instead.
- Uptime Kuma doesn't monitor it.

## Incidents

- [2026-09-23: database login failed](../incidents/2026-09-23-invidious-database-login-failed.md)
