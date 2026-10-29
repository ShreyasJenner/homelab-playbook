# Gitea down after `app.ini` edits

- **Date:** 2026-10-24
- **Status:** resolved (the exact fix isn't recorded)
- **Service:** Gitea
- **Runbook:** [Connection reset after choosing or changing a port](../runbooks/connection-reset-after-port-change.md)
- **Source:** chat "Gitea SSH clone URL" (2026-10-24). Unverified; end state verified 2026-10-28.

## Symptom

Trying to change the clone URL from `git@localhost` to `git@gitea` took the web UI down. The log showed `Listen: http://0.0.0.0:8310gitea.example.com` and `AppURL(ROOT_URL): gitea.example.com/`.

## Cause

- `HTTP_PORT` had been set to the host port (8310), while compose maps `8310:3000`, so nothing listened on 3000.
- `ROOT_URL` was set without a scheme.
- These had been passed as env vars, and Gitea writes env settings into `app.ini`, so removing them from compose didn't undo them.

## Fix

Edited `app.ini` and restarted. On 2026-10-28 it has `HTTP_PORT = 3000`, `DOMAIN = gitea` and `ROOT_URL = https://gitea`. The last one is still wrong behind Caddy (follow-up 18).
