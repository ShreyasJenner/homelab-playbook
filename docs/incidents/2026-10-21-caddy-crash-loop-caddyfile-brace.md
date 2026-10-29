# Caddy crash-looped on a Caddyfile brace error

- **Date:** 2026-10-21
- **Status:** resolved
- **Service:** Caddy
- **Runbook:** none
- **Source:** chat "Port allocation on self-hosted servers" (2026-10-21). Unverified.

## Symptom

During the Caddy setup, the `caddy` container kept restarting (exit 1).

## Cause

A misplaced brace in the Caddyfile. Caddy's error said it "parsed 'handle' as a site address".

## Fix

Fixed the braces and checked the file before restarting:

```bash
sudo docker exec caddy caddy validate --config /etc/caddy/Caddyfile
```

Lesson: always `caddy validate` before `caddy reload`. A bad Caddyfile takes down every tailnet-only service at once.
