# Research: synced lyrics for the music library

```
Question:   Is there a self-hostable service that automatically downloads synced lyrics (.lrc)
            for the music library, including Japanese and Chinese songs tagged in kanji or romaji,
            and sends uncertain matches to the user to resolve by hand? Pick one setup and a runner-up.
Researched: 2026-10-30, 2026-11-03, from GitHub repos, source code and the GitHub API, official docs,
            LRCLIB's and MusicBrainz's API docs, live LRCLIB/lrcmux/MusicBrainz API queries,
            Docker Hub and GHCR. No host access.
Fits:       new lyrics containers on homelab (Docker compose under ~/docker/<service>/,
            tailnet-only behind Caddy, read-write on the music folder)
```

The music library lives in `/mnt/hdd-4tb/media/music` (folders roughly `Artist - Album`, `.flac` and `.mp3`). Japanese and Chinese albums are tagged in a mix of kanji/native script and romaji. [Navidrome](../services/navidrome.md) mounts the same folder read-only, scans hourly, and has `ND_LYRICSPRIORITY=.lrc,.txt,embedded`, so a `.lrc` next to a track wins over anything else. No lyrics fetcher is installed. beets was once used by hand and isn't running. So the gap is a tool that writes `.lrc` (or `.txt`) next to new tracks, catches up the existing library, works for Japanese and Chinese tags, and puts doubtful matches in front of the user instead of writing them, without touching the audio files.

Repo numbers are from the GitHub API on **2026-11-03** unless dated otherwise. "Open" is GitHub's `open_issues_count`, which includes PRs. Nothing below has been run on the host.

## Summary

**Installed 2026-11-03:** [LRCGET web](../services/lrcget.md), with a once-per-track hourly fetch instead of the retry-every-run timer sketched below.

