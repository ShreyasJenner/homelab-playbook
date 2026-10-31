# Kavita

```
Status:     live (since 2026-08-15)
Host:       homelab
Exposure:   tailnet-only (intended); 5000 is published on 0.0.0.0, so also reachable from the home LAN
URL:        https://manga.example.com
Config:     ~/docker/kavita/ (docker-compose.yml, .env, config/)
Depends on: media/manga and media/lns on the 4 TB HDD
Per-User:   no; one instance, an account per User
Verified:   2026-10-30
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

- **Uploads from a phone** go through [Nextcloud](nextcloud.md)'s external storage (`/mnt/manga`), which needed write access for Nextcloud's uid 33 on the manga folder.
- Layout: one folder per series, volumes as CBZ. Libraries are of type Manga, pointed at `/manga` and `/lns`.
- `media/manga` and `media/lns` are in the nightly backup.
- Uptime Kuma checks `http://localhost:5000/api/health`.

## Runbooks

- [Media libraries are empty, or nothing runs, after a reboot](../runbooks/media-libraries-empty-after-reboot.md)

## Incidents

- [2026-10-02: media libraries empty after the HDD mounted late](../incidents/2026-10-02-media-libraries-empty-after-late-hdd-mount.md)
- [2026-10-30: slow to open manga under heavy traffic (server's Wi-Fi downlink at 7.3 Mbit/s)](../incidents/2026-10-30-server-wifi-downlink-stuck-at-mcs0.md)
