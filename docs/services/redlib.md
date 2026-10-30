# Redlib

```
Status:     live, two instances (one per User)
Host:       homelab
Exposure:   tailnet-only (intended); 8943 and 8941 are published on 0.0.0.0, so also reachable from the home LAN
URL:        https://rla.example.com (redlib-shreyas, ShreyasJenner)
            https://rlb.example.com (redlib-bob, bob)
Config:     ~/docker/redlib/ (docker-compose.yml, one .env per instance)
Depends on: a locally built image, redlib-local:latest, from upstream redlib-org/redlib
Per-User:   yes
Verified:   2026-10-30
```

## What it's for

A private Reddit frontend.

## Why two instances

Redlib has no accounts. Subscriptions live in browser cookies, with defaults from `REDLIB_DEFAULT_SUBSCRIPTIONS` in `.env`. So each User gets their own container, `.env` and URL.

## Why a local build

The published image failed with "Failed to create OAuth client: expected value at line 1 column 1" (upstream issue #551). From 2026-10-21 the image was built from the polak14 fork, which had a fix upstream didn't have yet.

Since 2026-10-30 it's built from upstream again, `https://github.com/redlib-org/redlib.git#main` (v0.40.0). The published `quay.io/redlib/redlib:latest` is the same commit, so the local build may no longer be needed (follow-up 33).

## How it's set up

- One compose file. A YAML anchor (`x-redlib-common`) shares `image: redlib-local:latest`, `user: nobody`, `read_only`, `no-new-privileges` and `cap_drop: ALL`.
- `redlib-shreyas` has `pull_policy: build` and the `build:` context; `redlib-bob` has `pull_policy: never` and reuses the image.
- Host ports `8943` and `8941` → `8080`, from `.env` (`HOST_PORT_A`, `HOST_PORT_B`).

### Updating

Never `docker compose pull`: the image only exists locally.

```bash
cd ~/docker/redlib
sudo docker compose build --no-cache          # only the instance with build: has anything to build
sudo docker compose up -d --force-recreate
sudo docker compose logs --tail 20 | grep -i -E 'oauth|error'
```

`stacks.sh update` includes `redlib`, and `pull` on it fails or skips. "Instance is at least 20 commits old" is a false alarm when the image is built from a git URL.

## Known issues (2026-10-30)

- **Reddit refuses the home IP** (2026-10-30, open): every page fails with 403s, on any Redlib version and from any machine at home. See the incident below.
- **Both containers show "unhealthy" because the healthcheck runs `wget`, which isn't in the image.** That part is a false alarm. Fix the healthcheck (or remove it) in the compose file.
- **Reddit returns 403 Forbidden at startup** ("Rate limit check failed: Failed to parse page JSON data"), even when browsing works (user, 2026-10-28). The startup error alone is noise.

## Runbooks

- [Redlib is broken or won't update](../runbooks/redlib-broken-or-wont-update.md)

## Incidents

- [2026-09-24: OAuth client error with the published image](../incidents/2026-09-24-redlib-oauth-client-error.md)
- [2026-10-30: Reddit refuses the home IP](../incidents/2026-10-30-redlib-reddit-blocks-home-ip.md) (open)
