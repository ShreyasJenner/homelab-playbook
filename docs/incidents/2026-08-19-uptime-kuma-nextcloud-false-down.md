# Nextcloud monitor down although Nextcloud worked

- **Date:** 2026-08-19
- **Status:** resolved
- **Service:** Uptime Kuma (the Nextcloud monitor)
- **Runbook:** [An Uptime Kuma alert is wrong or didn't arrive](../runbooks/uptime-kuma-alert-wrong-or-missing.md)
- **Source:** chat "Uptime Kuma Nextcloud monitoring issue" (2026-08-19). Unverified; the end state was verified on 2026-10-28.

## Symptom

Kuma showed Nextcloud DOWN, while `curl http://localhost:8080/login` on the host returned 200. `/` returned a 302. Pointing the monitor at `host.docker.internal:8080/status.php` instead gave a Nextcloud trusted-domain error.

## Cause

Kuma ran in a bridge network, so `localhost` inside it was Kuma's own container, not the host. `host.docker.internal` reached the host, but Nextcloud refuses any host name that isn't in `trusted_domains`.

## Fix

Kuma was moved to `network_mode: host` rather than adding a name to Nextcloud's `trusted_domains`. The monitor checks `http://localhost:8080/status.php`. Verified 2026-10-28: Kuma is on the host network, and that is the monitor's URL.
