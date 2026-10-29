# Couldn't move or delete files in external storage

- **Date:** 2026-09-30
- **Status:** probably resolved (no reply in the chat)
- **Service:** Nextcloud (external storage)
- **Runbook:** [Nextcloud can't create, move or delete files](../runbooks/nextcloud-cant-write-files.md)
- **Source:** chat "Nextcloud file permission issue" (2026-09-30). Unverified.

## Symptom

Some files in an external storage folder, owned by `www-data`, couldn't be moved or deleted.

## Cause (probable)

Moving or deleting a file needs write permission on its **parent folder**, not on the file. The parent belonged to uid 1000 without write access for uid 33 (or the mount was read-only).

## Fix

Not recorded for this occurrence. The external storage folders later got `o+w` and a shared group (see [2026-09-02](2026-09-02-nextcloud-external-storage-permission-denied.md)), followed by `occ files:scan --all`.
