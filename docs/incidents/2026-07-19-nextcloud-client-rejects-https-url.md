# Desktop client rejected Nextcloud's HTTPS URL

- **Date:** 2026-07-19
- **Status:** resolved
- **Service:** Nextcloud
- **Runbook:** none
- **Source:** chat "Setting up home server music streaming" (2026-07-18). Unverified.

## Symptom

After Nextcloud moved to its Tailscale HTTPS URL, the desktop client refused to log in: "returned server URL does not start with HTTPS".

## Cause

Behind Tailscale's proxy, Nextcloud only sees plain HTTP from `127.0.0.1`. It thought it was being served over HTTP and handed out `http://` URLs.

## Fix

```bash
sudo docker exec -u www-data nextcloud_app php occ config:system:set overwriteprotocol --value=https
sudo docker exec -u www-data nextcloud_app php occ config:system:set overwrite.cli.url --value=https://homelab.tail0000.ts.net
sudo docker exec -u www-data nextcloud_app php occ config:system:set trusted_proxies 0 --value=127.0.0.1
```

Then restarted the app container. **Any future hostname or port change needs the same three settings checked.** As of 2026-10-28, `overwrite.cli.url` includes `:10000`, and `trusted_proxies` also holds Caddy's gateway `172.22.0.1`.
