# Nextcloud

```
Status:     live
Host:       homelab
Exposure:   public (Funnel :10000); also on the tailnet through Caddy
URL:        https://homelab.tail0000.ts.net:10000 (public, used for share links)
            https://drive.example.com (tailnet)
Config:     ~/docker/nextcloud/ (docker-compose.yml; data/ → /var/www/html, the whole webroot including user files)
Depends on: nextcloud_db (MariaDB); Tailscale Funnel; the 4 TB HDD (external storage);
            Euro-Office for document editing; the host's LAN address (Euro-Office calls)
Per-User:   no; one instance, one account per User (plus admin)
Verified:   2026-10-28 (config, apps, mounts); compose details unverified
```

## What it's for

The homelab's Google Drive: file storage and sync through the web UI, the desktop client and the iOS app, plus share links (with optional password and expiry) that work for people outside the tailnet. Documents open and are edited in [Euro-Office](euro-office.md), including from the iOS app.

## Why this one

- The first request (2026-06) was "a home server that allows access to files like in gdrive", reachable from outside. Nextcloud is the closest self-hosted equivalent.
- On 2026-07-18 the priority was storage plus share links. **Syncthing was rejected**: it syncs, but has no share links and no web file browser.
- **MariaDB over SQLite**, which slows down as usage grows.
- **Public through Funnel** because share links and shared-document editing must work for people who aren't on the tailnet (ADR 0004).
- Alternatives were looked at again on 2026-09-14 (Seafile, ownCloud Infinite Scale, Pydio Cells and others), with no change.

## How it's set up

### Containers

Two containers from one stack:
- `nextcloud_app`: `8080→80`. Data is a bind, `~/docker/nextcloud/data → /var/www/html`.
- `nextcloud_db`: MariaDB.

From the setup notes (unverified): images `nextcloud:latest` and `mariadb:10.6`, with the database in `./db`. No Redis, so Nextcloud uses database file locking.

User files are at `~/docker/nextcloud/data/data/<user>/files/` on the host. The double `data/data` is because `./data` is the whole webroot. The app log is `data/data/nextcloud.log`.

### Settings (verified 2026-10-28)

| Setting | Value |
|---|---|
| `trusted_domains` | `192.0.2.10:8080`, `homelab.tail0000.ts.net:10000`, `localhost`, `198.51.100.10`, `drive.example.com` |
| `overwrite.cli.url` | `https://homelab.tail0000.ts.net:10000` |
| `overwriteprotocol` | `https` (`overwritehost` is empty, so both hostnames work) |
| `trusted_proxies` | `127.0.0.1`, `172.22.0.1` (the `nextcloud_default` gateway, i.e. Caddy reaching the container from the host) |

`198.51.100.10` is there because Euro-Office calls back to Nextcloud on the LAN address. If the address changes, document editing breaks ([runbook](../runbooks/document-editing-broke-after-lan-ip-change.md)).

**Enabled apps of note:**
- `eurooffice` 11.0.6: the document connector.
- `richdocumentscode`: the built-in Collabora server, a leftover kept on purpose.
- `twofactor_totp` and `twofactor_backupcodes`: installed, but **no account has enrolled in 2FA**, although the login page is public.

Retired connectors `richdocuments` and `onlyoffice` are also still installed. These leftovers are recorded, not cleaned up; see the [Collabora](collabora.md) and [ONLYOFFICE](onlyoffice.md) pages.

**Accounts** (confirmed by the user, 2026-10-28): `alice`, `Shreyas` (ShreyasJenner) and `bob` (bob). Server-side encryption is off.

### External storage

Local folders on the 4 TB HDD, mounted into `nextcloud_app` and added with the External storage app:

| Host folder (under `/mnt/hdd-4tb`) | Container path | In the nightly backup? |
|---|---|---|
| `media/manga` | `/mnt/manga` | yes |
| `media/lns` | `/mnt/lns` | yes |
| `backup/vns` | `/mnt/backup/vns` | **no** |
| `media/games` | `/mnt/games` | **no** |

Nextcloud runs as `www-data` (uid 33) inside the container, while the host folders belong to `alice` (uid 1000). A folder Nextcloud has to write to needs write access for uid 33. Both `o+w` and a shared group were applied at some point, and it isn't known which one made it work; `stat`/`getfacl` on the folders shows the current state.

To add an external folder, the path must first be mounted into `nextcloud_app` as a compose volume. In Nextcloud you then enter the container path. Apply the compose change with `sudo docker compose up -d`, not `restart`.

