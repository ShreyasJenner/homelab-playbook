# ntfy listen address missing its colon

- **Date:** 2026-08-30
- **Status:** resolved
- **Service:** ntfy
- **Runbook:** [A new container won't start or crash-loops](../runbooks/new-container-crash-loops.md)
- **Source:** chat "Setting up ntfy in Docker" (2026-08-30). Unverified; the end state was verified on 2026-10-28.

## Symptom

ntfy exited at startup: `FATAL listen tcp: address 80: missing port in address`.

## Cause

Probably `NTFY_LISTEN_HTTP=80`. ntfy expects a Go listen address, `[host]:port`, so a bare `80` isn't valid. The chat ends before the fix was confirmed.

## Fix

`NTFY_LISTEN_HTTP=:80`, then `docker compose up -d`. Verified 2026-10-28: that's the live value, and ntfy is healthy.
