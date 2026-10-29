# Media libraries are empty, or nothing runs, after a reboot

The 4 TB USB disk (`/mnt/hdd-4tb`) holds all media. It can take about two minutes to appear after boot.

## Symptom

**Before 2026-10-04:**
- Navidrome, Kavita and Jellyfin show empty libraries, or every track "missing".
- `ls` on the folders is slow.

**Since 2026-10-04,** `docker.service` waits for the disk (`RequiresMountsFor=/mnt/hdd-4tb`). So if the disk doesn't mount, **Docker doesn't start, and every service is down**, not just media.

## Check

```bash
findmnt /mnt/hdd-4tb                               # mounted?
lsblk -f | grep -A1 -i -E 'sdb|hdd-4tb'                  # is the disk present at all?
systemctl status docker --no-pager | head -5               # waiting for the mount?
systemctl show docker -p RequiresMountsFor
journalctl -b | grep -i -E 'hdd-4tb|Dependency failed|sdb' | tail -20
sudo docker exec navidrome ls /music | head -3             # does a container see files?
```

## Likely causes

1. **The disk enumerated late** and systemd's mount wait ran out. With `nofail`, boot carried on without it.
2. **The disk isn't connected or failed to spin up** (USB cable, power, enclosure).
3. **The containers started before the mount** and bound the empty mountpoint on the internal disk. Only possible if the `RequiresMountsFor` drop-in is missing.

## Fix

```bash
sudo mount /mnt/hdd-4tb        # by fstab (UUID)
findmnt /mnt/hdd-4tb
sudo systemctl start docker            # if Docker was waiting
```

If containers came up against the empty folder, recreate the media stacks so they bind the real mount:

```bash
cd ~/docker && for s in navidrome jellyfin kavita; do (cd $s && sudo docker compose up -d --force-recreate); done
```

If containers ran against the empty mountpoint, they may have written files onto the internal disk underneath it. Those files are hidden once the disk is mounted. To find them, look in the folder at a time when the disk is unmounted.

## Prevention in place

- fstab: `defaults,nofail,x-systemd.device-timeout=5min`, so the mount waits up to 5 minutes for the disk.
- `RequiresMountsFor=/mnt/hdd-4tb` on `docker.service`.
- `x-systemd.automount` was tried on 2026-10-11 and isn't in use.

## Related incidents

- [2026-10-02: media libraries empty after the HDD mounted late](../incidents/2026-10-02-media-libraries-empty-after-late-hdd-mount.md)
- [2026-10-11: HDD not mounted after the automount test](../incidents/2026-10-11-hdd-not-mounted-after-automount-test.md)
