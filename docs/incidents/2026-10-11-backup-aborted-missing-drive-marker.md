# Backup aborted: drive marker missing

- **Date:** 2026-10-11
- **Status:** resolved
- **Service:** Restic backup
- **Runbook:** [The nightly backup failed](../runbooks/backup-failed.md)
- **Source:** chat "Restic backup for Docker containers" (2026-09-29 onwards). Unverified.

## Symptom

The script stopped with "backup drive not mounted. Aborting", although `findmnt` showed the disk mounted.

## Cause

The script checks two things, that the disk is mounted *and* that it has the marker file `.backup-drive`, but prints one message for both. The marker had never been created.

## Fix

`sudo touch /mnt/backup-hdd/.backup-drive`. Splitting the check into two messages was suggested; the live script (2026-10-28) still has the combined one.
