# Memos connection reset from a port mismatch

- **Date:** 2026-10-21
- **Status:** resolved
- **Service:** Memos
- **Runbook:** [Connection reset after choosing or changing a port](../runbooks/connection-reset-after-port-change.md)
- **Source:** chat "Self-hosted journaling software" (2026-10-21). Unverified; fix from the user and verified 2026-10-28.

## Symptom

`curl …/healthz` gave "Recv failure: Connection reset by peer", even on localhost. The container was up, and its log looked healthy.

## Cause

The compose file had `ports: "${LOCAL_PORT}:5230"` and `MEMOS_PORT: ${LOCAL_PORT}`. Memos listened on `LOCAL_PORT` inside the container, while Docker sent traffic to 5230, where nothing listened.

## Fix

Set `MEMOS_PORT` to `5230` under `environment:`, so Memos listens where Docker sends traffic. The host port stays `LOCAL_PORT` (9418). The troubleshooting artifact's version ("LOCAL_PORT consistent on both sides") is wrong.
