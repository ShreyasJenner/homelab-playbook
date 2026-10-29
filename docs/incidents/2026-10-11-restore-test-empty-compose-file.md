# Restore test gave an empty compose file

- **Date:** 2026-10-11
- **Status:** resolved (cause unknown; a later test worked)
- **Service:** Restic backup
- **Runbook:** [Restoring from the backup](../runbooks/restoring-from-backup.md)
- **Source:** chat "Restic backup for Docker containers" (2026-09-29 onwards). Unverified.

## Symptom

In the first restore test, into `/tmp/restore-test`, the restored `docker-compose.yml` was empty. Before that, browsing the restore as a normal user gave "permission denied", because restored files are owned by root.

## Cause

Never established. The candidates were an empty file in the snapshot, a different file name (`compose.yaml`), or `/tmp` being a small tmpfs that filled up.

## Fix

Restored to a real disk and worked as root. On 2026-10-15 a Navidrome project restored from the repo and started under another project name worked.
