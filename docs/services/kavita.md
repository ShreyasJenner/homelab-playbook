# Kavita

```
Status:     live (since 2026-08-15)
Host:       homelab
Exposure:   tailnet-only (intended); 5000 is published on 0.0.0.0, so also reachable from the home LAN
URL:        https://manga.example.com
Config:     ~/docker/kavita/ (docker-compose.yml, .env, config/)
Depends on: media/manga and media/lns on the 4 TB HDD
Per-User:   no; one instance, an account per User
Verified:   2026-11-02
```

## What it's for

Reading manga and light novels, through Kavita's PWA.

## Why this one

Compared with Komga, Stump, Mango and Atsumeru on 2026-08-15. Kavita handles manga, ebooks and comics in one app, with OIDC, AniList/MAL sync and OPDS. Panels (iOS) needs a paid tier for self-hosted servers, so the PWA is used instead.

## How it's set up

- Image `jvmilazz0/kavita:latest`, port `5000`, `TZ` from `.env`.
- Mounts (all read-only apart from config):

  | Host | Container |
  |---|---|
  | `~/docker/kavita/config` | `/kavita/config` |
  | `/mnt/hdd-4tb/media/manga` | `/manga` |
  | `/mnt/hdd-4tb/media/lns` | `/lns` |

- **Folder Watching is on** (Settings → General; it was off until 2026-10-31). New files are picked up within minutes without a manual scan: Tanya showed up under "Recently updated" on 2026-10-31. Per-library overrides were never touched.
- **Uploads from a phone** go through [Nextcloud](nextcloud.md)'s external storage (`/mnt/manga`), which needed write access for Nextcloud's uid 33 on the manga folder.
- **Series from chapter folders of images** are packed on the laptop by [`tools/make-cbz.py`](../../tools/make-cbz.py) (linked as `~/.local/bin/make-cbz`): one CBZ per volume, one per chapter not yet in a volume, each with a `ComicInfo.xml`, from a `series.toml` in the source folder. It writes to `./<folder>/` and prints the `rsync` to `media/manga/<folder>/`. Kavita reads `<Series> v01` and `<Series> c001` file names, and a chapter number with only one decimal digit. ComicInfo `Series` overrides the file name, so `series` must be the name Kavita already shows for that series. `Count` (set only for completed series) marks the series Completed when it equals the highest volume. Source: Kavita `develop` at `9e17770`, read 2026-11-02 (`Kavita.Services/Scanner/Parser.cs`, `ProcessSeries.cs`). Verified 2026-11-02: My Girl, packed and rsynced this way, showed in Kavita with its volumes and metadata.
- Layout: one folder per series, volumes as CBZ. Libraries are of type Manga, pointed at `/manga` and `/lns`.
- **A series must live in exactly one folder.** Kavita takes the series name from the file names, so two folders whose files parse to the same series become one series bound to one folder. Each scan drops the other folder's volumes, and the log says `Volume cleanup code was trying to remove a volume with a file still existing on disk`. Merge the files into one folder ([2026-11-01](../incidents/2026-11-01-kavita-series-split-across-two-folders.md)).
- `media/manga` and `media/lns` are in the nightly backup.
- Uptime Kuma checks `http://localhost:5000/api/health`.

## Runbooks

- [Media libraries are empty, or nothing runs, after a reboot](../runbooks/media-libraries-empty-after-reboot.md)

## Incidents

- [2026-10-02: media libraries empty after the HDD mounted late](../incidents/2026-10-02-media-libraries-empty-after-late-hdd-mount.md)
- [2026-10-30: slow to open manga under heavy traffic (server's Wi-Fi downlink at 7.3 Mbit/s)](../incidents/2026-10-30-server-wifi-downlink-stuck-at-mcs0.md)
- [2026-11-01: only the last volume showed, because the series was split across two folders](../incidents/2026-11-01-kavita-series-split-across-two-folders.md)
