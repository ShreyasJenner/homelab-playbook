# rclone sync to B2 denied

- **Date:** 2026-10-22
- **Status:** resolved
- **Service:** Restic backup (offsite copy)
- **Runbook:** [The nightly backup failed](../runbooks/backup-failed.md)
- **Source:** chat "Restic backup to OneDrive" (2026-10-22). Unverified; the working setup is verified 2026-10-28.

## Symptom

The first manual `rclone sync` reported "Errors: 2" and transferred nothing; the log said `open /mnt/backup-hdd/restic-repo: permission denied`. The first attempt also tried to copy `lost+found`.

## Cause

rclone ran as the normal user, but the restic repo is readable only by root. The first attempt also used the disk's root instead of the repo folder as the source.

## Fix

Run rclone as root, with the user's config passed explicitly, and the repo folder as the source:

```bash
sudo rclone sync /mnt/backup-hdd/restic-repo backblaze:restic-backups --config /home/alice/.config/rclone/rclone.conf
```

That's what the script does. The same night OneDrive turned out to be too small, and the offsite copy moved to B2.
