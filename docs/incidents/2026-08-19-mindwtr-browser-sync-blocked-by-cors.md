# Mindwtr browser sync blocked by CORS

- **Date:** 2026-08-19
- **Status:** resolved at the time; the setting is stale again (see below)
- **Service:** Mindwtr
- **Runbook:** [A service's address changed](../runbooks/service-address-changed.md)
- **Source:** chat "Comparing Mindwtr and tududi task managers" (2026-08-17 onwards). Unverified.

## Symptom

Syncing from the browser app failed on tailnet devices, and only worked on the server itself.

## Cause

`MINDWTR_CLOUD_CORS_ORIGIN` was `http://localhost:5173`. The sync server allows exactly one origin, so browsers loading the app from any other address were refused.

## Fix

Set it to the web app's exact HTTPS address at the time, then `docker compose up -d`.

On 2026-10-28 it's `https://homelab.tail0000.ts.net:6390`, an address that's gone since the move to Caddy. It doesn't matter today because sync runs through the native app, which ignores CORS. If the browser app is used again, set it to `https://task.example.com` (follow-up 17).