**Chosen setup (2026-11-03):** LRCGET web's automatic exact-match LRCLIB pass (part 1 below, from the hourly timer), plus a manual workflow for whatever it misses. lrcmux and the review pass are dropped. For the manual part, the user runs LDDC on their Arch Linux desktop, copies the downloaded `.lrc` files to the host, and pairs them with the [pairing script](#pairing-script). A self-hosted web UI is skipped for now. The best one found is the lrcmux frontend, with its API, but it's weak: one result per search, no source choice, no album mode, and no download button in a released image yet ([Manual web UI](#manual-web-ui)). It will be reconsidered when lrcmux tags a release with downloads. The ranking below stays as the record of the research.

1. **Recommended: a three-part chain.** No single tool does LRCLIB first, CJK fallback, and a review queue, so this joins two existing tools with one small script.
   - **LRCGET web** (`ghcr.io/ellemarks/lrcget-web`) does the automatic first pass, as in the 2026-10-30 round: exact LRCLIB `/api/get` matches only, written as `.lrc` or `.txt`, from an hourly timer. Tracks it can't match stay in its "no lyrics" list. There the user can search LRCLIB by hand and pick a candidate, which is the UI brief 20 ranks highest.
   - **lrcmux** (`ghcr.io/f1nniboy/lrcmux-api`, self-hosted, [f1nniboy/lrcmux](https://github.com/f1nniboy/lrcmux)) is a lyrics aggregator. It gives one API over NetEase and KuGou (and LRCLIB, Deezer and others), so the script never talks to those fragile APIs itself.
   - **A review pass** (a short Python script, sketched below, not yet written) runs after LRCGET. For each track still without lyrics, it asks lrcmux one source at a time. It looks up romaji names through MusicBrainz aliases, for matching only. It writes a sidecar on its own only when it has a single exact match that passes a script check. Fuzzy matches, alias-based matches and disagreeing candidates go into a review folder plus a report. The user deletes the wrong candidates there and runs the pairing script from the manual fallback to install the rest.
   - Why this one: it is the only setup that meets brief 19 (nothing doubtful gets written) and still automates everything else. The cost is a script to maintain and two one-person projects (the LRCGET fork and lrcmux).
2. **Runner-up: LRCGET web pointed at a self-hosted lrcmux.** LRCGET has an "LRCLIB instance" setting, and lrcmux serves an LRCLIB-compatible `/compat/lrclib/api/get`, so this needs no custom code. But lrcmux races all enabled sources and keeps the first good answer, so LRCLIB isn't tried first. Disagreeing sources are never shown, and LRCGET's manual search then returns at most one result. In short, it gives more automatic coverage than the recommendation but no review queue.
3. **Third: Canticle** ([sydlexius/canticle](https://github.com/sydlexius/canticle), formerly mxlrcgo-svc). It is the strongest single tool for Japanese. It has Petit Lyrics (a Japanese lyrics service, with word timing), a script guard that rejects lyrics in the wrong script, a queue, a web UI with "Needs attention" and "Lyrics are wrong" actions, and a watcher. But it has no LRCLIB, NetEase, QQ or KuGou, so Chinese coverage depends on Musixmatch. Its default primary source is an auto-minted unofficial Musixmatch token. It ranks below the two LRCLIB-first setups because of brief 17.
4. **Watch: beets `lyrics` with an `lrcmux` backend.** Released beets 2.14.1 already has an `lrcmux` source with a configurable URL ([lyrics.py at v2.14.1](https://github.com/beetbox/beets/blob/v2.14.1/beetsplug/lyrics.py)). `sources: [lrclib, lrcmux]` would give LRCLIB first, then NetEase/KuGou via a self-hosted lrcmux. It still writes tags, not sidecars, until [PR #7117](https://github.com/beetbox/beets/pull/7117) ships (still open on 2026-11-03, last commit 2026-10-27, no approving review). It has no review queue either.
5. **Manual fallback, for albums no source matches:** [LDDC](https://github.com/chenmozhijin/LDDC) (desktop app) downloads a whole album's lyrics from QQ Music, KuGou or NetEase in original script. Then the pairing script [below](#pairing-script) renames them to match the album's tracks. 163MusicLyrics is the alternative.
6. **Optional, unchanged: nd-lyrics** for play-time lyrics in Subsonic clients ([Play-time lyrics](#play-time-lyrics-no-files)). Its source list includes NetEase, QQ Music and KuGou, so it's a cheap net under everything above.

## Comparison

| | 1. LRCGET + lrcmux + review pass | 2. LRCGET → lrcmux compat | 3. Canticle | Watch: beets + lrcmux (after #7117) | nd-lyrics (play-time, not ranked) |
|---|---|---|---|---|---|
| **1. Automation** | Hourly timer: LRCGET scan + queue, then the review pass | Hourly timer: LRCGET scan + queue | Built-in periodic scan + inotify watcher | Timer: `beet import -A` + `beet lyrics` | When a client asks for lyrics |
| **2. Sources** | LRCLIB first, then NetEase, KuGou via lrcmux | LRCLIB, NetEase, KuGou (+ whatever else is enabled), raced | Musixmatch, Petit Lyrics, YouTube Music. No LRCLIB | LRCLIB, then lrcmux | LRCLIB, NetEase, QQ Music, KuGou, lrcmux and others |
| **Romaji ↔ kanji** | MusicBrainz artist aliases + album track durations, for matching only | None: needs tags in the source's script | None found in docs | None | None |
| **Doubtful matches** | Queued for the user (review folder + report); never auto-written | Auto-written; nothing queued | Script guard rejects wrong-script results; misses listed in "Needs attention" | Auto-written (`dist_thresh` fuzzy for LRCLIB) | First match within duration tolerance wins |
| **Existing sidecars** | Untouched (LRCGET skips tracks that have one; the script refuses to overwrite) | Untouched | Untouched (adopts them) | Untouched (PR #7117 design, Unverified) | Not overwritten unless `overwrite_lyrics` |
| **3. Maintenance** | LRCGET fork: 23 stars, no commits since 2026-10-24. lrcmux: 46 stars, 1 contributor, pushed 2026-11-03. Plus our script | Same two projects, no script | v1.51.1 (2026-11-02), 1 star, 152 open, 1 main contributor | beets 15 891 stars, 675 open; PR open | v8.1.0 (2026-09-17), 454 stars, 5 open |
| **4. Resources** | Rust binary + SQLite; Go binary (in-memory cache, no Redis); a Python run per hour | Rust + Go binaries | Go binary + SQLite | Python + library DB + Go binary | Inside Navidrome |
| **5. Web UI** | LRCGET (manual LRCLIB search, editor); the review queue is files + report | LRCGET, but manual search gets one result at most | Yes: queue buckets, reports, lyric preview/editor | None | None |

## LRCLIB and Japanese/Chinese tags

LRCLIB has no published per-language statistics. Its [database dumps page](https://lrclib.net/db-dumps) needs JavaScript and wasn't read, so the dumps' size and date are Unverified. Its tracker has open requests for title/artist aliases ([lrclib #97](https://github.com/tranxuanthang/lrclib/issues/97), 2026-04-19) and better metadata ([#39](https://github.com/tranxuanthang/lrclib/issues/39)), which is the romaji/kanji problem in general form.

**Probe, 2026-11-03.** Live queries to `https://lrclib.net/api/get` with a generic User-Agent, for well-known songs tagged both ways. The duration was taken from the native-script record, so native tags had a small head start. Album names were guesses, and each case was also tried without one. Eight songs are not a coverage measure.

| Song | Native-script tags | Romaji / pinyin tags |
|---|---|---|
| YOASOBI 夜に駆ける / Yoru ni Kakeru | hit, plain only | hit, synced (Japanese text) |
| 米津玄師 Lemon / Kenshi Yonezu Lemon | hit, synced | hit, plain only |
| LiSA 紅蓮華 / Gurenge | hit, synced | hit, synced, **but the lyrics are in romaji** |
| ヨルシカ ただ君に晴れ / Yorushika Tada Kimi ni Hare | hit, synced | hit, synced (Japanese text) |
| Aimer 残響散歌 / Zankyosanka | hit, synced | hit without album; 404 with a guessed album name |
| 周杰倫 晴天 / Jay Chou Qing Tian | hit, synced | 404 |
| 陳奕迅 十年 / Eason Chan Shi Nian | hit, synced | 404 |
| 王菲 紅豆 / Faye Wong Hong Dou | hit, synced | 404 |

What this shows:
- Popular Japanese songs are on LRCLIB under both spellings, because users have submitted both. Chinese songs under pinyin titles mostly aren't. Fuzzy `/api/search` for "Eason Chan / Shi Nian" returned a **different song** (時光倒流二十年) as its top synced hit.
- A record can exist under one spelling with synced lyrics and under the other with plain only. Which one `/api/get` returns isn't predictable.
- Romaji tags can return **romanised lyrics** (LiSA "Gurenge"). Brief 18 wants original script, so an automatic writer needs a script check. LRCGET has none, Canticle has one, and the review pass would have one.
- Traditional and Simplified tags both hit (周杰倫 and 周杰伦, 陳奕迅 and 陈奕迅), each returning whatever was submitted. 周杰伦's record had Traditional lyrics text. LRCLIB doesn't convert.
- LRCGET only uses `/api/get` (exact, duration ±2 s), never `/api/search`, so the false positive above can't happen in LRCGET's automatic pass.

**lrcmux, 2026-11-03,** the public instance `api.lrcmux.dev` with `sources=kugou` (its NetEase and LRCLIB sources are switched off there; its [`/sources`](https://api.lrcmux.dev/sources) lists Deezer, KuGou, YouTube Music, Genius, Musixmatch). ヨルシカ ただ君に晴れ: hit. Yorushika Tada Kimi ni Hare: 404. LiSA Gurenge: hit, in Japanese script. LiSA 紅蓮華, and all three Chinese songs in either script: 404. The instance's location, and why its KuGou missed the Chinese songs, are unknown. A self-hosted instance may do better or worse (Unverified).

LRCLIB's rate limits changed since 2026-10-30. They are now about 45 requests/min for a generic client, about 90/min for a User-Agent that names the app, and more for registered apps; clients must honour `Retry-After` ([docs](https://lrclib.net/docs.md)). `/api/get` needs `track_name` and `artist_name`; `album_name` and `duration` are optional but recommended (same page).

## How it would fit (recommended chain)

### Part 1: LRCGET web (unchanged from 2026-10-30)

**Compose** at `~/docker/lrcget/docker-compose.yml`, adapted from the fork's [docker-compose.yml](https://github.com/ellemarks/lrcget-web/blob/main/docker-compose.yml) and [README](https://github.com/ellemarks/lrcget-web#self-hosting-the-web-version). Host port 3000 is taken by Invidious ([2026-10-22](../incidents/2026-10-22-homepage-port-3000-in-use.md)), so publish another port on localhost only. Caddy runs on the host network and proxies `localhost:<port>` ([Caddy](../services/caddy.md)). Whether 5411 is free is Unverified.

```yaml
services:
  lrcget:
    image: ghcr.io/ellemarks/lrcget-web:2.2.1     # GHCR tags on 2026-11-03: latest, 2.2.1, two sha-*; pin a digest once it works
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
- **First run (UI):** add `/music` as the library folder. Leave **embedding off**. It is off by default: the first migration inserts `try_embed_lyrics = 0` ([01-initial/up.sql](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/migrations/01-initial/up.sql)), and that flag gates every embed ([db.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/db.rs)). Set auto-export to `.lrc` and `.txt`. Leave "LRCLIB instance" at its default `https://lrclib.net` ([05-…/up.sql](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/migrations/05-add_track_number_and_config/up.sql)).
- **Existing sidecars count:** the scanner reads `track.lrc` and `track.txt` next to each file ([metadata.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/scanner/metadata.rs)), so tracks that already have lyrics show up as having them and aren't re-fetched. That includes files written by the review pass or the pairing script.
- **Navidrome needs no change:** it reads the sidecar from disk when a client asks for lyrics, not at scan time ([core/lyrics/sources.go](https://github.com/navidrome/navidrome/blob/master/core/lyrics/sources.go)). Its mount can stay read-only.

**Trigger and backfill.** The server exposes every UI command as `POST /api/invoke/<command>` with camelCase JSON args ([main.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/bin/lrcget-server/main.rs), [api.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/bin/lrcget-server/api.rs)). Downloads run in a server-side queue ([jobs.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/bin/lrcget-server/jobs.rs)). The command names and args come from [commands.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/commands.rs). This is an internal API, not a documented one, and the script is **Unverified** (not run anywhere):

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
# then: the review pass (part 3), once the queue has drained
```

- Run it from a systemd timer **hourly** (Navidrome scans hourly anyway), avoiding the restic window around 02:30, when every stack is stopped ([homelab](../hosts/homelab.md)).
- The **backfill** is the same script's first run, or "select all → download" in the UI.
- **Misses are retried every run.** A track LRCLIB has nothing for gets no sidecar, so it stays in "no lyrics". If that pile is large, drop the timer to every 6 h. LRCGET sends its own User-Agent.
- **Exporting both formats:** `.txt` is written first and `.lrc` second. Each one deletes its same-named sibling ([export.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/export.rs)), so a track ends up with exactly one file: `.lrc` if synced exists, else `.txt`. That meets "plain-only lyrics: write the `.txt` automatically". Instrumentals get `[au: instrumental]` in a `.lrc`.
- **Script check gap:** LRCGET will write romanised lyrics if LRCLIB returns them for romaji tags (see the probe). The review pass's report should also list `.lrc` files LRCGET wrote that are mostly Latin letters under a tag that MusicBrainz says belongs to a native-script artist. That check is part of the sketch, not of LRCGET.
- **Undo:** stop the container. Every file it made is a `.lrc` or `.txt` next to a track.

### Part 2: lrcmux (self-hosted, API only)

lrcmux fans one request out to its enabled providers and caches the results ([README](https://github.com/f1nniboy/lrcmux#readme)). Its native API is `GET /get?artist=&title=&album=&duration=&level=line&format=lrc&sources=<id>`, and `sources` restricts the request to one provider ([handler.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/api/handler.go)). The review pass uses that to see each source's answer separately. Its upstream compose also runs Redis and a frontend on port 3000 ([docker-compose.yml](https://github.com/f1nniboy/lrcmux/blob/main/docker-compose.yml)). Both are left out here. Without Redis it uses an in-memory cache ([config.example.toml](https://github.com/f1nniboy/lrcmux/blob/main/config.example.toml)), and its own per-IP rate limit only runs when Redis is set ([main.go](https://github.com/f1nniboy/lrcmux/blob/main/cmd/lrcmux/main.go)).

```yaml
# ~/docker/lrcmux/docker-compose.yml
services:
  lrcmux:
    image: ghcr.io/f1nniboy/lrcmux-api:1.7.0   # 1.7.0 = latest release (2026-07-27); main has newer commits
    container_name: lrcmux
    restart: unless-stopped
    ports:
      - "127.0.0.1:5412:8080"                 # whether 5412 is free is Unverified; no Caddy entry needed
    volumes:
      - ./config.toml:/etc/lrcmux/config.toml:ro
```

```toml
# ~/docker/lrcmux/config.toml: copy config.example.toml, then turn off what the brief doesn't want
[providers.lrclib]
enable = true        # used by the runner-up; part 3 asks lrclib.net directly
[providers.netease]
enable = true
[providers.kugou]
enable = true
[providers.musixmatch]
enable = false       # unofficial token
[providers.genius]
enable = false       # plain text only
[providers.ytmusic]
enable = false
[providers.deezer]
enable = false       # whether the ISRC resolver still needs it is Unverified
```

- **No QQ Music:** lrcmux has no QQ provider ([providers/](https://github.com/f1nniboy/lrcmux/tree/main/internal/providers)). QQ is reachable through nd-lyrics at play time and through LDDC by hand.
- **Matching is strict:** a NetEase result is used only if its normalised title and artist equal the query's ([netease/provider.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/providers/netease/provider.go), [normalize.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/normalize/normalize.go)). Normalising does NFKC, lower-casing, removing Latin accents, and stripping "feat." and video markers. It does not convert romaji to kanji or Simplified to Traditional, so 周杰倫 and 周杰伦 are different artists to it.
- **Undo:** stop the container. It writes nothing to the library.

### Part 3: the review pass (sketch, not written)

A Python script run by the same timer after part 1. It reads LRCGET's view of the library through the same API: `get_track_ids {"noLyricsTracks":true}`, then `get_track {"trackId":…}` for `filePath`, `title`, `artistName`, `albumName`, `trackNumber`, `duration` ([commands.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/commands.rs), [persistent_entities.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/persistent_entities.rs)). So it needs no tag library. Per album still missing lyrics:

1. **Ask each source as tagged.** Query lrcmux once per source (`sources=netease`, then `sources=kugou`) with the track's own title, artist and duration. Keep every answer as a candidate with its source.
2. **If the tags look romaji or pinyin** (no CJK characters, and the artist resolves to a native-script name in MusicBrainz, see [Matching aids](#matching-aids-romaji--kanji)), resolve the album's native titles through MusicBrainz. Then ask LRCLIB's `/api/get` and each lrcmux source again with the native names. These candidates are marked "via lookup". The lookup result is used only for the request, never written to tags.
3. **Script check** on every candidate. Native-script tags plus a mostly-Latin lyric body means the lyric is romanised, so reject it. Romaji tags plus a native-script artist means the candidate needs Kana/Han text in the body.
4. **Decide:**
   - **Write automatically**, as `<track>.lrc` (or `.txt` if the only text is plain), only when exactly one candidate is left, or all agree. It must also have come from the track's own tags (not via lookup) and passed the script check. "Agree" means the same lines after stripping timestamps and NFKC/case-fold, which is a rule to tune.
   - **Queue** everything else: matches via lookup, disagreeing sources, and candidates without a duration within ±2 s. Never write over an existing `.lrc`/`.txt` (open with `"x"` as the pairing script does).
5. **Queue = files + report.** Write each queued candidate to `~/lyrics-review/<album folder>/<NN> <source> <title>.lrc`, with `[ti:]` and `[length:]` headers. Append a line per track to `~/lyrics-review/REPORT.md`: album, track, tags, each candidate's source and first lines, and why it was queued.
6. **The user resolves it.** Open the album's review folder, delete the wrong candidates (two candidates for one track number stay unpaired on purpose), then run the [pairing script](#pairing-script) on that album with `--apply --move`. Anything still unresolved goes to LRCGET's manual search or the manual fallback.

Size guess: 150–250 lines of stdlib Python. MusicBrainz calls are limited to 1/s (below), so the backfill of a large CJK collection takes a while; it caches lookups per album. This is the part with the most risk. It's our code, not a maintained project, and the agreement rule is guesswork until it has run on real albums.

## Matching aids (romaji ↔ kanji)

- **Artist aliases work well.** MusicBrainz artist search returns aliases in other scripts. For example "Yorushika" → ヨルシカ (aliases YORUSHIKA, Yorushika, ヨルシカ), and `alias:"Jay Chou"` → 周杰倫 (aliases include 周杰伦, ジェイ・チョウ, Zhōu Jié Lún), queried 2026-11-03 at `https://musicbrainz.org/ws/2/artist/?query=…&fmt=json`.
- **Recording titles in romaji mostly don't.** On the same day, recording searches for "Tada Kimi ni Hare" (Yorushika) and "Qing Tian" (Jay Chou's MBID) returned nothing relevant. MusicBrainz stores titles in the original script and rarely has romaji recording aliases.
- **So match by album, not by title.** Resolve the artist via alias, then pick the artist's release whose track count and track durations match the local folder (each within ±2 s). Read the native titles from that release's tracklist, by track number. This avoids transliterating titles at all. A release that doesn't fit cleanly sends the whole album to the review queue.
- **Rate limits** ([MusicBrainz API rate limiting](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting)): about 1 request per second per IP, and every request needs a meaningful User-Agent ("Application name/<version> ( contact-url )"). Anonymous or generic agents are limited further, and over-limit requests get 503. The review pass should send its own app name and sleep between calls.
- **The source's own search** (NetEase/KuGou keyword search) would also find native titles from romaji. lrcmux's strict match discards those hits, and using them directly would mean our script talking to unofficial APIs. Left out.

## Script, translation and word timing per tool

| Tool | Original script only? | Translation / romanisation | Simplified/Traditional | Word-level |
|---|---|---|---|---|
| LRCGET web | Writes what LRCLIB returns, which can be romaji (see probe) | None | No conversion found in its source | Supports LRCLIB "lyricsfile" data; line-level LRC is what it exports (word-level export Unverified) |
| lrcmux | Returns what the provider returns | No | No conversion; strict match treats them as different ([normalize.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/normalize/normalize.go)) | Yes for KuGou/NetEase/Deezer ("word" level in `/sources`) |
| Canticle | Script guard: `MXLRC_GUARD_ACCEPTED_SCRIPTS` allowlist (Latin, Han, Kana, Hangul, Other) and `MXLRC_GUARD_THRESHOLD` (default 0.20) ([CONFIGURATION.md](https://github.com/sydlexius/canticle/blob/main/docs/CONFIGURATION.md)) | Original only by default; opt-in `bilingual_output` interleaves a translation ([multilingual-output-policy.md](https://github.com/sydlexius/canticle/blob/main/docs/multilingual-output-policy.md)) | Not documented | Writes a companion `.elrc` when a source has word timing (`word_sync_mode`, same page) |
| LDDC | Choose "original" in the lyric-content options | Original, translation and romaji can be combined ([README](https://github.com/chenmozhijin/LDDC#readme)); Bing/Google/OpenAI-compatible translation | Not found in its source (no zhconv/OpenCC) | Yes: word-by-word LRC, enhanced LRC, line LRC, SRT, ASS |
| 163MusicLyrics | Original, or original + translation | Translation (Baidu/Caiyun API); romaji in the old WinForms build ([RomajiUtils.cs](https://github.com/jitwxs/163MusicLyrics/blob/master/archive-winform/MusicLyricApp/Utils/RomajiUtils.cs)), in v7 Unverified | **Converts if set:** "Chinese Text" = Ignore / Simplified / Traditional ([en-US.json](https://github.com/jitwxs/163MusicLyrics/blob/master/cross-platform/MusicLyricApp/Resources/Localization/en-US.json)). Keep it on Ignore | Unverified |
| nd-lyrics | Returns what the provider returns | Apple Music only (paid, excluded) | Not documented | ELRC from KuGou, NetEase, QQ |

## Sources: fragility and terms

| Source | How it's reached | Fragility | Terms |
|---|---|---|---|
| LRCLIB | Official, documented, keyless API ([docs](https://lrclib.net/docs.md)) | Stable API; crowd-sourced data, so mixed spellings and some romanised files | Open; asks for an identifying User-Agent and `Retry-After` handling |
| NetEase Cloud Music | Unofficial `music.163.com/api` endpoints, same as in [lrcmux](https://github.com/f1nniboy/lrcmux/blob/main/internal/providers/netease/provider.go) and [nd-lyrics](https://github.com/J0R6IT0/navidrome-lyrics-plugin/blob/main/src/providers/services/netease/mod.rs) | Can change or block without notice. The public lrcmux instance has it switched off (reason not stated) | Not checked against NetEase's own terms: Unverified. Unofficial use |
| QQ Music | Unofficial; lyrics come in the encrypted QRC format that tools decrypt ([nd-lyrics qrc.rs](https://github.com/J0R6IT0/navidrome-lyrics-plugin/blob/main/src/providers/services/qqmusic/qrc.rs)) | Same as NetEase, plus the decryption | Unverified. Unofficial use |
| KuGou | Unofficial; encrypted KRC format ([lrcmux decode.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/providers/kugou/decode.go)) | Same. lrcmux's `/sources` notes it "censors profanity" | Unverified. Unofficial use |
| Musixmatch | Canticle mints an unofficial token; lrcmux gets plain text only | Token can be revoked | Its API terms have clauses Canticle lists as "unaddressed" ([provider-terms.md](https://github.com/sydlexius/canticle/blob/main/docs/provider-terms.md)) |
| Petit Lyrics (SyncPower) | Through Canticle only | Unofficial client | Per Canticle's reading of the [Japanese terms](https://petitlyrics.com/contents/kiyaku): personal, non-commercial use only; providing lyrics to third parties is prohibited ([provider-terms.md](https://github.com/sydlexius/canticle/blob/main/docs/provider-terms.md)). Personal use here fits; not read first-hand |
| Apple Music | nd-lyrics only | | Needs a paid subscription: excluded by brief 17 |

## Manual web UI

Researched 2026-11-03 for the chosen manual workflow: a self-hosted page on homelab for searching and downloading a synced `.lrc` from the Chinese and Japanese sources by hand. It should write nothing to the library, or write only on an explicit click and never retag or overwrite.

### lrcmux frontend

The frontend is a SvelteKit app in the same repo ([frontend/](https://github.com/f1nniboy/lrcmux/tree/main/frontend)), built with the Node adapter and published as `ghcr.io/f1nniboy/lrcmux-frontend` ([svelte.config.js](https://github.com/f1nniboy/lrcmux/blob/main/frontend/svelte.config.js), [Dockerfile](https://github.com/f1nniboy/lrcmux/blob/main/Dockerfile)). It is what lrcmux.dev runs.

**What it can do** (read from `main` on 2026-11-03):
- **Search goes through Deezer's catalog, not the lyrics sources.** The search box calls the frontend's `/api/search`, which queries `api.deezer.com/search` and returns up to 5 tracks (artist, title, album, duration, cover) ([api/search/+server.ts](https://github.com/f1nniboy/lrcmux/blob/main/frontend/src/routes/api/search/%2Bserver.ts), [deezer.ts](https://github.com/f1nniboy/lrcmux/blob/main/frontend/src/lib/deezer.ts), [SearchBar.svelte](https://github.com/f1nniboy/lrcmux/blob/main/frontend/src/components/SearchBar.svelte)). A song not on Deezer can't be found from the search box.
  - On 2026-11-03, `lrcmux.dev/api/search` found ヨルシカ ただ君に晴れ under its kanji name, but only karaoke and music-box covers for "Yorushika Tada Kimi ni Hare".
  - For "周杰倫 晴天" it returned a piano cover, and for "陳奕迅 十年" a different Eason Chan song. Jay Chou's own catalog didn't show up.
- **Workaround: type the song page's address.** The song page is `/s/<artist>/<title>`, with spaces written as `-` and everything else URL-encoded ([slug.ts](https://github.com/f1nniboy/lrcmux/blob/main/frontend/src/lib/slug.ts)), so `/s/周杰倫/晴天` works without Deezer. The artist page (`/s/<artist>`) lists Deezer's top tracks for that artist.
- **One result, from the race winner.** The song page asks the API `/get?artist=…&title=…` with no album, duration or source ([s/[artist]/[title]/+page.svelte](https://github.com/f1nniboy/lrcmux/blob/main/frontend/src/routes/s/%5Bartist%5D/%5Btitle%5D/%2Bpage.svelte)). It shows the one result lrcmux picked: the first source to return line-synced lyrics (see [lrcmux](#lrcmux)). The page names that source. There's no list of candidates, no way to choose NetEase vs KuGou vs LRCLIB, and no duration check, so a live or alternate version can win.
- **Preview:** the full lyrics, with line timestamps when synced ([Lyrics.svelte](https://github.com/f1nniboy/lrcmux/blob/main/frontend/src/components/Lyrics.svelte)). Copying the text from the page leaves the timestamps out, by design (comment in the same file).
- **Download:** a menu offers LRC, Enhanced LRC (word-level), SRT, WebVTT, plain text and JSON, as far as the result's sync level allows. Each item is a link to the API's `/get?…&format=…&download=true` ([DownloadMenu.svelte](https://github.com/f1nniboy/lrcmux/blob/main/frontend/src/components/DownloadMenu.svelte)). **This menu is only on `main`** (the site redesign, commit of 2026-11-03). The v1.7.0 song page has no download button ([v1.7.0 page](https://github.com/f1nniboy/lrcmux/blob/v1.7.0/frontend/src/routes/s/%5Bartist%5D/%5Btitle%5D/%2Bpage.svelte)).
- **No album search, no album download.** The routes are home, search, artist, song, docs and llms.txt ([routes/](https://github.com/f1nniboy/lrcmux/tree/main/frontend/src/routes)).
- **Japanese and Chinese text:** shown and passed through as-is. The slug code URL-encodes every character, and lrcmux's normalising keeps kana and dakuten ([normalize.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/normalize/normalize.go)). There's no Simplified/Traditional conversion. **No translation or romanisation:** the result has one set of lines. Whatever a source returns is what you get, so original script is the normal case (lrcmux.dev returned kanji/kana for ヨルシカ ただ君に晴れ, via KuGou, word-synced).
- **Per-source downloads via the API.** The API itself takes `sources=`, `duration=` and `album=` ([handler.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/api/handler.go)). So `https://<api>/get?artist=周杰倫&title=晴天&duration=270&sources=netease&format=lrc&download=true` in the browser picks a source by hand, without the frontend. The frontend's `/docs` page renders the API reference from `/openapi`.

**Images.** The Docker workflow builds both images only on version tags or a manual run ([docker.yml](https://github.com/f1nniboy/lrcmux/blob/main/.github/workflows/docker.yml)).
- `1.7.0` (2026-07-27) is the newest image, and it lacks the download menu. GHCR also lists a `main` tag and short-SHA tags. Which commit `main` is is Unverified.
- To get the download menu before a 1.8.0 release, build the `frontend` target from a pinned commit: `docker build --target frontend -t lrcmux-frontend:<sha> https://github.com/f1nniboy/lrcmux.git#<sha>`. Not tried.
- v1.7.0 has a Plausible analytics proxy, which is active only when `PLAUSIBLE_KEY` is set ([x/script.js](https://github.com/f1nniboy/lrcmux/blob/v1.7.0/frontend/src/routes/x/script.js/%2Bserver.ts)). `main` removed it. Leave `PLAUSIBLE_KEY` unset.

**Deployment.** It needs the API next to it, nothing else: Redis is optional, and there are no secrets.
- The frontend reads two variables at runtime: `API_URL`, which the frontend server uses for `/sources` on the home page, and `PUBLIC_API_URL`, which the **browser** uses for lyrics and downloads ([lib/server/env.ts](https://github.com/f1nniboy/lrcmux/blob/main/frontend/src/lib/server/env.ts), [lib/env.ts](https://github.com/f1nniboy/lrcmux/blob/main/frontend/src/lib/env.ts)).
- So the API needs its own Caddy hostname. The API sends `Access-Control-Allow-Origin: *` ([middleware.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/api/middleware.go)).
- The frontend server calls `api.deezer.com` for search and artist pages. On `main` it also calls GitHub Sponsors, Liberapay and frankfurter.dev for its support-dialog totals ([api/support/+server.ts](https://github.com/f1nniboy/lrcmux/blob/main/frontend/src/routes/api/support/%2Bserver.ts)).
- Ports 5413 and 5414 below are picked to avoid 3000, 5411 and 5412. Whether they are free is Unverified.

```yaml
# ~/docker/lrcmux/docker-compose.yml
services:
  lrcmux-api:
    image: ghcr.io/f1nniboy/lrcmux-api:1.7.0
    container_name: lrcmux-api
    restart: unless-stopped
    ports:
      - "127.0.0.1:5413:8080"
    volumes:
      - ./config.toml:/etc/lrcmux/config.toml:ro   # as in Part 2 above; keep lrclib, netease, kugou on

  lrcmux-frontend:
    image: ghcr.io/f1nniboy/lrcmux-frontend:1.7.0  # no download menu; see "Images" for a build from main
    container_name: lrcmux-frontend
    restart: unless-stopped
    depends_on: [lrcmux-api]
    ports:
      - "127.0.0.1:5414:3000"                      # adapter-node listens on 3000 inside the container
    environment:
      API_URL: http://lrcmux-api:8080              # server-side calls
      PUBLIC_API_URL: https://lrcmux-api.example.com   # browser-side calls; must be reachable from the browser
      # PLAUSIBLE_KEY: unset, so no analytics
```

- **Caddy:** `@lrcmux host lrcmux.example.com` → `reverse_proxy localhost:5414`, and `@lrcmuxapi host lrcmux-api.example.com` → `reverse_proxy localhost:5413` ([Caddy](../services/caddy.md)). The hostnames are new and Unverified. lrcmux has no login. It's tailnet-only like everything else, so that's acceptable, but anyone on the tailnet can use it.
- SvelteKit's Node adapter may want `ORIGIN=https://lrcmux.example.com` behind a proxy. The frontend has no form actions, so it's probably not needed (Unverified).
- It writes nothing to the library and needs no music mount.
- Coverage is lrcmux's: no QQ Music. Whether NetEase answers requests from the host's IP is Unverified. lrcmux.dev, which has NetEase off, returned 404 for 周杰倫 晴天 and 陳奕迅 十年 on 2026-11-03 but found ヨルシカ ただ君に晴れ (Unverified for a self-hosted run).

### Other web UIs

None found that searches QQ Music, KuGou or NetEase by hand and downloads a synced `.lrc`, besides lrcmux.

- **LRCGET web, pointed at a self-hosted lrcmux** (the runner-up setup above). This gives a library-aware web UI: pick a track, search, preview, and save a sidecar next to it on a click. But the "LRCLIB instance" setting is global, the compat search returns at most one result ([lrclib.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/api/lrclib.go)), and saving replaces the track's existing `.lrc`/`.txt` ([export.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/export.rs)). Use it only on tracks with no lyrics. Untested.
- **LDDC's Flutter branch has a web target, but with no sources.** On the web build every source is a stub ("KG 在 Web 平台暂不支持", "QM 在 Web 平台不可用", likewise NE and LRCLIB) ([lyrics_http_transport_web.dart](https://github.com/chenmozhijin/LDDC/blob/flutter/packages/lddc_lyrics_runtime/lib/src/api/lyrics_sources/lyrics_http_transport_web.dart)). The search, local-match and open-lyrics pages are marked unsupported there ([app_feature_scopes_web.dart](https://github.com/chenmozhijin/LDDC/blob/flutter/lddc/lib/src/app/app_feature_scopes_web.dart)). There is no server mode.
- **LrcApi:** its web pages are a support/donation page and a file manager (`/file`, upload, download), not a lyric search ([index.html](https://github.com/HisAtri/LrcApi/blob/main/src/index.html), [api/file.py](https://github.com/HisAtri/LrcApi/blob/main/api/file.py)). It also has a `/tag` endpoint that writes tags ([api/tag.py](https://github.com/HisAtri/LrcApi/blob/main/api/tag.py)). Ruled out.
- **music-tag-web:** it has a per-track lyric search, but saving goes through the tag writer (`f["lyrics"] = …` then `f.save()`). The optional `.lrc` is opened with `"w"`, so it overwrites ([update_ids.py](https://github.com/xhongc/music-tag-web/blob/dev_1.0/applications/task/services/update_ids.py)). Whether its UI is useful read-only, to view and copy a lyric with a read-only mount, is Unverified. Ruled out.
- **Canticle:** its web UI has a queue, reports, marking and an offset editor, but no search-a-source-and-pick page ([USER_GUIDE.md](https://github.com/sydlexius/canticle/blob/main/docs/USER_GUIDE.md)). Ruled out for this question.
- **Navidrome web UI** doesn't show plugin lyrics ([nd-lyrics README](https://github.com/J0R6IT0/navidrome-lyrics-plugin#readme)). **Feishin's Docker/web build** (`ghcr.io/jeffvli/feishin`, 10 327 stars, v1.17.0) is a player. Its README says the *desktop* client "includes built-in fetching for lyrics", which implies the web build doesn't ([README](https://github.com/jeffvli/feishin#readme)). Neither downloads files.
- **[lyricbridge](https://github.com/wang1zhen/lyricbridge)** (Python + Flet, NetEase and QQ, song/album/playlist queries, LRC export; 0 stars, last push 2026-01-07, AUR `lyricbridge`). Flet apps can usually be served to a browser, which would make it a self-hosted album downloader. But it exports to a folder on the machine running it, and its web mode is untested and undocumented (Unverified). Too new to rely on.
- **[ZonyLrcToolsX](https://github.com/real-zony/ZonyLrcToolsX)** (1795 stars, alpha release 2026-01-08, AUR `zonylrctoolsx-bin`): a cross-platform CLI with NetEase, QQ, KuGou and KuWo providers and album providers for NetEase and QQ ([source tree](https://github.com/real-zony/ZonyLrcToolsX/tree/dev/src/ZonyLrcTools.Common)). It's not a web UI. Its overwrite behaviour wasn't checked. Noted as a desktop alternative only.

## Manual fallback

For an album no source matched automatically, download the album's lyrics in one go and pair them with the pairing script.

**Best tool: LDDC** ([chenmozhijin/LDDC](https://github.com/chenmozhijin/LDDC), 1873 stars, 39 open, v0.9.2 released 2025-06-23). It is a desktop app (PySide6, Windows/macOS/Linux). It searches QQ Music, KuGou and NetEase "single songs, albums and playlists" and also fetches from LRCLIB. It does "one-click lyrics download for a whole album or playlist", and its local-folder matching writes lyrics for local files ([README](https://github.com/chenmozhijin/LDDC#readme), in Chinese). Three Chinese sources plus LRCLIB, word-level timing and an original-only option make it the best fit for Japanese and Chinese. It has **no CLI, headless or Docker mode**: its only arguments are `--get-service-port` and `--not-show`, and `__main__.py` always starts a Qt app ([args.py](https://github.com/chenmozhijin/LDDC/blob/main/LDDC/common/args.py), [\_\_main\_\_.py](https://github.com/chenmozhijin/LDDC/blob/main/LDDC/__main__.py)). Development has moved to a `flutter` branch (last commit 2026-10-16). `main`'s last commit is 2025-06-24.

How to use it (UI labels from the README and source, exact wording Unverified):
1. On a desktop, search the album by name in its native script on QQ Music or KuGou first (best for Japanese), then NetEase. Open the album result.
2. In the lyric options, choose **original only** and **line-by-line LRC**, then save the album's lyrics to an empty folder.
3. Copy the folder to the host next to the album, e.g. `~/lrc-in/<Artist - Album>/`, and run the pairing script dry, then with `--apply`.

LDDC's own local match (point it at the album folder over a share) is an alternative to the script. It scores title/artist/album similarity against a minimum score (55–60 by default), ignores results more than 4 s off in duration, and can skip tracks that already have lyrics ([auto_fetch.py](https://github.com/chenmozhijin/LDDC/blob/main/LDDC/core/auto_fetch.py), [local_match.py](https://github.com/chenmozhijin/LDDC/blob/main/LDDC/gui/workers/local_match.py)). That's fuzzy and writes without review, so it fits brief 19 only if the user checks each album afterwards.

**Alternative: 163MusicLyrics** ([jitwxs/163MusicLyrics](https://github.com/jitwxs/163MusicLyrics), 4185 stars, 36 open, v7.4 released 2026-10-31 with a `linux-x64` build). It is a desktop app for NetEase and QQ Music, with album search by ID or URL, batch save and a folder scan ([README](https://github.com/jitwxs/163MusicLyrics#readme)). Set "Chinese Text" to Ignore so it doesn't convert. It has no KuGou and no LRCLIB.

### Manual workflow, end to end

**(a) LDDC on the desktop (the chosen path).**
1. **Install on Arch:** AUR `lddc-bin` (0.9.2-2, last updated 2026-02-07, from the AUR RPC on 2026-11-03), or the upstream `.deb` from the [v0.9.2 release](https://github.com/chenmozhijin/LDDC/releases/tag/v0.9.2). The AUR package is a third-party repackage of upstream's binary.
2. **Find it:** search in native script. For romaji-tagged albums, look up the native names first (MusicBrainz artist aliases, see [Matching aids](#matching-aids-romaji--kanji)). Try QQ Music or KuGou first for Japanese, NetEase or QQ for Chinese. Set lyric content to **original only** and the format to **line-by-line LRC** (labels Unverified).
3. **Save:**
   - *One track:* open the song result, preview, save one `.lrc` into `~/lrc-in/<Artist - Album>/` on the desktop.
   - *Whole album:* open the album result and save all its lyrics into that folder.
4. **Copy to the host** over the tailnet, e.g. `rsync -av ~/lrc-in/"<Artist - Album>"/ homelab:lrc-in/"<Artist - Album>"/`. The SSH host name is Unverified; `scp -r` works the same.
5. **Pair on the host:** run the pairing script dry, check every line (especially "check it" pairs), then run it with `--apply`. For one track this is still the safest path: it finds the right file name, writes `.txt` if the file has no timestamps, and refuses to overwrite. For an album, it also lists tracks the download didn't cover (bonus tracks, other editions).
6. Navidrome picks the file up the next time a client asks for that track's lyrics; no rescan is needed.

**(b) The lrcmux web UI.**
1. **Find it:** use the search box (Deezer catalog), or type `https://lrcmux.example.com/s/<artist>/<title>` for songs Deezer doesn't have. Native script gives the best hits.
2. **Check the preview:** script, version, and the source named on the page.
3. **Download:**
   - *One track:* on `main` builds, Download → LRC. On 1.7.0, or to pick a source, open the API link directly: `https://lrcmux-api.example.com/get?artist=…&title=…&duration=<seconds>&sources=netease&format=lrc&download=true`. The file lands on whatever device the browser runs on. Copy it to `~/lrc-in/<Artist - Album>/` on the host and pair as in (a) step 5.
   - *Direct, on the host:* `curl -fsS -G http://127.0.0.1:5413/get --data-urlencode "artist=…" --data-urlencode "title=…" -d duration=<s> -d sources=netease -d format=lrc -o ~/lrc-in/"<Artist - Album>"/"<NN> <title>.lrc"`, then the pairing script. This skips the browser. `curl -o` overwrites only the file in `~/lrc-in`, never the library.
   - *Whole album:* there's no album mode. Either do one track at a time, or loop on the host over the album's files: read title, artist and duration with `ffprobe`, call the curl line above per track, then run the pairing script. A sketch only, not written. Every result is lrcmux's single pick, so read the dry run carefully.
4. **No direct write to the library** from the lrcmux UI. The only web option that writes next to the track on a click is LRCGET web pointed at lrcmux (see [Other web UIs](#other-web-uis)), and it replaces existing sidecars.

**One track vs a whole album:** the copy and pair steps are the same. What differs is the download: LDDC saves a whole album in one action, while lrcmux needs one request per track. For albums, (a) is clearly better. (b) is for a quick single track from a phone or laptop without LDDC.

### Pairing script

Save as `~/bin/pair-lrc.py` on the host (or anywhere). Python 3 stdlib plus `ffprobe` (from ffmpeg) for tags and durations, so no mutagen. Whether ffmpeg is installed on homelab is Unverified. Run it on one album folder and the folder of downloaded `.lrc` files:

```sh
python3 ~/bin/pair-lrc.py "/mnt/hdd-4tb/media/music/<Artist - Album>" ~/lrc-in/"<Artist - Album>"           # dry run
python3 ~/bin/pair-lrc.py "/mnt/hdd-4tb/media/music/<Artist - Album>" ~/lrc-in/"<Artist - Album>" --apply   # write
```

How it pairs, in order. Each step only takes one-to-one matches; anything left goes to the next step, and anything left at the end is printed on both sides.
1. **Track number:** the audio's `track`/`tracknumber` tag against a leading number in the `.lrc` file name (`03 - x`, `03.x`, `1-03 x`). Skipped for a number that appears twice on either side, or when `[length:]` disagrees with the track by more than 2 s.
2. **Title:** NFKC, case-fold and strip punctuation/symbols/spaces on both sides. The `.lrc` side tries its `[ti:]` tag, its file name without the number, and the part after the last ` - `.
3. **Duration:** `[length:]` within ±2 s of the track. If a file has no `[length:]`, it falls back to its last timestamp, which comes *before* the end of the song. That is accepted when the track ends between 2 s before and `--tail` seconds (default 20) after it, and the line says "check it". This is wider than the brief's ±2 s, because a last timestamp never equals the song length.

It writes `<track>.lrc`, or `<track>.txt` with the `[xx:]` header lines removed when the file has no timestamps, as UTF-8. It never overwrites: a track that already has a `.lrc` or `.txt` is skipped before pairing, and files are opened in exclusive-create mode. Files not in UTF-8/UTF-16 (GBK, Shift-JIS) are reported, not guessed at. It exits 1 if anything is left unpaired. It has been run only on synthetic test files in a scratch folder (2026-11-03), not on the library.

```python
#!/usr/bin/env python3
"""pair-lrc: give downloaded .lrc files the names of the tracks they belong to.

Usage: pair-lrc.py ALBUM_DIR LRC_DIR [--apply] [--move] [--tail SECONDS]

Pairs each .lrc in LRC_DIR with one .flac/.mp3 in ALBUM_DIR: by track number,
then by normalised title, then by duration. Dry run unless --apply.
--apply writes <track>.lrc (or <track>.txt for a file with no timestamps)
next to the track as UTF-8; --move also deletes the source .lrc afterwards.
Never overwrites: a track that already has a .lrc or .txt is skipped.
Needs ffprobe (part of ffmpeg) on PATH. Python 3.8+, stdlib only.
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

AUDIO_EXT = {".flac", ".mp3"}
TOL = 2.0  # seconds, for [length:] against the track's duration

TIME_TAG = re.compile(r"\[(\d+):(\d{1,2}(?:[.:]\d{1,3})?)\]")
LENGTH_TAG = re.compile(r"^\[length:\s*(\d+):(\d{1,2}(?:\.\d+)?)\s*\]", re.I | re.M)
TITLE_TAG = re.compile(r"^\[ti:(.*)\]\s*$", re.I | re.M)
META_LINE = re.compile(r"^\[[a-z#]+:.*\]\s*$", re.I)
# "03 - x", "03.x", "1-03 x" (disc-track); not "1999 - x"
LEADING_NO = re.compile(r"^\s*(?:\d{1,2}-)?(\d{1,3})(?=[\s._)\]-]|$)[\s._)\]-]*")


def norm(s):
    """NFKC, case-fold, drop punctuation, symbols, spaces and control chars."""
    s = unicodedata.normalize("NFKC", s or "").casefold()
    s = "".join(c for c in s if unicodedata.category(c)[0] not in "PSZC")
    return s or None


def seconds(m, s):
    return int(m) * 60 + float(s.replace(":", "."))


class Track:
    def __init__(self, path):
        self.path = path
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "format=duration:format_tags:stream_tags",
             "-of", "json", str(path)],
            capture_output=True, check=True).stdout
        data = json.loads(out)
        tags = {}
        for st in data.get("streams", []):
            tags.update({k.lower(): v for k, v in (st.get("tags") or {}).items()})
        fmt = data.get("format", {})
        tags.update({k.lower(): v for k, v in (fmt.get("tags") or {}).items()})
        m = re.match(r"\s*(\d+)", tags.get("track") or tags.get("tracknumber") or "")
        self.number = int(m.group(1)) if m else None
        self.title = tags.get("title")
        self.tnorm = norm(self.title)
        self.duration = float(fmt["duration"]) if fmt.get("duration") else None


class Lrc:
    def __init__(self, path):
        self.path = path
        raw = path.read_bytes()
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            self.text = raw.decode("utf-16")
        else:
            self.text = raw.decode("utf-8-sig")  # raises on GBK/Shift-JIS: caught by caller
        stem = path.stem
        m = LEADING_NO.match(stem)
        self.number = int(m.group(1)) if m else None
        rest = stem[m.end():] if m else stem
        names = [rest, rest.rsplit(" - ", 1)[-1]]
        t = TITLE_TAG.search(self.text)
        if t:
            names.append(t.group(1).strip())
        self.titles = {n for n in map(norm, names) if n}
        ln = LENGTH_TAG.search(self.text)
        self.length = seconds(*ln.groups()) if ln else None
        stamps = [seconds(a, b) for a, b in TIME_TAG.findall(self.text)]
        self.last = max(stamps) if stamps else None
        self.synced = bool(stamps)


def dur_ok(track, lrc, tail):
    """True/False when durations can be compared, None when they can't."""
    if track.duration is None:
        return None
    if lrc.length is not None:
        return abs(track.duration - lrc.length) <= TOL
    if lrc.last is not None:  # last line starts before the track ends
        return -TOL <= track.duration - lrc.last <= tail
    return None


def pair(tracks, lrcs, tail):
    pairs, notes = [], []
    tracks, lrcs = list(tracks), list(lrcs)

    def take(t, l, how):
        pairs.append((t, l, how))
        tracks.remove(t)
        lrcs.remove(l)

    # 1. track number, only where the number is unique on both sides
    for n in sorted({t.number for t in tracks if t.number is not None}):
        ts = [t for t in tracks if t.number == n]
        ls = [l for l in lrcs if l.number == n]
        if len(ts) == 1 and len(ls) == 1:
            if dur_ok(ts[0], ls[0], tail) is False:
                notes.append(f"track {n}: numbers match but durations don't, left for title/duration")
            else:
                take(ts[0], ls[0], f"track number {n}")

    # 2. normalised title, only one-to-one
    def by_title(l):
        return [t for t in tracks if t.tnorm and t.tnorm in l.titles
                and dur_ok(t, l, tail) is not False]
    cands = {l: by_title(l) for l in lrcs}
    for l, ts in cands.items():
        if len(ts) == 1 and sum(ts[0] in other for other in cands.values()) == 1:
            take(ts[0], l, "title")

    # 3. duration, only one-to-one
    cands = {l: [t for t in tracks if dur_ok(t, l, tail)] for l in lrcs}
    for l, ts in cands.items():
        if len(ts) == 1 and sum(ts[0] in other for other in cands.values()) == 1:
            how = "duration" if l.length is not None else "duration of last line only, check it"
            take(ts[0], l, how)

    return pairs, tracks, lrcs, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("album_dir", type=Path)
    ap.add_argument("lrc_dir", type=Path)
    ap.add_argument("--apply", action="store_true", help="write the sidecars")
    ap.add_argument("--move", action="store_true", help="with --apply, delete each used .lrc")
    ap.add_argument("--tail", type=float, default=20.0,
                    help="seconds allowed after the last timestamp when there is no [length:] (default 20)")
    args = ap.parse_args()
    sys.stdout.reconfigure(errors="backslashreplace")

    tracks = []
    for p in sorted(args.album_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in AUDIO_EXT:
            try:
                tracks.append(Track(p))
            except FileNotFoundError:
                sys.exit("ffprobe not found: install ffmpeg")
            except (subprocess.CalledProcessError, ValueError) as e:
                print(f"SKIP audio (ffprobe failed): {p.name}: {e}")
    lrcs = []
    for p in sorted(args.lrc_dir.iterdir()):
        if p.is_file() and p.suffix.lower() == ".lrc":
            try:
                lrcs.append(Lrc(p))
            except UnicodeDecodeError:
                print(f"SKIP lrc (not UTF-8/UTF-16, re-save it as UTF-8): {p.name}")

    stems = [t.path.stem for t in tracks]
    free = []
    for t in tracks:  # a track that has a sidecar is never touched, so it takes no part
        existing = [s for s in (".lrc", ".txt") if t.path.with_suffix(s).exists()]
        if existing:
            print(f"SKIP {t.path.name}: already has {'/'.join(existing)}")
        else:
            free.append(t)
    pairs, left_t, left_l, notes = pair(free, lrcs, args.tail)
    for n in notes:
        print(f"NOTE {n}")

    written = 0
    for t, l, how in pairs:
        dest = t.path.with_suffix(".lrc" if l.synced else ".txt")
        if stems.count(t.path.stem) > 1:
            print(f"SKIP {t.path.name}: another track has the same name before the extension")
            continue
        text = l.text if l.synced else "\n".join(
            x for x in l.text.splitlines() if not META_LINE.match(x)) + "\n"
        verb = "WRITE" if args.apply else "WOULD WRITE"
        print(f"{verb} {dest.name}  <-  {l.path.name}  (by {how})")
        if args.apply:
            try:
                with open(dest, "x", encoding="utf-8", newline="") as f:  # "x": fail if it exists
                    f.write(text)
            except FileExistsError:
                print(f"SKIP {dest.name}: appeared while running")
                continue
            written += 1
            if args.move:
                l.path.unlink()

    for t in left_t:
        secs = f"{t.duration:.0f} s" if t.duration else "no duration"
        print(f"UNPAIRED audio: {t.path.name}  (track {t.number}, title {t.title!r}, {secs})")
    for l in left_l:
        print(f"UNPAIRED lrc:   {l.path.name}  (track {l.number}, length {l.length}, last line {l.last})")
    if not args.apply:
        print("Dry run: nothing written. Add --apply to write.")
    else:
        print(f"Wrote {written} file(s).")
    return 1 if (left_t or left_l) else 0


if __name__ == "__main__":
    sys.exit(main())
```

Undo: the dry run prints every file it would write. After `--apply`, delete those `.lrc`/`.txt` files; without `--move` the downloads are still in the input folder.

## Candidates

### LRCGET and its server builds

- **Upstream** [tranxuanthang/lrcget](https://github.com/tranxuanthang/lrcget): desktop (Tauri) only. "LRCGET is the official client of LRCLIB" ([README](https://github.com/ellemarks/lrcget-web#lrcget)). 3324 stars, 202 open, 2.2.1 released 2026-10-24, pushed 2026-11-03.
- **[ellemarks/lrcget-web](https://github.com/ellemarks/lrcget-web):** fork with a headless HTTP server and the same UI. Image `ghcr.io/ellemarks/lrcget-web`, amd64 and arm64. 23 stars, 0 open. No commits since the server work on 2026-10-24 ("Add self-hosted web server alongside the Tauri desktop app", "Run bulk download/export queues on the server"). Part 1 of the recommendation.
- **Custom LRCLIB instance:** yes. Settings has an "LRCLIB instance" field ([Config.vue](https://github.com/ellemarks/lrcget-web/blob/main/src/components/library/Config.vue)). Every request is `<instance>` + `/api/get`, `/api/search`, `/api/get/{id}`, `/api/publish` or `/api/flag`, with only a trailing slash trimmed ([client.rs](https://github.com/ellemarks/lrcget-web/blob/main/src-tauri/src/lrclib/client.rs)). So a base URL with a path, like `http://127.0.0.1:5412/compat/lrclib`, works by construction (Unverified in practice). That's the runner-up.
- **[Gtt1229/docker-lrcget](https://github.com/Gtt1229/docker-lrcget)** and **[crywolf203/lrcget-unraid](https://github.com/crywolf203/lrcget-unraid)** run the desktop app in a browser-reachable container (numbers from 2026-10-30). Neither can be scripted.
- **[diego-ninja/lrcget-cli](https://github.com/diego-ninja/lrcget-cli):** ruled out on 2026-10-30 (no commits since 2025-09, watch-mode panics on non-ASCII paths [#9](https://github.com/diego-ninja/lrcget-cli/issues/9), [#18](https://github.com/diego-ninja/lrcget-cli/issues/18)).

### lrcmux

- [f1nniboy/lrcmux](https://github.com/f1nniboy/lrcmux): Go, MIT, created 2026-06-27, 46 stars, 1 open, 1 contributor, v1.7.0 released 2026-07-27, pushed 2026-11-03. A public instance runs at lrcmux.dev. Images `ghcr.io/f1nniboy/lrcmux-api` (tags 1.2.0–1.7.0, `latest`, `main`) and `ghcr.io/f1nniboy/lrcmux-frontend`.
- Providers in the code: Deezer, Genius, KuGou, LRCLIB, Musixmatch, NetEase, YouTube Music ([providers/](https://github.com/f1nniboy/lrcmux/tree/main/internal/providers)). It has no QQ Music and no Petit Lyrics.
- **LRCLIB-compatible endpoints:** `GET /compat/lrclib/api/get` and `GET /compat/lrclib/api/search`, the latter added 2026-07-06 ([lrclib.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/api/lrclib.go)). The search returns at most one result. There is no `/api/get/{id}` or `/api/publish`, so LRCGET's publish button and lookup-by-ID wouldn't work behind it.
- **How it picks:** all providers that can reach the requested sync level are asked at once, and the first result that is line-synced (or better), not instrumental and not censored cancels the rest ([fanout.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/orchestrator/fanout.go), [rank.go](https://github.com/f1nniboy/lrcmux/blob/main/internal/orchestrator/rank.go)). So the fastest source wins, not LRCLIB. That's why the runner-up doesn't meet brief 17's "LRCLIB first", and why part 3 asks one source at a time.
- Its newest commit (2026-11-03) is "send a browser user agent by default" for providers, so lrcmux's own LRCLIB requests may count as a generic client (~45/min) rather than an identified one (Unverified).
- **beets** already has an `lrcmux` source with a configurable `url` ([lyrics.py](https://github.com/beetbox/beets/blob/master/beetsplug/lyrics.py)). **[otaviocc/lyrics](https://github.com/otaviocc/lyrics)** (Rust, 3 stars, pushed 2026-10-20) writes sidecars from LRCLIB or lrcmux. It's too new to rank.

### Canticle (formerly mxlrcgo-svc)

- The repo is now [sydlexius/canticle](https://github.com/sydlexius/canticle) (the old name redirects). v1.51.1 released 2026-11-02, 1 star, 152 open, created 2026-03-13. Image `ghcr.io/sydlexius/canticle`.
- Serve mode runs a periodic scan (`hourly`/`daily`/`weekly`) and an optional watcher. It writes `.lrc`, or `.txt` for unsynced lyrics or an instrumental marker ([README](https://github.com/sydlexius/canticle#readme), [CONFIGURATION.md](https://github.com/sydlexius/canticle/blob/main/docs/CONFIGURATION.md)). It adopts existing sidecars into its queue rather than replacing them ([USER_GUIDE.md](https://github.com/sydlexius/canticle/blob/main/docs/USER_GUIDE.md)).
- **Sources:** primary `musixmatch` by default; Petit Lyrics and InnerTube (YouTube Music) are alternative lanes, `ordered` by default ([multi-provider-orchestration.md](https://github.com/sydlexius/canticle/blob/main/docs/multi-provider-orchestration.md)). A tokenless Japanese-first setup is `primary = "petitlyrics"`, with `fallback_order` holding innertube. Whether that leaves Musixmatch out entirely is Unverified. The repo tree has a `petitlyrics` package and nothing for LRCLIB, NetEase, QQ or KuGou.
- **Conflicts:** the web UI (off by default, `web_ui_enabled`) has queue buckets, a "Needs attention" list of failed/deferred tracks, a "Lyrics are wrong" flag, and a lyric preview with a timing editor ([USER_GUIDE.md](https://github.com/sydlexius/canticle/blob/main/docs/USER_GUIDE.md)). It doesn't show competing candidates to choose from (none found in its docs).
- Optional sidecars (Whisper verification, YAMNet instrumental detection, forced alignment) are off by default.

### beets `lyrics` plugin

- Defaults: `sources: [lrclib, google, genius, lrcmux]`, `synced: no`, `dist_thresh: 0.11` ([docs](https://beets.readthedocs.io/en/stable/plugins/lyrics.html)). The `lrcmux` source takes `url` and `sources` options ([lyrics.py](https://github.com/beetbox/beets/blob/master/beetsplug/lyrics.py)).
- **Writes tags, not files**, until [PR #7117](https://github.com/beetbox/beets/pull/7117) ("Write lyrics to sidecar files (.lrc/.txt)") merges. On 2026-11-03 it was open, not a draft, last updated 2026-10-30, with three "commented" reviews and no approval. Tracked in [issue #6396](https://github.com/beetbox/beets/issues/6396).
- MP3: synced lyrics go to `SYLT`, which Navidrome doesn't map ([PR #6566](https://github.com/beetbox/beets/pull/6566), [mappings.yaml](https://github.com/navidrome/navidrome/blob/master/resources/mappings.yaml)). Known bug [#7070](https://github.com/beetbox/beets/issues/7070) (synced dropped when the LRC ends with a blank line).
- **How it would fit if #7117 ships:** `lscr.io/linuxserver/beets`, library read-write, `import: {copy: no, move: no, write: no, autotag: no}`, `lyrics: {synced: yes, sources: [lrclib, lrcmux], lrcmux: {url: http://lrcmux:8080}, write_files: yes}`. A timer runs `beet import -A -q --incremental /music` and `beet lyrics --write-files`. No UI, no queue.

### Self-hosted Chinese tools

- **[HisAtri/LrcApi](https://github.com/HisAtri/LrcApi)** (1267 stars, 3 open, 1.6.0 released 2025-01-21, pushed 2026-08-18). A Flask lyrics API for Navidrome-style clients at `/lyrics` and `/jsonapi`, querying KuGou, NetEase and the author's hosted `api.lrc.cx` in parallel ([searchx/\_\_init\_\_.py](https://github.com/HisAtri/LrcApi/blob/main/mod/searchx/__init__.py), [lyrics.py](https://github.com/HisAtri/LrcApi/blob/main/api/lyrics.py)). It is **not LRCLIB-compatible**, so LRCGET can't use it. It also has a tag-writing endpoint. Ruled out in favour of lrcmux.
- **[xhongc/music-tag-web](https://github.com/xhongc/music-tag-web)** (6182 stars, 48 open, pushed 2026-10-08). A Docker tag editor with Chinese sources. In the published source, a `.lrc` file is written only alongside a tag update (`f["lyrics"] = …`), with `open(…, "w")`, so it overwrites ([update_ids.py](https://github.com/xhongc/music-tag-web/blob/dev_1.0/applications/task/services/update_ids.py)). It retags and overwrites, so it's ruled out. Its README points to a "V2" manual. Whether V2's code is the same is Unverified.
- **[LyricsX](https://github.com/ddddxxx/LyricsX)** (macOS app, 5245 stars) and its library [LyricsKit](https://github.com/ddddxxx/LyricsKit) (pushed 2024-02-17): macOS only, not a library fetcher.
- **[Lyricify Lyrics Helper](https://github.com/WXRIW/Lyricify-Lyrics-Helper)** (C#, 235 stars, pushed 2026-10-21): a library for lyric formats and providers, not a tool. Not looked at further.

## Play-time lyrics (no files)

Not ranked against the writers above.

- **[nd-lyrics](https://github.com/J0R6IT0/navidrome-lyrics-plugin)** (Navidrome plugin, 454 stars, 5 open, v8.1.0 released 2026-09-17, pushed 2026-10-28). It needs Navidrome ≥ v0.63.0; the latest Navidrome release is still v0.64.2 (2026-09-24). Add `nd-lyrics` to `ND_LYRICSPRIORITY` after the file sources. "The plugin will fetch lyrics only when a client requests them" ([README](https://github.com/J0R6IT0/navidrome-lyrics-plugin#readme)).
  - Providers: LRCLIB, lyrics.ovh, lrcmux, KuGou, NetEase, QQ Music, Apple Music (subscription), stixoi.info, Genie Music, BiniLyrics. Modes: priority, rotation, type priority, best sync level.
  - Matching for NetEase: search "title artist", take the first result within the duration tolerance, optionally requiring an album match ([netease/mod.rs](https://github.com/J0R6IT0/navidrome-lyrics-plugin/blob/main/src/providers/services/netease/mod.rs)). There's no romaji handling and no review.
  - It can write sidecars and won't overwrite unless `overwrite_lyrics` is on ([writing.rs](https://github.com/J0R6IT0/navidrome-lyrics-plugin/blob/main/src/writing.rs)). Navidrome's mount is read-only here, so it would need a custom path, and the results would be unreviewed. Leave writing off.
  - "The Navidrome WebUI does not display lyrics from plugins", so a Subsonic client is needed. It stays the optional second step: the one place QQ Music is used automatically.
- **[Feishin](https://github.com/jeffvli/feishin)** (desktop Navidrome client) has built-in online fetchers for LRCLIB, NetEase and Genius ([source](https://github.com/jeffvli/feishin/tree/development/src/main/features/core/lyrics)).
- Whether the iOS clients in use (play:Sub, Substreamer, Amperfy) fetch lyrics online is Unverified.

## Ruled out

- **[newtonsart/synclyr2metadata](https://github.com/newtonsart/synclyr2metadata)**: embeds into tags.
- **[Shikogoru/lyricfetcher](https://github.com/Shikogoru/lyricfetcher)**: LRCLIB + NetEase to `.lrc`, but created 2026-10-26, 0 stars, no watch mode.
- **[tappyduckmancodes/multiplatform-lyric-downloader](https://github.com/tappyduckmancodes/multiplatform-lyric-downloader)**: desktop tool driven by Spotify/Deezer playlists.
- **[jellyfin/jellyfin-plugin-lrclib](https://github.com/jellyfin/jellyfin-plugin-lrclib)**: for Jellyfin's own library. Jellyfin is video-only here.
- **[Jonny-Ponny/md-lrclib-addon](https://github.com/Jonny-Ponny/md-lrclib-addon)**: an addon for metadata-docker, 0 stars.
- **[Wilooper/Lyrica](https://github.com/Wilooper/Lyrica)**: a lyrics API, not a library fetcher.
- **lrcget-cli**: unmaintained, watch-mode crashes.
- **LrcApi, music-tag-web, LyricsX, Lyricify**: see [Self-hosted Chinese tools](#self-hosted-chinese-tools).
- **LDDC and 163MusicLyrics as automatic fetchers**: desktop only, no headless mode. Kept for the manual fallback.

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

Added 2026-11-03, for Japanese and Chinese songs and manual conflict resolution:

16. Re-rank the whole recommendation. Criteria in order: (1) automation, (2) match accuracy and synced coverage, including Japanese and Chinese songs, (3) maintenance, (4) resources, (5) web UI.
17. Sources: LRCLIB first. NetEase, QQ Music, KuGou, Musixmatch and Petit Lyrics are acceptable fallbacks; record how fragile each is and what its terms of service say. Nothing that needs a paid account.
18. Script: original script only. Translation or romanisation is a nice-to-have, noted per tool. Simplified/Traditional Chinese: keep what the source returns, and note it if a tool converts.
19. Conflicts: fuzzy-only matches, including matches found through a romaji↔kanji lookup, and disagreeing candidates go to a queue for the user. Plain-only lyrics: write the .txt automatically. Existing sidecars: never touched.
20. Resolving conflicts: a UI where the user picks a candidate ranks higher; a report or log is the minimum.
21. Tags are a mix of kanji and romaji and can't be fixed up front. Lookups (MusicBrainz aliases, the source's own search) may be used for matching only, never written to the tags.
22. Line-level sync is enough; word-level timing is a note.
23. Done when: one recommended setup, which may be a chain of tools, with a sketch of how it fits and how conflicts reach the user, plus a runner-up.
24. Manual fallback, which is always included: for albums LRCLIB doesn't have, name the best source or tool for downloading a whole album's synced .lrc files in Japanese or Chinese, plus a script that pairs the downloaded .lrc files with the .flac/.mp3 files in an album folder and renames them. It pairs by track number, then title, then duration, reports anything it can't pair, and never overwrites.

Added 2026-11-03, after the findings:

25. **Manual UI fallbacks:** the user asked which manual fallbacks have a UI. Answered in [Manual fallback](#manual-fallback) and [Manual web UI](#manual-web-ui). LDDC runs on the user's desktop, not in a container on homelab.
26. **Chosen setup:** the manual workflow instead of the automatic three-part chain. LRCGET web's automatic LRCLIB pass is kept, and the manual workflow (LDDC, then the pairing script) covers what it misses. lrcmux and the review pass are dropped.
27. **Self-hosted web UI (lrcmux frontend):** skipped for now. Reconsider when lrcmux tags a release that has the download button.
28. **More research?** No. The Unverified items (NetEase from the host's IP, LRCGET against lrcmux, LDDC's UI labels, free ports, the timer script) are settled during setup.
