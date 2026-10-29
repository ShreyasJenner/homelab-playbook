# Nextcloud's files consumed by Paperless-ngx

- **Date:** 2026-10-02
- **Status:** resolved (how complete the recovery was isn't recorded)
- **Service:** Nextcloud (and Paperless-ngx, since retired)
- **Runbook:** none
- **Source:** chat "Paperless NGX docker compose setup" (2026-10-02). Unverified.

## Symptom

"All the files in my nextcloud are missing."

## Cause

Paperless-ngx's consume folder was bind-mounted onto a folder inside Nextcloud's data directory. Paperless deletes every file it consumes, so it ingested and removed Nextcloud's files. **No backup was running at the time.**

## Fix (recovery)

1. Stopped Paperless.
2. **Didn't run `occ files:scan`.** A scan would have purged Nextcloud's file cache, which still listed every file's path, name and size.
3. Dumped the database (`mysqldump`) before touching anything.
4. Exported the originals from Paperless (`document_exporter`).
5. Rebuilt the folder tree by matching the exported files to a read-only `SELECT` on `oc_filecache`, by name and size.

## Lessons

- Never point another service at a folder inside Nextcloud's data directory. Give it its own folder, and add that to Nextcloud as external storage if it's needed there.
- Nightly restic backups of `~/docker` (which includes Nextcloud's data) started later, so a repeat could now be restored from a snapshot.
