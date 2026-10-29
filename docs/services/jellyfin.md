# Jellyfin

```
Status:     live
Host:       homelab
Exposure:   tailnet-only (intended); 8167/tcp and 7461/udp are published on 0.0.0.0, so also reachable from the home LAN
URL:        https://movies.example.com
Config:     ~/docker/jellyfin/ (docker-compose.yml, .env, config/, cache/)
Depends on: the media folders on the 4 TB HDD
Per-User:   no; one instance, an account per User
Verified:   2026-10-28
```

## What it's for

Watching movies, TV and anime, as separate libraries.

## Why this one

For watching movies. [Navidrome](navidrome.md) stays the music server; Jellyfin is only for video.

## How it's set up

- Image `jellyfin/jellyfin` (untagged, so `latest`), `user: ${UID}:${GID}` (1000), host port `8167` → `8096`, and `7461/udp` → `7359/udp` for client discovery.
- `./config` (including plugins) and `./cache` are bind mounts. `extra_hosts: host.docker.internal:host-gateway`.
- **Identity mounts** (read-only, host path = container path):
  - `/mnt/hdd-4tb/media/{anime,anime_movies,tv_shows,movies}`

  An absolute symlink only resolves inside a container if its target exists there at the same path. That's why the folders are mounted at their host paths, and **library paths in Jellyfin must be these full paths**, not `/media` ([2026-09-04](../incidents/2026-09-04-jellyfin-symlinked-show-not-found.md)).
- **TV and anime are hardlinks** (converted from symlinks on 2026-10-22). **`media/movies` still has 12 symlinks**.
- **Naming:** series folders `<Title> (<Year>) [tvdbid-<id>]`, seasons `Season 01`, episodes `… - S01E01 - …`. Jellyfin matches on `SxxExx` and the `[tvdbid-…]` tag.
- **The TheTVDB plugin is installed** (`config/plugins/TheTVDB_24.0.0.0`), for anime episode numbering.
- Uptime Kuma checks `http://localhost:8167/health`.
- **Not backed up on purpose:** the TV, anime and movie files are too large. `config/` is backed up with `~/docker`.

## Gaps

- **The discovery port is published as `7461`**, not `7359`, so apps on the LAN probably can't find the server automatically. Typing the address works. It's set by `UDP_HOST_PORT` in `.env`.

## Runbooks

- [Jellyfin shows wrong or missing episodes](../runbooks/jellyfin-wrong-episode-metadata.md)
- [Media libraries are empty, or nothing runs, after a reboot](../runbooks/media-libraries-empty-after-reboot.md)

## Incidents

- [2026-09-04: symlinked show not found](../incidents/2026-09-04-jellyfin-symlinked-show-not-found.md)
- [2026-10-02: media libraries empty after the HDD mounted late](../incidents/2026-10-02-media-libraries-empty-after-late-hdd-mount.md)
- [2026-10-13: one MP4 wouldn't play](../incidents/2026-10-13-jellyfin-mp4-wont-play.md)
- [2026-10-22: anime season misidentified](../incidents/2026-10-22-jellyfin-anime-season-misidentified.md)
