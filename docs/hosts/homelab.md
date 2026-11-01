# homelab

```
Status:     live
Role:       runs every service in the homelab
Hardware:   Lenovo IdeaCentre Tower 08IAS10 (firmware M5WKT1FA, 2026-01-20)
CPU:        Intel Core Ultra 5 225
RAM:        16 GB (15 GiB usable), 15 GiB swap
OS:         Debian 13 (trixie), kernel 6.12.95+deb13-amd64
Login:      alice, SSH on port 2207
Tailnet:    homelab.tail0000.ts.net, 192.0.2.10
LAN:        198.51.100.10 (DHCP over Wi-Fi, not reserved)
Config:     ~/docker/<stack>/ (one Compose project per stack)
Verified:   2026-10-30
```

## What it's for

The home machine. Every service runs here as a Docker Compose stack.

## Why this one

The original requirements were to run Vaultwarden, Jellyfin (or Plex), Nextcloud and Vikunja at the same time on something budget-friendly, quiet, with enough storage. The chat recommended mini PCs. Why the IdeaCentre tower was chosen instead isn't recorded.

## Disks

| Disk | Device | Mount | fstab options | Holds |
|---|---|---|---|---|
| Internal NVMe, 512 GB (476.9 GiB) | `nvme0n1` | `/`, `/boot/efi`, swap | default | the OS and `~/docker` (every stack's config and data) |
| 4 TB USB HDD (3.6 TiB) | `sdb1`, ext4 | `/mnt/hdd-4tb` | `defaults,nofail,x-systemd.device-timeout=5min` (fsck pass 2) | `media/` (music, light novels, manga, TV shows, anime, movies) |
| Backup HDD, 1 TB (USB, 931.5 GiB) | `sda1`, ext4 | `/mnt/backup-hdd` | `defaults,nofail,x-systemd.device-timeout=10s` (fsck pass 0) | the restic repo (`restic-repo/`) and the `.backup-drive` marker file |

fstab mounts everything by UUID, so it doesn't matter which disk comes up as `sda` or `sdb`. There's no `x-systemd.automount`.

**Docker won't start without the 4 TB disk.** `docker.service` has `RequiresMountsFor=/mnt/hdd-4tb`. Before that was added, the disk sometimes enumerated too late at boot and the containers started against the empty mountpoint on the NVMe. Now, if the disk doesn't mount, *every* service is down, not just the media ones. The backup disk isn't required.

## Network

- **Wi-Fi only** (`wlp130s0`), DHCP from the ISP's router at `198.51.100.1`. NetworkManager manages the connection (`HomeWiFi`). The Ethernet port `enp131s0` can't be used: there's no space to run a cable to the router (user, 2026-10-30). `/etc/systemd/network/20-wired.network` exists but nothing uses it.
- **The Wi-Fi link** (verified 2026-10-30): Realtek `rtw89_8852be`, 5 GHz (5200 MHz), 80 MHz, Wi-Fi 6, 1200.9 Mbit/s each way when healthy. Signal is very strong, about `-31` to `-34 dBm` (the server is close to the router). Power save is on (NetworkManager's default). `iw` is installed for reading the rates: `iw dev wlp130s0 link`. **The router once got stuck sending to the server at 7.3 Mbit/s (HE-MCS 0)**, which made everything slow under heavy traffic; a Wi-Fi reconnect fixed it ([incident](../incidents/2026-10-30-server-wifi-downlink-stuck-at-mcs0.md)).
- **There's no admin access to the router** (user, 2026-10-30), so nothing can be configured on it: no DHCP reservation, no port forwards.
- **The LAN address isn't reserved in the router** and can't be (see above), so it can change on any DHCP renewal. It changed once already (2026-09-12). Nextcloud and Euro-Office call each other on this address, and Nextcloud's `trusted_domains` includes it, so a change breaks document editing.
- **DNS:** `/etc/resolv.conf` is a plain file with `nameserver 100.100.100.100` (Tailscale) and `nameserver 8.8.8.8`. `/etc/dhcpcd.conf` still has `nohook resolv.conf`, a leftover from the 2026-07-21 DNS fix; dhcpcd itself is inactive. On 2026-10-30, `100.100.100.100` answered `SERVFAIL` for a public name (`manga.example.com`), so public lookups on the server actually go to `8.8.8.8`.
- **[Tailscale](../services/tailscale.md)** gives the host its tailnet name and address. Under ADR 0004 every service is reached through Caddy on the tailnet, apart from three Tailscale Serve/Funnel entries:

  | Entry | Target | Exposure |
  |---|---|---|
  | `https://homelab.tail0000.ts.net:10000` | `http://localhost:8080` (Nextcloud) | public (Funnel) |
  | `https://homelab.tail0000.ts.net:8443` | `http://localhost:9917` (Euro-Office) | public (Funnel) |
  | `tcp://homelab.tail0000.ts.net:8313` | `tcp://localhost:8312` (Gitea SSH) | tailnet-only (Serve, TCP) |

- **[Caddy](../services/caddy.md)** runs in host network mode on `:80` and `:443` and routes `*.example.com` to `localhost:<port>`. `*.example.com` resolves to the server.

### Firewall (ufw)

Default deny incoming, allow outgoing, deny routed. Rules:

| Rule | Purpose |
|---|---|
| `2207/tcp` LIMIT | SSH |
| all traffic on `tailscale0` | the tailnet |
| `443/tcp on tailscale0` | Caddy |
| `3407/tcp` from `192.0.2.0/20` | leftover; no current Docker network is in that range |
| deny `1080/tcp` (v6) | leftover, probably from an abandoned SOCKS/frp attempt |

The leftovers are recorded, not cleaned up.

**ufw doesn't cover ports that Docker publishes.** Docker's own iptables rules come first, so a port published on `0.0.0.0` is reachable from the home LAN at `198.51.100.10:<port>`, bypassing Caddy and Tailscale. Host-network services (Caddy, Uptime Kuma, Homepage) are filtered correctly. See the open incident [Tailnet-only services are reachable from the home LAN](../incidents/2026-10-28-services-reachable-from-home-lan.md).

## Docker

Every stack is a Compose project in `~/docker/<stack>/`, with its config and data as bind mounts inside that folder. `~/docker` is what the nightly restic backup covers.

| Stack dir | Containers | Service pages |
|---|---|---|
| `actual-budget` | `actual-budget-actual_server-1` | [Actual Budget](../services/actual-budget.md) |
| `caddy` | `caddy` | [Caddy](../services/caddy.md) |
| `euro-office` | `euro-office` | [Euro-Office](../services/euro-office.md) |
| `gitea` | `gitea` | [Gitea](../services/gitea.md) |
| `homepage` | `homepage-homepage-a-1`, `homepage-homepage-b-1` | [Homepage](../services/homepage.md) (one instance per User) |
| `invidious` | `invidious-invidious-1`, `invidious-companion-1`, `invidious-invidious-db-1` | [Invidious](../services/invidious.md) |
| `jellyfin` | `jellyfin` | [Jellyfin](../services/jellyfin.md) |
| `kavita` | `kavita` | [Kavita](../services/kavita.md) |
| `memos` | `memos` | [Memos](../services/memos.md) |
| `mindwtr` | `mindwtr-app`, `mindwtr-cloud` | [Mindwtr](../services/mindwtr.md) |
| `monitoring` | `grafana`, `prometheus`, `loki`, `alloy`, `node-exporter`, `cadvisor` | [Monitoring stack](../services/monitoring.md) |
| `navidrome` | `navidrome` | [Navidrome](../services/navidrome.md) |
| `nextcloud` | `nextcloud_app`, `nextcloud_db` | [Nextcloud](../services/nextcloud.md) |
| `ntfy` | `ntfy` | [ntfy](../services/ntfy.md) |
| `redlib` | `redlib-shreyas`, `redlib-bob` | [Redlib](../services/redlib.md) (one instance per User) |
| `uptime-kuma` | `uptime-kuma` | [Uptime Kuma](../services/uptime-kuma.md) |
| `vaultwarden` | `vaultwarden` | [Vaultwarden](../services/vaultwarden.md) |

**Leftovers in `~/docker`** (recorded, not cleaned up): stack folders for retired, evaluated or never-run services (`authentik` ([page](../services/authentik.md)), `collabora` ([page](../services/collabora.md)), `dailytxt`, `donetick` ([page](../services/donetick.md)), `maloja` ([page](../services/maloja.md)), `materialious` ([page](../services/materialious.md)), `onlyoffice` ([page](../services/onlyoffice.md)), `paperless-ngx` ([page](../services/paperless-ngx.md)), `tududi`), `venv/`, `service-list.txt`, and a top-level `docker-compose.yml`.

### Updating: `~/docker/stacks.sh`

The procedure is in the runbook [Updating containers](../runbooks/updating-containers.md).


```
./stacks.sh <command> [stack ...]
```

Commands: `up` (`up -d`), `stop`, `down`, `restart` (doesn't pick up compose changes; use `up`), `pull`, `update` (`pull`, then `up -d`; after the loop, `docker image prune -f`), `ps`, `logs` (`-f --tail 50`), `list`. With no stack names it acts on the `DEFAULT_STACKS` list in the script. A stack that fails prints `!! <stack> failed` and the loop carries on; the exit code is 1 if anything failed.

Since 2026-10-30 (follow-up 12, verified that day), `DEFAULT_STACKS` holds every live stack (17, with `gitea` and `vaultwarden` added; `materialious` is commented out). The same day, unused images (51 GB) and build cache (20 GB) were pruned: `/` went from 170 GB to 104 GB used. The leftover stack folders above no longer have images.

Known gaps in the script:
- Almost every image follows `latest` (Gitea is pinned), so an update can pull a release with breaking config changes.
- The prune only takes dangling images. Images of stacks that were stopped for good stay until `sudo docker image prune -a`.

### Backups

A systemd timer runs `/usr/local/sbin/restic-docker-backup.sh` as root at about 02:30 (details on the [Restic page](../services/restic.md)). It stops every stack, backs up `~/docker` plus media folders from the 4 TB disk to the restic repo on `/mnt/backup-hdd`, starts the stacks again, and then mirrors the repo to Backblaze B2. **Services, monitoring included, are down for about 3 minutes every night, and for much longer after a lot of new media** (1 h 15 min on 2026-11-01), because the media is read while the stacks are stopped (follow-up 40).

## Gaps

- Docker log rotation has been configured since 2026-10-28: `/etc/docker/daemon.json` sets `json-file` with `max-size 10m` and `max-file 3`. Containers created before that keep uncapped logs until they're next recreated; `docs/runbooks/loki-storage-check.sh` lists them. The trigger was Loki's own debug log reaching 38 GB ([incident](../incidents/2026-10-28-loki-debug-logging-filled-disk.md)).

## Runbooks

- [A service URL returns 502 or closes the connection](../runbooks/service-url-returns-502.md)
- [Names don't resolve: MagicDNS and the host's DNS](../runbooks/names-dont-resolve.md)
- [Media libraries are empty, or nothing runs, after a reboot](../runbooks/media-libraries-empty-after-reboot.md)
- [A compose or `.env` change didn't take effect](../runbooks/compose-change-didnt-take-effect.md)
- [Updating containers](../runbooks/updating-containers.md)
- [The nightly backup failed](../runbooks/backup-failed.md)
- [The nightly backup took long](../runbooks/backup-took-long.md)
- [Restoring from the backup](../runbooks/restoring-from-backup.md)

## Incidents

- [Tailnet-only services are reachable from the home LAN](../incidents/2026-10-28-services-reachable-from-home-lan.md) (open)
- [2026-10-30: everything slow under heavy traffic: the router sent to the server at 7.3 Mbit/s](../incidents/2026-10-30-server-wifi-downlink-stuck-at-mcs0.md) (resolved)
- [Euro-Office broken after switching it to Funnel](../incidents/2026-10-28-euro-office-broken-after-funnel-switch.md) (resolved)
- [2026-09-10: server offline after moving to a new network](../incidents/2026-09-10-server-offline-after-network-move.md) (resolved)
- [2026-07-21: Tailscale and dhcpcd fought over the server's DNS](../incidents/2026-07-21-server-dns-fight-with-dhcpcd.md) (resolved)
- [2026-10-02: media libraries empty after the HDD mounted late](../incidents/2026-10-02-media-libraries-empty-after-late-hdd-mount.md) (resolved)
- [2026-10-04: `stacks.sh` found no compose files](../incidents/2026-10-04-stacks-sh-no-compose-file-found.md) (resolved)
- [2026-10-11: HDD not mounted after the automount test](../incidents/2026-10-11-hdd-not-mounted-after-automount-test.md) (resolved)
