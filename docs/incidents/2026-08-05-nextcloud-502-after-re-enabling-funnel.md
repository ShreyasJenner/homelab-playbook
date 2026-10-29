# Nextcloud 502 after re-enabling Funnel

- **Date:** 2026-08-05
- **Status:** resolved
- **Service:** Nextcloud
- **Runbook:** [A service URL returns 502 or closes the connection](../runbooks/service-url-returns-502.md)
- **Source:** chat "Nextcloud tailscale funnel setup" (2026-08-05). Unverified.

## Symptom

Nextcloud returned 502 after Funnel was turned back on.

## Cause

`tailscale funnel --bg 443` with a bare number means "funnel 443 to `localhost:443`". It reset Nextcloud's target to `127.0.0.1:443`. This is the same mistake as on [2026-07-19](2026-07-19-nextcloud-502-after-enabling-funnel.md).

## Fix

```bash
sudo tailscale funnel --bg --https=443 http://localhost:8080
```

Lesson: always give `funnel` both `--https=<port>` and the target.
