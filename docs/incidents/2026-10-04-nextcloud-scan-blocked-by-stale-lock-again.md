# files:scan blocked by a stale lock again

- **Date:** 2026-10-04
- **Status:** resolved
- **Service:** Nextcloud
- **Runbook:** [`occ files:scan` says another process is already scanning](../runbooks/nextcloud-scan-already-running.md)
- **Source:** chat "Nextcloud files scan lock issue" (2026-10-04). Unverified; fix from the user (2026-10-28).

## Symptom

`occ files:scan --all` stopped at the last user: "Starting scan for user 3 out of 3 (alice) / Another process is already scanning '/alice'".

## Cause

A stale database lock, the same as on [2026-09-28](2026-09-28-nextcloud-scan-blocked-by-stale-lock.md). This second occurrence is why it has a runbook.

## Fix

Cleared `oc_file_locks`, restarted the container, and scanned again. Redis for file locking was suggested as prevention, and hasn't been added.
