# Couldn't create folders in new external storage

- **Date:** 2026-09-02
- **Status:** resolved
- **Service:** Nextcloud (a newly added external storage folder)
- **Runbook:** [Nextcloud can't create, move or delete files](../runbooks/nextcloud-cant-write-files.md)
- **Source:** chat "Nextcloud external storage file editing issue" (2026-09-02). Unverified; fix from the user (2026-10-28).

## Symptom

A new external folder could be read, but creating anything in it failed: the PHP `mkdir` test returned `bool(false)`, "permission denied".

## Cause

The folder belonged to `alice` (uid 1000), and "other" only had read and execute. Nextcloud writes as `www-data` (uid 33).

## Fix

The user applied both `o+w` and a shared group on the external storage folders, and doesn't know which one made it work. The runbook has both commands. To see what's in place now: `stat` and `getfacl` on the folder.
