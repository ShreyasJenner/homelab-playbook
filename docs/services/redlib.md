# Redlib

```
Status:     live, two instances (one per User)
Host:       homelab
Exposure:   tailnet-only (intended); 8943 and 8941 are published on 0.0.0.0, so also reachable from the home LAN
URL:        https://rla.example.com (redlib-shreyas, ShreyasJenner)
            https://rlb.example.com (redlib-bob, bob)
Config:     ~/docker/redlib/ (docker-compose.yml, one .env per instance)
Depends on: a locally built image, redlib-local:latest, from the polak14 fork
Per-User:   yes
Verified:   2026-10-28
```

## What it's for

A private Reddit frontend.

## Why two instances

Redlib has no accounts. Subscriptions live in browser cookies, with defaults from `REDLIB_DEFAULT_SUBSCRIPTIONS` in `.env`. So each User gets their own container, `.env` and URL.

## Why a local build

The published image failed with "Failed to create OAuth client: expected value at line 1 column 1" (upstream issue #551). Since 2026-10-21 the image is built from `https://github.com/polak14/redlib.git#main` (v0.36.0 on 2026-10-28), a fork with a fix that upstream didn't have yet. This is meant to be temporary.

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

## Known issues (2026-10-28)

- **Both containers show "unhealthy" because the healthcheck runs `wget`, which isn't in the image.** That part is a false alarm. Fix the healthcheck (or remove it) in the compose file.
- **Reddit returns 403 Forbidden at startup** ("Rate limit check failed: Failed to parse page JSON data"), but **browsing works** (user, 2026-10-28). The startup error is noise.
- **The polak14 fork is a temporary fix.** It carries someone else's patch for the Reddit change, and the upstream `redlib-org/redlib` didn't work at the time. Once upstream has a fix, point the `build: context:` back at `https://github.com/redlib-org/redlib.git` and rebuild.

## Runbooks

- [Redlib is broken or won't update](../runbooks/redlib-broken-or-wont-update.md)

## Incidents

- [2026-09-24: OAuth client error with the published image](../incidents/2026-09-24-redlib-oauth-client-error.md)
