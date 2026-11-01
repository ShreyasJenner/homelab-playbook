# The nightly backup took long

The backup script stops every stack, runs `restic backup` over `~/docker` and the media folders, and only then starts the stacks again. So when restic is slow, every service, Uptime Kuma included, stays down until it finishes.

## Symptom

- healthchecks.io emails "down" a few minutes after 02:30 and "up" much later.
- Services are unreachable after 02:30 for longer than the usual 3–4 minutes.

## Check

The journal needs `sudo`; without it `journalctl` prints only a hint and no lines.

```bash
sudo journalctl -u restic-docker-backup.service --since today --no-pager -o short-iso \
  | grep -E '\] Stopping|Running restic|processed|Added to the|uptime-kuma Starting|retention|finished|ERROR|WARNING'
sudo journalctl -k --since '02:00' --until '05:00' --no-pager | grep -i -E 'usb|reset|I/O error|blk_update' | tail
R="sudo restic -r /mnt/backup-hdd/restic-repo --password-file /root/.config/restic/password"
set -- $($R snapshots --compact | awk '/^[0-9a-f]{8} /{print $1}' | tail -2)
$R diff "$1" "$2" > /tmp/rdiff.txt
grep -E '^[+MUT-] ' /tmp/rdiff.txt | awk '{n=split($2,a,"/"); print $1, a[2]"/"a[3]"/"a[4]"/"a[5]"/"a[6]}' | sort | uniq -c | sort -rn | head -15
tail -8 /tmp/rdiff.txt; rm -f /tmp/rdiff.txt
```

Compare `processed … GiB in <time>` with `Added to the repository`, and with the previous night's run.

## Likely causes

| What the check shows | Cause |
|---|---|
| `Added` is large (tens of GiB), close to the snapshot's growth | A lot of new media in the backed-up folders: manga, LNs or music. Restic has to read and upload it all. |
| `processed` grew far more than `Added`; the diff has many `+` or `T` lines for files that aren't new | Files restic already has turned up at **paths it has no parent for**: a folder renamed or moved, symlinks converted to hardlinks, a `chown`/`chmod` over a whole tree. It reads and hashes them again, then dedups. |
| Kernel lines with USB resets or I/O errors during the run | The disk or its USB link is struggling. Check SMART (follow-up 29). |
| The gap is after `Running restic`, but `uptime-kuma Starting` comes after `retention` or the check | The script order changed. In the current script the stacks start straight after `restic backup`. |

## Fix

- **New data, or new paths:** nothing to do. Once a snapshot has the files, the next run compares against it and is fast again.
- **Disk errors:** see follow-up 29 before trusting the repo; run `$R check`.
- **For good:** back up `~/docker` with the stacks stopped, start them, and back up the media with everything running (follow-up 40). Then the downtime no longer depends on the media.

## Related incidents

- [2026-11-01: backup kept every service down for 1 h 15 min](../incidents/2026-11-01-backup-downtime-after-hardlink-conversion.md)
