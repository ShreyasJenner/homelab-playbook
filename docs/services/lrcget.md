# LRCGET web

```
Status:     live (since 2026-11-03)
Host:       homelab
Exposure:   tailnet-only (5411 is published on 127.0.0.1 only, so not reachable from the home LAN)
URL:        https://lyrics.example.com
Config:     ~/docker/lrcget/ (docker-compose.yml, .env, data/ → /data, tried-ids.txt);
            /usr/local/sbin/lrcget-fetch.py; /etc/systemd/system/lrcget-fetch.{service,timer}
Depends on: the music library on the 4 TB HDD (/mnt/hdd-4tb/media/music, read-write); lrclib.net
Per-User:   no; one basic-auth login, used only by ShreyasJenner
Verified:   2026-11-03
```

## What it's for

Fetches synced lyrics for the music library from LRCLIB and writes them as sidecar files next to each track: `track.lrc` when synced lyrics exist, `track.txt` when only plain lyrics do. [Navidrome](navidrome.md) reads those files first (`ND_LYRICSPRIORITY=.lrc,.txt,embedded`). An hourly timer gives each new track **one** try. Tracks LRCLIB doesn't have stay in the UI's "no lyrics" filter, to be fixed by hand.

## Why this one

Researched on 2026-10-30 and again on 2026-11-03 for Japanese and Chinese songs: [Research: synced lyrics](../research/synced-lyrics.md). LRCGET is the official LRCLIB client. The [ellemarks/lrcget-web](https://github.com/ellemarks/lrcget-web) fork runs it as a web server with the same UI, including a manual search that turned out to be the most useful part. It only adds `.lrc`/`.txt` files and never retags, renames or moves tracks. For albums LRCLIB lacks (most often Chinese ones), the note's manual fallback is LDDC on the desktop plus a pairing script. The automatic Japanese/Chinese chain from the note (lrcmux and a review script) was not set up.

## How it's set up

- Image `ghcr.io/ellemarks/lrcget-web:latest` (2.2.1 on 2026-11-03), container `lrcget`, `user: "1000:1000"` (the owner of the music folder). Host port **`127.0.0.1:5411` → `3000`**. Mounts `~/docker/lrcget/data → /data` (SQLite database and cache) and `/mnt/hdd-4tb/media/music → /music`, read-write. The image sets `LRCGET_ROOT=/music`, so nothing outside the library can be browsed. Sources: the fork's [README](https://github.com/ellemarks/lrcget-web#self-hosting-the-web-version), [docker-compose.yml](https://github.com/ellemarks/lrcget-web/blob/main/docker-compose.yml) and [Dockerfile](https://github.com/ellemarks/lrcget-web/blob/main/Dockerfile). The loopback bind, the bind mount instead of upstream's named volume (so restic covers it) and `latest` were install decisions.
- **Login:** basic auth, user `alice`, password `<LRCGET_PASSWORD>` in `~/docker/lrcget/.env` (generated on the host) and in Vaultwarden. Auth covers every URL, including `/api/info`. With no login set, anyone on the tailnet could change lyrics files and publish to LRCLIB, so don't remove it.
- **Settings (UI):** embedding into tracks off (the default), auto-export `.lrc` + `.txt`, LRCLIB instance `https://lrclib.net`. Exporting both formats leaves exactly one file per track: the `.lrc` replaces a same-named `.txt`.
- **Caddy:** `@lyrics host lyrics.example.com` → `reverse_proxy localhost:5411`.
- **Homepage:** a tile in instance a (Media group, after Navidrome) with **no `siteMonitor`**: every URL answers 401 without the login, so a dot would always be red.
- **Uptime Kuma:** HTTP monitor `http://localhost:5411/api/info` with basic auth and the "Kuma Alert" notification ticked (user, 2026-11-03).
- In `DEFAULT_STACKS` (after `navidrome`). Restic backs up `~/docker/lrcget` (database and `tried-ids.txt`) with the stack stopped, and the `.lrc`/`.txt` files with the music.

### The hourly fetch: once per track

`lrcget-fetch.timer` runs `lrcget-fetch.service` (oneshot, as `alice`) at :15 every hour **except 02:15**, the backup window. The service runs `/usr/local/sbin/lrcget-fetch.py`, which uses the server's internal API (`POST /api/invoke/<command>`, the same calls the UI makes, [api.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/bin/lrcget-server/api.rs)):

1. `scan_library` (local disk only; returns when the scan is done).
2. `get_track_ids` with only `noLyricsTracks` true: the tracks with no `.lrc`/`.txt`. The four flags are include-flags (checked 2026-11-03: no-lyrics 1381 + synced 873 + plain 59 = all 2313).
3. Drops every ID already in `~/docker/lrcget/tried-ids.txt`. If nothing is left, LRCLIB isn't contacted at all.
4. If the UI's download queue is busy, skips this run.
5. Records the new IDs as tried **before** queueing them, then `queue_downloads` with `.lrc` + `.txt` export and no embedding. LRCGET spaces requests 0.5–0.75 s apart and honours LRCLIB's `Retry-After`.
6. Waits for the queue to drain, then logs `tried N new tracks: X got lyrics, Y missed`.

**A miss is never retried.** The user chose this to keep the load off LRCLIB for lyrics that probably don't exist. To retry a track, use the UI (search or download). `lrcget-fetch.py --seed` records every current no-lyrics track as tried without fetching anything.

**Backfill, 2026-11-03:** the script's first run tried all 1,381 tracks that had no lyrics, in 20 minutes: **999 got lyrics, 382 missed**. Before that, 932 tracks already had sidecars (901 `.lrc`, 33 `.txt` from earlier use), and a Japanese album fetched from the UI came out right (user). The first timer run after the backfill (22:15) logged `nothing new (382 tracks without lyrics, all tried before)`, so the misses weren't asked about again.

```bash
systemctl list-timers --no-pager | grep lrcget        # next run
sudo journalctl -u lrcget-fetch -n 5 --no-pager       # last results
wc -l ~/docker/lrcget/tried-ids.txt                   # tracks ever tried
```

Undo the timer: `sudo systemctl disable --now lrcget-fetch.timer`.

## Gotchas

- **The track IDs are LRCGET's database row IDs.** If `data/` is lost or the library is rebuilt (`full_scan_library`, or removing and re-adding `/music`), the IDs change, and the next run tries every lyric-less track once more (about 380 requests today).
- **Romaji tags can give romanised lyrics.** LRCLIB returned romaji lyrics for LiSA "Gurenge" tagged in romaji (research probe, 2026-11-03), and LRCGET doesn't check the script. Fix such a track by hand.
- **The image follows `latest` from a one-person fork.** `stacks.sh update` can pull a breaking change. If it breaks, pin `:2.2.1` in the compose file.
- **The fetch script relies on an undocumented API.** An update that renames `scan_library`, `get_track_ids`, `queue_downloads` or `get_download_queue` makes the service fail with an HTTP error in the journal; nothing alerts on that yet (follow-up 43).
- 2,320 audio files on disk, but LRCGET lists 2,313 tracks (2026-11-03). The 7 others are probably files it couldn't read; not looked into.
