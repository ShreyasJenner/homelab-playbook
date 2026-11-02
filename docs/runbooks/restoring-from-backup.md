# Restoring from the backup

A procedure. Only a single-service test restore (Navidrome, 2026-10-15) has been done for real, so treat the full-rebuild steps as a plan.

Everything needs the restic password (`/root/.config/restic/password`, or the copy you keep elsewhere). Restored files are owned by root, so work as root (`sudo -i`).

```bash
R="restic -r /mnt/backup-hdd/restic-repo --password-file /root/.config/restic/password"
$R snapshots --compact
```

Since 2026-11-02 each night makes two snapshots: `docker` (`~/docker`) and, a minute later, `media` (the media folders). A bare `latest` is therefore usually the `media` one, so narrow it with `--tag docker` or `--tag media`. Snapshots up to 2026-11-01 hold both, and are tagged `docker`.

## One file or folder

```bash
$R ls latest --tag docker /home/alice/docker/<stack>                  # find it
$R dump latest --tag docker /home/alice/docker/<stack>/<file> > /root/<file>   # a single file
$R restore latest --tag docker --target /root/restore --include /home/alice/docker/<stack>/<folder>
```

Restore to a folder on a real disk, not `/tmp` (which may be a small tmpfs). Then copy back what you need, with the right owner.

## One service, side by side (a test)

1. `$R restore latest --tag docker --target /root/restore --include /home/alice/docker/<stack>`
2. Copy `/root/restore/home/alice/docker/<stack>` somewhere new.
3. In the copy's compose file, change `container_name` and the host port.
4. `sudo docker compose -p <stack>-test up -d`, and check it works. Then `down`, and delete the copy.

## A service, for real

1. `cd ~/docker/<stack> && sudo docker compose down`
2. Move the broken folder aside.
3. `$R restore <snapshot> --target / --include /home/alice/docker/<stack>`
4. `sudo docker compose up -d`

Vaultwarden: restore under the same `DOMAIN`, and test over HTTPS (a plain `http://` address gives a secure-context error).

## The whole server

1. Install Debian, Docker, Tailscale, restic and rclone. Create the user `alice` (uid 1000).
2. Mount the 4 TB disk at `/mnt/hdd-4tb` **before** restoring, or the media paths land on the root disk. Mount the backup disk at `/mnt/backup-hdd`, or get the repo from B2:
   ```bash
   rclone --config <rclone.conf> sync backblaze:restic-backups /mnt/backup-hdd/restic-repo
   ```
3. Put the restic password in `/root/.config/restic/password` (mode 600).
4. `$R restore latest --tag docker --target /`, then `$R restore latest --tag media --target /`
5. Redo the host configuration that isn't in the backup:
   - fstab and the Docker drop-in `RequiresMountsFor=/mnt/hdd-4tb`
   - `/etc/docker/daemon.json` (log rotation)
   - the restic script and units
   - ufw rules
   - Tailscale login with the same machine name, plus the three Serve/Funnel entries ([Tailscale page](../services/tailscale.md#serve-and-funnel-entries))
   - the router's address for the server (the Euro-Office connector depends on the LAN address)
6. `cd ~/docker && ./stacks.sh up` (the default list has every live stack since 2026-10-30).
7. Rebuild Invidious's database (it isn't in the backup), and rebuild the Redlib image.

## Related incidents

- [2026-10-11: restore test gave an empty compose file](../incidents/2026-10-11-restore-test-empty-compose-file.md)
