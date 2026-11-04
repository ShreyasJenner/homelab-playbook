# Navidrome

```
Status:     live
Host:       homelab
Exposure:   tailnet-only (intended); 4533 is published on 0.0.0.0, so it's also reachable from the home LAN
URL:        https://music.example.com
Config:     ~/docker/navidrome/ (docker-compose.yml; data/ → /data: database, cache, navidrome.toml)
Depends on: the music library on the 4 TB HDD (/mnt/hdd-4tb/media/music, read-only)
Per-User:   no; one instance, an account per User
Verified:   2026-10-28
```

## What it's for

Streams the music library to the browser and to phones through Subsonic clients.

## Why this one

Lightweight, music-only, and it speaks the Subsonic API, so many iOS clients work with it (play:Sub, Substreamer, Amperfy). It was compared with Jellyfin on 2026-07-18 and kept for music. [Jellyfin](jellyfin.md) came later for video only.

Synced lyrics (`.lrc` files next to the tracks) were researched on 2026-10-30, and again on 2026-11-03 for Japanese and Chinese songs: [Research: synced lyrics](../research/synced-lyrics.md). Since 2026-11-03, [LRCGET web](lrcget.md) writes them, and Navidrome reads them from its read-only mount with no change.

## How it's set up

- Image `deluan/navidrome:latest`, port `4533`, networks `navidrome_default` and `music`. `music` is a leftover from Maloja; nothing else is on it.
- Mounts: `~/docker/navidrome/data → /data`, and `/mnt/hdd-4tb/media/music → /music` (read-only).
- Settings (env, 2026-10-28):
  - `ND_SCANSCHEDULE=1h`: new albums appear within the hour.
  - `ND_AGENTS=lastfm`: scrobbling goes to **Last.fm**, configured per account in the UI.
  - `ND_SESSIONTIMEOUT=24h`, `ND_LOGLEVEL=info`, `ND_LYRICSPRIORITY=.lrc,.txt,embedded`.
- Albums are grouped by `ALBUM` + `ALBUMARTIST`, so a compilation needs `albumartist="Various Artists"`. beets was used for manual tag fixes; its files are now in `/mnt/hdd-4tb/media/beets`.
- Uptime Kuma checks `http://localhost:4533/ping`.

## Known leftovers

`ND_LISTENBRAINZ_ENABLED=true` with `ND_LISTENBRAINZ_BASEURL=http://maloja:42010/apis/listenbrainz/1/` still point at [Maloja](maloja.md), which is retired. Scrobbles to it fail quietly; Last.fm is unaffected. To remove, delete both lines from the compose file and run `sudo docker compose up -d`.

## Runbooks

- [Media libraries are empty, or nothing runs, after a reboot](../runbooks/media-libraries-empty-after-reboot.md)
- [A compose or `.env` change didn't take effect](../runbooks/compose-change-didnt-take-effect.md)

## Incidents

- [2026-10-02: media libraries empty after the HDD mounted late](../incidents/2026-10-02-media-libraries-empty-after-late-hdd-mount.md)
