# External storage folder was read-only

- **Date:** 2026-08-23
- **Status:** probably resolved (the fix wasn't confirmed in the chat)
- **Service:** Nextcloud (an external storage folder)
- **Runbook:** [Nextcloud can't create, move or delete files](../runbooks/nextcloud-cant-write-files.md)
- **Source:** chat "Nextcloud tailscale funnel setup" (2026-08-05 onwards). Unverified.

## Symptom

"Creating new folder failed" in an external storage folder. WebDAV returned 403 (`Sabre\DAV\Exception\Forbidden`), and PHP reported `mkdir(): Read-only file system`.

## Cause

The folder was mounted read-only into the container: either `:ro` on the compose volume, or a read-only host mount.

## Fix

Removed `:ro` from the volume and ran `docker compose up -d`. A later chat says the `mkdir` test then returned `bool(true)`, but the user never confirmed it directly.
