# Research: synced lyrics for the music library

```
Question:   Is there a self-hostable service that automatically downloads synced lyrics (.lrc)
            for the music library, ideally with a web UI? Pick one and a runner-up.
Researched: 2026-10-30, from GitHub repos, source code and the GitHub API, official docs,
            LRCLIB's API docs, Docker Hub and GHCR. No host access.
Fits:       a new lyrics container on homelab (Docker compose under ~/docker/<service>/,
            tailnet-only behind Caddy, read-write on the music folder)
```

The music library lives in `/mnt/hdd-4tb/media/music` (folders roughly `Artist - Album`). [Navidrome](../services/navidrome.md) mounts the same folder read-only, scans hourly, and already has `ND_LYRICSPRIORITY=.lrc,.txt,embedded`, so a `.lrc` next to a track wins over anything else. beets was once used by hand and isn't running. So the gap is a tool that writes `.lrc` (or `.txt`) next to new tracks, catches up the existing library, and shows what's missing, without touching the audio files.

Repo numbers are from the GitHub API on **2026-10-30**. "Open" is GitHub's `open_issues_count`, which includes PRs. Nothing below has been run on the host.

## Summary

1. **Recommended: LRCGET web server** (`ghcr.io/ellemarks/lrcget-web`), plus a small systemd timer that calls its API. It's the official LRCLIB client ([LRCGET](https://github.com/tranxuanthang/lrcget), 3310 stars, 2.2.1 released 2026-10-24) rebuilt as a web app in a fork. It writes `track.lrc` for synced lyrics and `track.txt` when only plain lyrics exist, right next to the audio ([export.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/export.rs)). It matches on title, album, artist and duration through LRCLIB's exact `/api/get`. It has the best UI for the job: filter tracks by "no lyrics / plain / synced", search LRCLIB by hand, edit and re-sync a lyric, and publish fixes back. It has no scheduler of its own, so the timer does "scan, list tracks with no lyrics, queue downloads" through the same API the UI uses. The risk is the fork: created as a server on 2026-10-24, 23 stars, one maintainer. Accepted: pin the image to a digest once it works, and fall back to beets if the fork goes quiet.
2. **Runner-up: Canticle** (`ghcr.io/sydlexius/canticle`, repo [sydlexius/mxlrcgo-svc](https://github.com/sydlexius/mxlrcgo-svc)). It's the most complete service, with a periodic scan, an optional inotify watcher, a web UI, and `.lrc` with `.txt` fallback. But it has **no LRCLIB**. Its sources are Musixmatch (an auto-minted unofficial token), Petit Lyrics and YouTube Music's InnerTube API, all scraping-type sources the brief ranks lower. It's also a one-person project with 1 star. Pick it if zero glue matters more than the source. Once beets PR #7117 ships, beets replaces it as runner-up.
3. **Watch: beets `lyrics` plugin.** It's the most mature fetcher (LRCLIB first, `synced: yes`), but today it only writes lyrics into tags, which means retagging every file. That breaks the "only adds .lrc/.txt" rule. [PR #7117](https://github.com/beetbox/beets/pull/7117) (opened 2026-10-27, review required) adds `write_files` for `.lrc`/`.txt` sidecars. If it ships, beets in `linuxserver/beets` becomes the stronger runner-up.
4. **Optional second step: nd-lyrics.** A Navidrome plugin that fetches lyrics at play time for tracks LRCLIB had no file for (see [Play-time lyrics](#play-time-lyrics-no-files)).

## Comparison

| | LRCGET web (fork) | Canticle | beets `lyrics` (linuxserver/beets) | lrcget-cli |
|---|---|---|---|---|
| **1. Automation** | No scheduler; timer calls its API (scan → no-lyrics IDs → queue). Backfill = same call | Built-in scheduled scan (default every 900 s) + optional inotify watcher | Timer runs `beet import -A` + `beet lyrics` | `watch` mode with `--initial-scan` |
| **2. Source / matching** | LRCLIB `/api/get` (title, album, artist, duration ±2 s) | Musixmatch, Petit Lyrics, InnerTube. **No LRCLIB** | LRCLIB first, then Google, Genius, lrcmux; `dist_thresh` fuzzy match | LRCLIB, "fuzzy matching and intelligent fallback" |
| **Output** | `.lrc`, else `.txt`; embedding only if turned on | `.lrc`, else `.txt` | Tags only (FLAC `LYRICS`; MP3 `SYLT` + `USLT`). Sidecars only after PR #7117 | `.lrc` (plain `.txt` Unverified) |
| **Safe on a read-write library** | Yes: writes sidecars only. Note: writing `.txt` deletes a same-named `.lrc` and vice versa | Yes: sidecars only; `realign`/`revalidate` change sidecars only and are dry-run by default | **No**: `write: yes` rewrites tags | Yes (sidecars) |
| **3. Maintenance** | Upstream active (198 open, pushed 2026-10-24). Fork: 23 stars, 0 open, all server commits on 2026-10-24 | v1.50.4 (2026-10-26), 1 star, 151 open, created 2026-03-13 | v2.14.1 (2026-09-17), 15 872 stars, 680 open; LSIO image `2.14.1` (2026-10-21) | 1.0.0-beta (2025-09-25); last push 2025-09-29; watch-mode panics on non-ASCII paths open |
| **4. Resources** | One Rust binary + SQLite; ffmpeg only for in-browser playback | One Go binary + SQLite | Python; DB of the whole library | Rust binary; optional Redis |
| **5. Web UI** | Yes: library, filters, manual search, editor, publish to LRCLIB | Yes, off by default (`web_ui_enabled`) | None | None |

## How it would fit (LRCGET web)

**Compose** at `~/docker/lrcget/docker-compose.yml`, adapted from the fork's [docker-compose.yml](https://github.com/ellemarks/lrcget-web/blob/main/docker-compose.yml) and [README](https://github.com/ellemarks/lrcget-web#self-hosting-the-web-version). Host port 3000 is already taken by Invidious ([2026-10-22](../incidents/2026-10-22-homepage-port-3000-in-use.md)), so publish another port on localhost only. Caddy runs on the host network and proxies `localhost:<port>` ([Caddy](../services/caddy.md)). Whether 5411 is free is Unverified.

```yaml
services:
  lrcget:
    image: ghcr.io/ellemarks/lrcget-web:latest   # pin a digest once it works; built on every push to main
    container_name: lrcget
    restart: unless-stopped
    user: "${PUID}:${PGID}"                       # same owner as the music files
    ports:
      - "127.0.0.1:5411:3000"
    environment:
      LRCGET_USERNAME: alice
      LRCGET_PASSWORD: ${LRCGET_PASSWORD}         # <LRCGET_PASSWORD>, lives in ~/docker/lrcget/.env
    volumes:
      - ./data:/data                              # create first, owned by PUID (README warns Docker makes it root-owned)
      - /mnt/hdd-4tb/media/music:/music   # read-write: it writes .lrc/.txt here
```

- **Caddy:** add `@lyrics host lyrics.example.com` → `reverse_proxy localhost:5411`. Keep the basic auth on: "Anyone who can reach it can browse `LRCGET_ROOT`, change lyrics files, and publish to LRCLIB" ([README](https://github.com/ellemarks/lrcget-web#self-hosting-the-web-version)).
- **First run (UI):** add `/music` as the library folder. In settings, leave **embedding off** (`try_embed_lyrics` gates every embed: [db.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/db.rs)). Whether it defaults to off is Unverified. Set auto-export to `.lrc` and `.txt`.
- **Existing sidecars count:** the scanner reads `track.lrc` and `track.txt` next to each file ([metadata.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/scanner/metadata.rs)), so tracks that already have lyrics show up as having them and aren't re-fetched.
- **Navidrome needs no change:** it reads the sidecar from disk when a client asks for lyrics, not at scan time ([core/lyrics/sources.go](https://github.com/navidrome/navidrome/blob/master/core/lyrics/sources.go)). Its mount can stay read-only.

**Trigger and backfill.** The server exposes every UI command as `POST /api/invoke/<command>` with camelCase JSON args ([main.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/bin/lrcget-server/main.rs), [api.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/bin/lrcget-server/api.rs)). Downloads run in a server-side queue ([jobs.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/bin/lrcget-server/jobs.rs)). The command names and args below come from [commands.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/commands.rs). This is an internal API, not a documented one, and the script is **Unverified** (not run anywhere):

```sh
#!/bin/sh
# /usr/local/sbin/lrcget-fetch.sh: scan, then fetch lyrics for tracks that have none
set -eu
AUTH="alice:<LRCGET_PASSWORD>"          # real value in ~/docker/lrcget/.env
API=http://127.0.0.1:5411/api/invoke
post() { curl -fsS -u "$AUTH" -H 'Content-Type: application/json' -X POST -d "$2" "$API/$1"; }

post scan_library '{}' >/dev/null                        # incremental; quick hash = first 64 KB of each file
IDS=$(post get_track_ids '{"noLyricsTracks":true}')      # JSON array of track IDs
post queue_downloads "{\"trackIds\":$IDS,\"autoExport\":{\"plainText\":true,\"syncedLrc\":true,\"embedIntoTrack\":false}}"
```

- Run it from a systemd timer **hourly** (Navidrome scans hourly anyway), avoiding the restic window around 02:30, when every stack is stopped ([homelab](../hosts/homelab.md)).
- The **backfill** is the same script's first run, or "select all → download" in the UI.
- **Misses are retried every run.** A track LRCLIB has nothing for gets no lyricsfile, so it stays in "no lyrics". If that pile is large, drop the timer to every 6 h. LRCLIB allows roughly 90 requests/min per IP for a client that sends a User-Agent and expects `Retry-After` to be honoured on 429 ([LRCLIB docs](https://lrclib.net/docs.md)). LRCGET sends its own UA.
- **"Which tracks lack lyrics":** the UI's filter, or `get_track_ids` with `{"noLyricsTracks":true}` / `{"plainLyricsTracks":true}` for counts.
- **Exporting both formats:** `.txt` is written first and `.lrc` second. Each one deletes its same-named sibling ([export.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/export.rs)), so a track ends up with exactly one file: `.lrc` if synced exists, else `.txt`. Instrumentals get `[au: instrumental]` in a `.lrc`.
- **Undo:** stop the container. Every file it made is a `.lrc` or `.txt` next to a track.

**Match quality depends on tags.** `/api/get` needs the track's title, artist, album and a duration within ±2 s ([LRCLIB docs](https://lrclib.net/docs.md)). Badly tagged albums will miss. That's where the UI's manual search helps. LRCLIB's synced coverage for this library wasn't measured.

**If the fork goes quiet:** upstream has had an open request for an official web/Docker build since 2024 ([#87](https://github.com/tranxuanthang/lrcget/issues/87)). The fork's server code is a separate binary (`lrcget-server`) on top of upstream, so it can be rebuilt from source with the `cargo build … --features server` line in its README.

## Candidates

### LRCGET and its server builds

- **Upstream** [tranxuanthang/lrcget](https://github.com/tranxuanthang/lrcget): desktop (Tauri) only. "LRCGET is the official client of LRCLIB" ([README](https://github.com/ellemarks/lrcget-web#lrcget)). 2.2.1 released 2026-10-24.
- **[ellemarks/lrcget-web](https://github.com/ellemarks/lrcget-web):** fork with a headless HTTP server and the same UI. Image `ghcr.io/ellemarks/lrcget-web`, amd64 and arm64. Its commits on 2026-10-24 are "Add self-hosted web server alongside the Tauri desktop app" and "Run bulk download/export queues on the server". Recommended above.
- **[Gtt1229/docker-lrcget](https://github.com/Gtt1229/docker-lrcget)** (16 stars, pushed 2026-07-24) and **[crywolf203/lrcget-unraid](https://github.com/crywolf203/lrcget-unraid)** (2 stars, LRCGET 2.2.1 build released 2026-10-29) run the desktop app in a browser-reachable container. Docker-lrcget is VNC-based. Lrcget-unraid's mechanism is Unverified. Neither can be scripted, so automation is manual.
- **[diego-ninja/lrcget-cli](https://github.com/diego-ninja/lrcget-cli)** (40 stars): Rust CLI with `watch --initial-scan` and a Docker Hub image `diegoninja/lrcget-cli` (last pushed 2025-09-29). Its README calls it "early-beta", and its watch mode has open panics on non-ASCII paths ([#9](https://github.com/diego-ninja/lrcget-cli/issues/9), [#18](https://github.com/diego-ninja/lrcget-cli/issues/18)). No commits for 13 months. Ruled out.

### Canticle (mxlrcgo-svc)

- Serve mode runs a clock-anchored periodic scan, and an optional watcher (`MXLRCGO_WATCH_ENABLED`) rescans a directory within seconds of a change ([User Guide](https://github.com/sydlexius/mxlrcgo-svc/blob/main/docs/USER_GUIDE.md)). It writes "`.lrc` for synced lyrics and `.txt` for unsynced lyrics or an instrumental marker" ([README](https://github.com/sydlexius/mxlrcgo-svc#readme)). The web UI is "off by default; enable it with `web_ui_enabled = true`" and has one admin account. Image `ghcr.io/sydlexius/canticle:latest`.
- **Sources:** Musixmatch is primary by default. "On first run Canticle obtains [a token] automatically" ([README](https://github.com/sydlexius/mxlrcgo-svc#token)). Petit Lyrics and InnerTube are tokenless fallbacks ([orchestration](https://github.com/sydlexius/mxlrcgo-svc/blob/main/docs/multi-provider-orchestration.md)). Its own [provider-terms.md](https://github.com/sydlexius/mxlrcgo-svc/blob/main/docs/provider-terms.md) records Musixmatch clauses still "unaddressed" and says it is "not a compliance sign-off". A GitHub code search for "lrclib" in the repo found nothing.
- For a tokenless setup, make Petit Lyrics or InnerTube the primary and leave Musixmatch out. Whether that drops Musixmatch entirely (no auto-minted token) is Unverified.
- Runner-up for automation and UI; ranked below LRCGET for source and maintenance.

### beets `lyrics` plugin

- Defaults: `sources: [lrclib, google, genius, lrcmux]`, `synced: no`, `auto: yes`, `dist_thresh: 0.11`. `google` needs `google_API_key` ([docs](https://beets.readthedocs.io/en/stable/plugins/lyrics.html)). Set `synced: yes` and `sources: [lrclib]` to stay keyless.
- **Writes tags, not files.** Lyrics live in the beets DB and reach the file only when `import.write` is on ([docs](https://beets.readthedocs.io/en/stable/plugins/lyrics.html)). That means beets writes its whole tag set back to each track. Sidecar support is [issue #6396](https://github.com/beetbox/beets/issues/6396) and [PR #7117](https://github.com/beetbox/beets/pull/7117) (open, review required, 2026-10-30): `write_files`, `.lrc` when synced, `.txt` otherwise, plus `beet lyrics --local --write-files` to back-fill from the DB.
- **Navidrome gap for MP3:** since [PR #6566](https://github.com/beetbox/beets/pull/6566) (merged 2026-05-27), synced lyrics in ID3 go to `SYLT` and plain text to `USLT`. Navidrome's tag mapping reads `lyrics` from `uslt`, `lyrics` and `unsyncedlyrics` only ([mappings.yaml](https://github.com/navidrome/navidrome/blob/master/resources/mappings.yaml)), so MP3s would show unsynced lyrics. FLAC keeps LRC text in `LYRICS`, which Navidrome parses as synced. This is inferred from the code, Unverified in practice.
- Known bug: synced LRCLIB lyrics are dropped for plain when the LRC ends with a blank line ([#7070](https://github.com/beetbox/beets/issues/7070), open).
- **How it would fit if #7117 ships:** `lscr.io/linuxserver/beets:2.14.1` (or newer), library mounted read-write, config `import: {copy: no, move: no, write: no, autotag: no}`, `lyrics: {synced: yes, sources: [lrclib], write_files: yes}`. Then a timer runs `beet import -A -q --incremental /music` and `beet lyrics --write-files`. No UI. "Which tracks lack lyrics" = `beet ls lyrics::^$`.

## Play-time lyrics (no files)

Not ranked against the writers above.

- **[nd-lyrics](https://github.com/J0R6IT0/navidrome-lyrics-plugin)** (Navidrome plugin, 446 stars, v8.1.0 released 2026-09-17). Navidrome ≥ v0.63.0. The host runs `deluan/navidrome:latest`, and the latest release is v0.64.2 (2026-09-24). Add `nd-lyrics` to `ND_LYRICSPRIORITY` after the file sources. "The plugin will fetch lyrics only when a client requests them". Sources: LRCLIB, lyrics.ovh, lrcmux, KuGou, NetEase, QQ Music, Apple Music (subscription) and others. It *can* write sidecar files, but only for tracks someone plays, and Navidrome's mount is read-only here. The README warns "The Navidrome WebUI does not display lyrics from plugins", so a Subsonic client is needed. It's a cheap complement to the recommendation for tracks LRCLIB misses, and the chosen optional second step (a small change to Navidrome's compose).
- **[Feishin](https://github.com/jeffvli/feishin)** (desktop Navidrome client, 1.17.0, 2026-09-15) has built-in online fetchers for LRCLIB, NetEase and Genius ([source](https://github.com/jeffvli/feishin/tree/development/src/main/features/core/lyrics)).
- Whether the iOS clients in use (play:Sub, Substreamer, Amperfy) fetch lyrics online is Unverified.

## Ruled out

- **[newtonsart/synclyr2metadata](https://github.com/newtonsart/synclyr2metadata)** (49 stars, pushed 2026-05-23): embeds into tags.
- **[Shikogoru/lyricfetcher](https://github.com/Shikogoru/lyricfetcher)**: LRCLIB + NetEase to `.lrc`, but created 2026-10-26, 0 stars, no watch mode.
- **[tappyduckmancodes/multiplatform-lyric-downloader](https://github.com/tappyduckmancodes/multiplatform-lyric-downloader)**: desktop tool driven by Spotify/Deezer playlists, not a library watcher.
- **[jellyfin/jellyfin-plugin-lrclib](https://github.com/jellyfin/jellyfin-plugin-lrclib)**: for Jellyfin's own library. Jellyfin is video-only here.
- **[Jonny-Ponny/md-lrclib-addon](https://github.com/Jonny-Ponny/md-lrclib-addon)**: an addon for metadata-docker, 0 stars.
- **[Wilooper/Lyrica](https://github.com/Wilooper/Lyrica)**: a lyrics API, not a library fetcher.
- **lrcget-cli**: see above (unmaintained, watch-mode crashes).

## Brief

1. **Scope:** research lyrics add-ons that sit beside the existing music library.
2. **Format:** sidecar `.lrc` next to each track first; plain `.txt` when no synced lyrics exist is fine; embedding optional.
3. **Trigger:** automatic for each newly imported album, a one-off backfill of the existing library, and some UI or log of which tracks lack lyrics.
4. **Web UI:** nice-to-have, not a dealbreaker; a UI ranks higher for manually searching and fixing a lyric.
5. **Sources:** prefer free/keyless (LRCLIB). Token-based or scraping sources (Musixmatch, Genius, NetEase, etc.) allowed as fallbacks but ranked lower; note ToS and fragility.
6. **Constraints:** a Docker container on homelab, tailnet-only, write access to the music folder. Must only add `.lrc`/`.txt` and never rename, move or retag tracks (or say how to turn that off).
7. **Criteria, in order:** (1) automation / hooking into new imports, (2) match accuracy and synced coverage, (3) maintenance and project activity, (4) resource use, (5) web UI.
8. **Done when:** one recommended tool with a sketch of how it fits (compose, mounts, trigger), and a runner-up.
9. **Candidates:** beets `lyrics` with LRCLIB in a container; LRCGET and any server/Docker builds or forks; standalone lyrics-fetcher containers; anything else found.
10. **Play-time fetching** (Navidrome plugins, Subsonic clients): its own section, not ranked against the `.lrc` writers.

Added 2026-10-30, after the first round of findings:

11. **Accept the days-old LRCGET web fork?** Yes. Pin the image to a digest once it works; beets (after PR #7117) is the fallback if the fork goes quiet.
12. **Add nd-lyrics as a complement?** Yes, as an optional second step, not part of the recommendation.
13. **Runner-up:** Canticle today, because it works now; beets replaces it once PR #7117 ships.
14. **Tools that write lyrics into tags:** stay ruled out (tags, not sidecars).
15. **More research?** No. Embedding default, the timer script, LRCLIB coverage of this library, port 5411 and the iOS clients' online lyrics stay Unverified, to be settled during setup.
