# Restic (nightly backup)

```
Status:     live (since 2026-10-11)
Host:       homelab
Exposure:   n/a (no listener; outbound to Backblaze B2 only)
Script:     /usr/local/sbin/restic-docker-backup.sh (runs as root)
Units:      restic-docker-backup.timer → restic-docker-backup.service (/etc/systemd/system/)
Repo:       /mnt/backup-hdd/restic-repo (1 TB USB backup disk), mirrored to B2 bucket restic-backups
Secrets:    restic password: /root/.config/restic/password (600, root); B2 key: rclone.conf (see below)
Depends on: the backup disk mounted with its .backup-drive marker; the 4 TB disk (media paths); rclone and B2
Verified:   2026-10-28
```

## What it's for

A nightly, versioned, encrypted backup of everything needed to rebuild the homelab's services on a new machine (`~/docker`: every stack's compose file, `.env`, config and data), plus the media that's hard to replace. One copy lives on a USB disk next to the server, and one is offsite in Backblaze B2.

## Why this one

- **Restic rather than an rsync mirror:** a mirror copies deletions straight away and keeps no history. Restic keeps deduplicated, encrypted snapshots with retention, and preserves owners, permissions and symlinks. Borg would have done as well.
- **Stop the containers rather than dump each database:** one loop covers every stack and every database engine (MariaDB, Postgres, SQLite), and copying a live database directory can give a corrupt copy. The price is about 3–4 minutes of downtime each night.
- **What's included:** `~/docker`, music, light novels and manga. **TV, anime and movies are left out on purpose:** they're too large for the 1 TB disk.
- **B2 rather than OneDrive** for the offsite copy: OneDrive didn't have the space. B2 is pay-as-you-go.
- **Mirror the repo with rclone** rather than keep a second restic repo: the repo already existed on the disk. The mirror only runs if `restic check` passes, so a corrupt local repo isn't copied over the good offsite one.
- The earlier rsync `~/backup.sh` (to a desktop's disk) was never actually running, and is gone.

## How it works

The timer fires at 02:30 (with up to 10 minutes of random delay; `Persistent=true` catches up after downtime). The script then:

1. **Checks the backup disk.** It mounts `/mnt/backup-hdd` if needed, and **aborts without touching any container** unless the disk is mounted *and* `/mnt/backup-hdd/.backup-drive` exists. Without the marker, an unmounted disk would just be an empty folder on the internal disk.
2. **Records the running images** in `~/docker/.image-manifest.txt` (names, image tags and digests), so a restore can use the same versions.
3. **Stops every running project** in `~/docker/*/` with `docker compose stop`. A `trap` makes sure they're started again even if the backup fails.
4. **Backs up:**
   ```
   restic backup ~/docker \
     /mnt/hdd-4tb/media/{music,lns,manga} \
     --host homelab --tag docker --exclude-caches --exclude-if-present .nobackup
   ```
   Exit code 3 (some files unreadable) counts as a warning.
5. **Starts the projects again** straight away.
6. **Applies retention:** `forget --prune --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --keep-yearly 1`.
7. **Checks the repo:** `restic check` every night, and on Sundays re-reads 5% of the data.
8. **Mirrors to B2**, only if the check passed: `rclone sync` to `backblaze:restic-backups` with `--b2-hard-delete`, under a lock so two syncs can't overlap.

**Excluding something:** put an empty `.nobackup` file in the folder. Loki's and Prometheus's data folders have one (2026-10-28). Their older data stays in existing snapshots until retention removes them.

### Where the secrets live

- **The restic password:** `/root/.config/restic/password`, deliberately not on the backup disk, so a stolen disk can't be read. **Both the local repo and B2 are useless without it.** Today it's also in Vaultwarden, relying on the Bitwarden app's offline cache. That's circular, since restoring Vaultwarden needs the password, so it needs a copy that doesn't depend on the server (follow-up 5).
- **The B2 application key:** in `/home/alice/.config/rclone/rclone.conf` (remote `backblaze`), restricted to the one bucket. The file also still holds an old `onedrive` remote and token.
- The repo itself contains every `.env` file, encrypted by restic.

### State on 2026-10-28

- 9 snapshots (2026-10-11 to 2026-10-28), latest 230.6 GiB.
- Repo 207 GB on the 916 GB backup disk (24% used).
- B2 has space alerts, but no cap.
- The latest snapshot contains the data of Nextcloud, Vaultwarden, Gitea, Memos, Mindwtr, Actual Budget, Uptime Kuma and ntfy.

## Running restic by hand

The repository and password only exist inside the script, so pass them every time. This form never prints the password:

```bash
R="sudo restic -r /mnt/backup-hdd/restic-repo --password-file /root/.config/restic/password"
$R snapshots --compact
$R ls latest /home/alice/docker/<stack>
journalctl -u restic-docker-backup.service --since today --no-pager | tail -20
```

## What isn't backed up

- **Docker named volumes** (in `/var/lib/docker/volumes`): **Invidious's database**, Euro-Office's config and logs, plus leftovers from retired services.
- **Host configuration:** fstab, the Docker drop-in and `daemon.json`, the restic script and units, ufw rules, Tailscale state, `rclone.conf`, and the restic password itself.
- **Media:** TV, anime, movies, `backup/vns` and `media/games` on the 4 TB disk.

## Known gaps

- **A failed run alerts nobody.** The service has no `OnFailure=`, and nothing pings ntfy or healthchecks.io (follow-up 28).
- **Only one restore has been tested** (Navidrome, 2026-10-15). Not Vaultwarden, not Nextcloud, nothing from B2 (follow-up 30).
- Disk health (SMART) has never been checked; `smartmontools` isn't installed (follow-up 29).

## Runbooks

- [The nightly backup failed](../runbooks/backup-failed.md)
- [Restoring from the backup](../runbooks/restoring-from-backup.md)

## Incidents

- [2026-10-02: Nextcloud's files consumed by Paperless-ngx](../incidents/2026-10-02-nextcloud-files-consumed-by-paperless.md) (before any backup existed)
- [2026-10-11: backup aborted, drive marker missing](../incidents/2026-10-11-backup-aborted-missing-drive-marker.md)
- [2026-10-11: restore test gave an empty compose file](../incidents/2026-10-11-restore-test-empty-compose-file.md)
- [2026-10-22: rclone sync to B2 denied](../incidents/2026-10-22-rclone-sync-permission-denied.md)
