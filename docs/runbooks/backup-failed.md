# The nightly backup failed

Nothing alerts on a failed run yet, so this usually starts from a manual check. If the run succeeded but kept the services down for a long time, see [The nightly backup took long](backup-took-long.md).

## Symptom

- `systemctl status restic-docker-backup.service` shows "failed", or the last journal lines don't end in "Backup finished (exit 0)".
- No new snapshot for today.
- B2 hasn't changed.

## Check

```bash
systemctl list-timers restic-docker-backup.timer --no-pager
systemctl status restic-docker-backup.service --no-pager | head -8
sudo journalctl -u restic-docker-backup.service --since -1d --no-pager | grep -E '\[20|ERROR|WARNING|error' | tail -20
findmnt /mnt/backup-hdd; ls -la /mnt/backup-hdd/.backup-drive
R="sudo restic -r /mnt/backup-hdd/restic-repo --password-file /root/.config/restic/password"
$R snapshots --compact | tail -3
sudo docker ps -a --filter status=exited --format '{{.Names}}'     # did every container come back?
```

## Likely causes

| Log line | Cause |
|---|---|
| `ERROR: backup drive not mounted. Aborting; containers untouched.` | The backup disk isn't mounted, **or the `.backup-drive` marker is missing**. One message covers both. |
| `ERROR: restic backup failed (exit N)` | Restic itself failed: a stale lock after a power cut, a full disk, or a repo problem. |
| `ERROR: restic check failed; NOT mirroring to B2` | The local repo has an error. B2 is deliberately left untouched. |
| `ERROR: B2 sync failed` | rclone couldn't reach B2, or the key or config is wrong. |
| `WARNING: previous B2 sync still running` | The last sync was still uploading (not a failure). |
| `WARNING: failed to start <dir>` | A project didn't come back up after the backup. |

## Fix

- **Disk or marker:** `sudo mount /mnt/backup-hdd`; if the marker is missing on the right disk, `sudo touch /mnt/backup-hdd/.backup-drive`.
- **Stale lock** (after a crash or power cut): `$R unlock`, then run again.
- **Check failed:** `$R check` for details. Don't sync to B2 until it's fixed, because B2 is the good copy.
- **B2 sync:** run rclone as root, with the config:
  ```bash
  sudo rclone --config /home/alice/.config/rclone/rclone.conf lsd backblaze:
  ```
  rclone as a normal user gets "permission denied", because the repo is root-only.
- **A project didn't restart:** `cd ~/docker/<stack> && sudo docker compose up -d`.

Run the whole backup again by hand:

```bash
sudo systemctl start restic-docker-backup.service
journalctl -u restic-docker-backup.service -f
```

## Verify

The journal ends with "Backup finished (exit 0)", and `$R snapshots --compact | tail -1` shows today.

## Related incidents

- [2026-10-11: backup aborted, drive marker missing](../incidents/2026-10-11-backup-aborted-missing-drive-marker.md)
- [2026-10-22: rclone sync to B2 denied](../incidents/2026-10-22-rclone-sync-permission-denied.md)
