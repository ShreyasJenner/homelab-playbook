# The nightly backup took long

The backup script stops every stack, runs `restic backup` over `~/docker`, starts the stacks again, and only then backs up the media folders. So when the `~/docker` backup is slow, every service, Uptime Kuma included, stays down until it finishes. A slow media backup only makes the run end later. Before 2026-11-02 (follow-up 40), the media was backed up with the stacks stopped too.

## Symptom

- healthchecks.io emails "down" a few minutes after 02:30 and "up" much later.
- Services are unreachable after 02:30 for longer than the usual 1–2 minutes.

## Check

The journal needs `sudo`; without it `journalctl` prints only a hint and no lines.

```bash
sudo journalctl -u restic-docker-backup.service --since today --no-pager -o short-iso \
  | grep -E '\] Stopping|Running restic|processed|Added to the|uptime-kuma Starting|retention|finished|ERROR|WARNING'
sudo journalctl -k --since '02:00' --until '05:00' --no-pager | grep -i -E 'usb|reset|I/O error|blk_update' | tail
R="sudo restic -r /mnt/backup-hdd/restic-repo --password-file /root/.config/restic/password"
set -- $($R snapshots --compact --tag docker | awk '/^[0-9a-f]{8} /{print $1}' | tail -2)   # or --tag media
$R diff "$1" "$2" > /tmp/rdiff.txt
grep -E '^[+MUT-] ' /tmp/rdiff.txt | awk '{n=split($2,a,"/"); print $1, a[2]"/"a[3]"/"a[4]"/"a[5]"/"a[6]}' | sort | uniq -c | sort -rn | head -15
tail -8 /tmp/rdiff.txt; rm -f /tmp/rdiff.txt
```

Each night has two `restic backup` runs, `(docker)` and then `(media)`. Only the time between the first `Stopping` and `uptime-kuma Starting` is downtime. For each run, compare `processed … GiB in <time>` with `Added to the repository`, and with the previous night's run.

## Likely causes

| What the check shows | Cause |
|---|---|
| `Added` is large (tens of GiB), close to the snapshot's growth | A lot of new data. Restic has to read and upload it all. In `~/docker` (Nextcloud uploads, say) it costs downtime; in the media (manga, LNs, music) it only makes the run finish later. |
| `processed` grew far more than `Added`; the diff has many `+` or `T` lines for files that aren't new | Files restic already has turned up at **paths it has no parent for**: a folder renamed or moved, symlinks converted to hardlinks, a `chown`/`chmod` over a whole tree. It reads and hashes them again, then dedups. |
| Kernel lines with USB resets or I/O errors during the run | The disk or its USB link is struggling. Check SMART (follow-up 29). |
| `uptime-kuma Starting` comes after `Running restic backup (media)`, `retention` or the check | The script order changed. In the current script the stacks start straight after the `(docker)` backup. |
| `using parent` is missing from a run, or both runs are slow on the same night | That path set has no earlier snapshot: the script's paths changed. Seed it once with `--parent <last snapshot>` (see the Restic page, State). |

## Fix

- **New data, or new paths:** nothing to do. Once a snapshot has the files, the next run compares against it and is fast again.
- **Disk errors:** see follow-up 29 before trusting the repo; run `$R check`.
- **Media keeping the stacks down:** fixed for good on 2026-11-02 (follow-up 40). `~/docker` is backed up with the stacks stopped, they start, and the media is backed up with everything running.

## Related incidents

- [2026-11-01: backup kept every service down for 1 h 15 min](../incidents/2026-11-01-backup-downtime-after-hardlink-conversion.md)
