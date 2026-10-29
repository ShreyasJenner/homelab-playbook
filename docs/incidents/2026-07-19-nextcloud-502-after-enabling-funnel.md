# Nextcloud 502 after turning on Funnel

- **Date:** 2026-07-19
- **Status:** resolved
- **Service:** Nextcloud
- **Runbook:** [A service URL returns 502 or closes the connection](../runbooks/service-url-returns-502.md)
- **Source:** chat "Setting up home server music streaming" (2026-07-18). Unverified.

## Symptom

Nextcloud returned 502 Bad Gateway straight after Funnel was turned on to make it public.

## Cause

The Funnel `:443` handler proxied to `http://127.0.0.1:443` instead of Nextcloud on `localhost:8080`. A bare-number `funnel` command had replaced the target.

## Fix

```bash
sudo tailscale serve --bg --https=443 http://localhost:8080
```

Nextcloud worked again. (Nextcloud has been on Funnel `:10000` since 2026-10-21, when Caddy took 443.)
