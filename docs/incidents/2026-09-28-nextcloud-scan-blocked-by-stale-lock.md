# files:scan blocked by a stale lock

- **Date:** 2026-09-28
- **Status:** resolved
- **Service:** Nextcloud
- **Runbook:** [`occ files:scan` says another process is already scanning](../runbooks/nextcloud-scan-already-running.md)
- **Source:** chat "Nextcloud files scan process lock" (2026-09-28). Unverified; fix from the user (2026-10-28).

## Symptom

`occ files:scan` refused to run: "Another process is already scanning".

## Cause

A stale file lock left in the database by an interrupted scan. Nextcloud has no Redis here, so it uses database locking.

## Fix

Cleared the locks with `DELETE FROM oc_file_locks WHERE 1;` in `nextcloud_db`, restarted the container, and scanned again.
