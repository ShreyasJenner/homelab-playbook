# Backup kept every service down for 1 h 15 min

- **Date:** 2026-11-01
- **Status:** resolved
- **Service:** Restic backup
- **Runbook:** [The nightly backup took long](../runbooks/backup-took-long.md)

## Symptom

healthchecks.io emailed "down" at 02:40 and "up" at 03:52. On a normal night the backup stops the stacks for 3–4 minutes and no email comes. The user had added a new TV show and some manga the day before.

## Cause

The script stops every stack, runs `restic backup` over `~/docker` *and* the media folders, and only then starts the stacks again. So the downtime lasts as long as restic takes to read the media.

On 2026-10-31 the 43 symlinks in `media/manga` and `media/lns` were converted to hardlinks. Restic had stored each one as a small symlink. Now each is a folder of real files at a path restic had no parent for, so it read and hashed every file again, although deduplication meant it already had the content:

```
02:37:21 Running restic backup
03:51:49 Added to the repository: 24.015 GiB (23.705 GiB stored)
03:51:49 processed 133445 files, 392.678 GiB in 1:14:28
03:52:00 Container uptime-kuma Starting
```

The snapshot grew from 270.1 GiB (2026-10-31) to 392.7 GiB, but only 24 GiB was new: about 98 GiB was read and found to be already stored. `restic diff` between the two snapshots showed `43 T` (type changed, the 43 converted links) and new paths such as `media/manga/Fool…` and `media/manga/Yona…`. The 24 GiB added was the new manga (`+233` files). The TV show isn't in the backup.

The night before (2026-10-31) the backup step took 16:05 for 18 GiB added. That's already longer than the healthcheck grace, so it probably alerted too. **The downtime grows with how much new media restic has to read**, which is the "sometimes" the user had seen.

## Ruled out

- **Slow or failing USB disk:** the kernel log from 02:00 to 04:30 had no USB resets, I/O errors or `blk_update` lines.
- **Something other than `restic backup` keeping the stacks down:** stopping took about 12 seconds (02:37:09–02:37:21) and starting about 10 (03:51:50–03:52:00). `start_all` runs at line 70 of the script, before retention and the Sunday `--read-data-subset=5%` check, which ran 03:52–03:57 with everything up.
- **A network outage dropping the pings:** the alert window (02:40–03:52) matches Kuma stopping (02:37:16) and starting (03:52:00).

## Fix

None needed for this night: the converted folders now have a parent snapshot, so the next runs should be back to a few minutes. The design problem stays: the stacks are down while media is read. Splitting the backup so only `~/docker` is copied with the stacks stopped is follow-up 40.
