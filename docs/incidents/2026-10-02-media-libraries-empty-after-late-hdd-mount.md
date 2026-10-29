# Media libraries empty after the HDD mounted late

- **Date:** 2026-10-02 to 2026-10-04
- **Status:** resolved; prevention in place
- **Service:** Navidrome, Kavita, Jellyfin (every app using the 4 TB HDD)
- **Runbook:** [Media libraries are empty, or nothing runs, after a reboot](../runbooks/media-libraries-empty-after-reboot.md)
- **Source:** chats "Media server file discovery issue" (2026-10-02) and "Nextcloud files scan lock issue" (2026-10-04). Unverified; prevention verified 2026-10-28.

## Symptom

- **2026-10-02:** every library looked empty, and `ls` on the folders took 1.5 seconds.
- **2026-10-03/04:** Navidrome marked every track "missing".

## Cause

The USB HDD enumerated about two minutes after boot. systemd's default 90-second wait for the device ran out ("Dependency failed for mnt-hdd\x2d4tb.mount"), `nofail` let boot continue, and Docker started every container against the empty mountpoint on the internal disk. Mounting the disk by hand afterwards didn't help the running containers, which kept the empty folder.

## Fix

Mounted the disk and restarted the containers. To stop it happening again:
- `RequiresMountsFor=/mnt/hdd-4tb` on `docker.service`
- fstab `x-systemd.device-timeout=5min`

Since then a missing disk stops Docker entirely, instead of starting the apps empty.
