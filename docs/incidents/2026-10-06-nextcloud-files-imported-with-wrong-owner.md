# Imported files had the wrong owner

- **Date:** 2026-10-06
- **Status:** resolved
- **Service:** Nextcloud
- **Runbook:** [Nextcloud can't create, move or delete files](../runbooks/nextcloud-cant-write-files.md)
- **Source:** chat "Nextcloud desktop logs location" (2026-10-06). Unverified.

## Symptom

The desktop client couldn't move files: "you don't have access to this resource" (403).

## Cause

"It was a user ownership issue." The files had been copied into the container with `docker cp`, which kept the wrong owner instead of `www-data`.

## Fix

Changed the files' owner to `www-data`. The bulk import steps on the [Nextcloud page](../services/nextcloud.md#day-to-day-commands) now include the `chown`.
