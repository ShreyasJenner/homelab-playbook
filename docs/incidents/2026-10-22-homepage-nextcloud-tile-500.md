# Homepage: Nextcloud tile showed 500

- **Date:** 2026-10-22
- **Status:** resolved (the fix is in place on 2026-10-28)
- **Service:** Homepage, Nextcloud
- **Runbook:** [Homepage is blank, or a tile is red](../runbooks/homepage-blank-or-tile-red.md)
- **Source:** chat "Homepage dashboard via Docker" (2026-10-22). Unverified; end state verified 2026-10-28.

## Symptom

Nextcloud's tile showed 500, although Nextcloud worked in the browser.

## Cause

`siteMonitor: http://localhost:8080` checks Nextcloud's front page, which returns an error to a plain request. Nextcloud's health endpoint is `status.php`.

## Fix

`siteMonitor: http://localhost:8080/status.php`, in both `config_a` and `config_b`.