### Day-to-day commands

```bash
# occ, always as www-data
sudo docker exec -u www-data nextcloud_app php occ <command>

# health (what Uptime Kuma checks; "/" returns a redirect)
curl -s http://localhost:8080/status.php

# rescan after files were changed outside Nextcloud
sudo docker exec -u www-data nextcloud_app php occ files:scan --path="/<user>/files"

# app log
sudo docker exec -u www-data nextcloud_app tail -n 50 /var/www/html/data/nextcloud.log
```

**Bulk import** (when a file can't go through a client):
1. `sudo docker cp <files> nextcloud_app:/var/www/html/data/<user>/files/`
2. `sudo docker exec nextcloud_app chown -R www-data:www-data /var/www/html/data/<user>/files/`
3. `files:scan --path="/<user>/files"`

Skipping the `chown` caused the [2026-10-06 incident](../incidents/2026-10-06-nextcloud-files-imported-with-wrong-owner.md).

### Gotchas

- **Never point another service at a folder inside Nextcloud's data directory.** Paperless-ngx's consume folder did that, and it deleted every file it consumed ([2026-10-02](../incidents/2026-10-02-nextcloud-files-consumed-by-paperless.md)).
- Don't edit files under `data/data` while Nextcloud runs without running `files:scan` afterwards: the database tracks the metadata. **During a recovery, don't scan at all**, because a scan purges the file cache entries you may need.
- Don't run scans around 02:30, when the nightly backup stops every stack.
- `docker compose restart` doesn't pick up compose changes such as new volumes. Use `up -d`.
- Installing an app and restarting straight away once left Nextcloud in maintenance mode. `occ upgrade`, then `occ maintenance:mode --off`.
- Changing the server URL means changing it on every client: log out, re-add the account, and point it at the existing local folder.

## Updating

Through `stacks.sh update` (`nextcloud` is in the default list). Nextcloud doesn't support skipping major versions. If an update fails, check `occ status` and the log before anything else.

## Gaps

- **The update path is unverified.** With `:latest`, a pull can jump a major version.
- **The background jobs mode** (AJAX, Webcron or cron) has never been checked: `occ config:app:get core backgroundjobs_mode`.
- The `nextcloud_db` mounts and the image tags.

## Runbooks

- [A service URL returns 502 or closes the connection](../runbooks/service-url-returns-502.md)
- [Nextcloud can't create, move or delete files](../runbooks/nextcloud-cant-write-files.md)
- [`occ files:scan` says another process is already scanning](../runbooks/nextcloud-scan-already-running.md)
- [Document editing broke after the host's LAN address changed](../runbooks/document-editing-broke-after-lan-ip-change.md)

## Incidents

- [2026-07-19: desktop client rejected the HTTPS URL](../incidents/2026-07-19-nextcloud-client-rejects-https-url.md)
- [2026-07-19: Nextcloud 502 after turning on Funnel](../incidents/2026-07-19-nextcloud-502-after-enabling-funnel.md)
- [2026-08-05: Nextcloud 502 after re-enabling Funnel](../incidents/2026-08-05-nextcloud-502-after-re-enabling-funnel.md)
- [2026-08-14: Nextcloud down after funneling Collabora](../incidents/2026-08-14-nextcloud-down-after-funneling-collabora.md)
- [2026-08-23: external storage folder was read-only](../incidents/2026-08-23-nextcloud-external-storage-read-only.md)
- [2026-09-02: couldn't create folders in new external storage](../incidents/2026-09-02-nextcloud-external-storage-permission-denied.md)
- [2026-09-12: document editing broke after the LAN address changed](../incidents/2026-09-12-document-editing-broke-after-lan-ip-change.md)
- [2026-09-28: files:scan blocked by a stale lock](../incidents/2026-09-28-nextcloud-scan-blocked-by-stale-lock.md)
- [2026-09-30: couldn't move or delete files in external storage](../incidents/2026-09-30-nextcloud-cant-move-or-delete-files.md)
- [2026-10-02: Nextcloud's files consumed by Paperless-ngx](../incidents/2026-10-02-nextcloud-files-consumed-by-paperless.md)
- [2026-10-04: files:scan blocked by a stale lock again](../incidents/2026-10-04-nextcloud-scan-blocked-by-stale-lock-again.md)
- [2026-10-06: imported files had the wrong owner](../incidents/2026-10-06-nextcloud-files-imported-with-wrong-owner.md)
