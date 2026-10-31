# Open follow-ups: drafted commands

Drafted 2026-10-28 and untested; the numbers are those in [`FOLLOWUPS.md`](FOLLOWUPS.md). The sections are in priority order, and a section is deleted once its follow-up is done. The user decided against clean-up for 27 and 31, so those are optional.

## 1. Security

**10. Monitoring ports to loopback** (first: Prometheus, Loki, cAdvisor and the Alloy UI have no authentication). Binding to `127.0.0.1` rather than removing the ports keeps Caddy and `loki-storage-check.sh` (`localhost:3517`) working.
```bash
cd ~/docker/monitoring
cp -p docker-compose.yml docker-compose.yml.bak-20261028
grep -n -A2 'ports:' docker-compose.yml
nano docker-compose.yml     # each  - "${X_HOST_PORT}:..."  ->  - "127.0.0.1:${X_HOST_PORT}:..."
diff docker-compose.yml.bak-20261028 docker-compose.yml
sudo docker compose config --quiet && sudo docker compose up -d
sudo ss -tlnp | grep -E ':(4710|9090|3517|8186|12761)\b'    # every line 127.0.0.1
```
Check: `grafana.example.com` loads; from the phone with Tailscale off, `http://198.51.100.10:9090` fails. Undo: restore the `.bak`, then `up -d`. Side effect: the recreated containers get capped logs.

**4. The same for the other stacks, one at a time.** Leave Nextcloud `8080` and Euro-Office `9917` (they call each other on the LAN IP). Ports: ntfy 10230, Gitea 8310/8312, Memos 9418, Mindwtr 6301/6302, Actual Budget 5006, Invidious 3000, Navidrome 4533, Kavita 5000, Jellyfin 8167 (TCP only), Redlib 8943/8941. Before starting, find callers that use the LAN IP (`-o` prints only the match, so no secrets):
```bash
sudo grep -rno '198\.51\.100\.10:[0-9]*' ~/docker --include='*.yml' --include='*.yaml' --include='.env' --include='*.ini' --include='*.json' --include='*.xml' 2>/dev/null | sort -u
```
Check each stack: its Caddy URL loads and its Kuma monitor stays green. When everything is done, the LAN-exposure incident can be resolved.

**16 then 22. Vaultwarden DOMAIN, then 2FA.**
```bash
cd ~/docker/vaultwarden
grep -n 'DOMAIN' docker-compose.yml .env        # DOMAIN lines only
nano <that file>                                # DOMAIN=https://vault.example.com
sudo docker compose up -d
sudo docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' vaultwarden | grep '^DOMAIN='
```
2FA: web vault → Settings → Security → Two-step login → Authenticator app. Keep the recovery code outside Vaultwarden.

**2. Nextcloud 2FA.** Each account turns it on under Personal settings → Security → TOTP. Check with `sudo docker exec -u www-data nextcloud_app php occ twofactorauth:state <USER>`. DAV clients then need app passwords. Run `occ twofactorauth:enforce --on` only after everyone is set up.

**18. Gitea URLs and 2FA.** `SSH_DOMAIN` defaults to `DOMAIN`, so pin it to `gitea` to keep the `git@gitea:` alias URLs working.
```bash
F=~/docker/gitea/gitea/gitea/conf/app.ini
sudo cp -p $F $F.bak-20261028
sudo nano $F     # [server]: ROOT_URL = https://gitea.example.com/ , DOMAIN = gitea.example.com , SSH_DOMAIN = gitea
sudo grep -n -E '^(ROOT_URL|DOMAIN|SSH_DOMAIN|SSH_PORT) ' $F    # app.ini holds secrets: grep only these
cd ~/docker/gitea && sudo docker compose restart gitea
```
Check: a push from the laptop works. Then 2FA under Settings → Security (HTTPS git would then need a token; SSH isn't affected).

## 2. Backups

**28. Alert on a failed backup, through healthchecks.io** (it already emails, and needs no Tailscale). Create a check "restic nightly" (period 1 day, grace 2 h) and copy its ping URL.
```bash
systemctl show -p Type restic-docker-backup.service          # needs Type=oneshot
sudo grep -n 'exit' /usr/local/sbin/restic-docker-backup.sh   # does a failed B2 sync exit non-zero?
sudo systemctl edit restic-docker-backup.service
#   [Service]
#   ExecStartPost=/usr/bin/curl -fsS -m 10 --retry 5 -o /dev/null <BACKUP_PING_URL>
```
`ExecStartPost` runs only if the script succeeds, so a failure means no ping, and healthchecks.io emails. If the Type isn't oneshot, put the curl at the end of the script instead. The ping URL then lives in `/etc/systemd/system/restic-docker-backup.service.d/override.conf` (a credential; host config isn't backed up).

**14. After 02:40 on 2026-10-29: did restic skip the Loki and Prometheus data?**
```bash
journalctl -u restic-docker-backup.service --since today --no-pager | grep -E 'Added to the repository|Backup finished'
R="sudo restic -r /mnt/backup-hdd/restic-repo --password-file /root/.config/restic/password"
$R ls latest /home/alice/docker/monitoring/loki/data | head -3    # expect nothing
```

**5. The restic password.** Airplane-mode test: open Bitwarden offline and unlock with PIN or biometrics. Make a copy that doesn't depend on the server (for example on paper); `sudo cat /root/.config/restic/password` only while writing it down, and never paste it.

**30. Restore tests.**
```bash
sudo -i
R="restic -r /mnt/backup-hdd/restic-repo --password-file /root/.config/restic/password"
$R restore latest --target /root/restore-test --include /home/alice/docker/vaultwarden
sqlite3 /root/restore-test/home/alice/docker/vaultwarden/data/db.sqlite3 'pragma integrity_check; select count(*) from ciphers;'
RCLONE_CONFIG=/home/alice/.config/rclone/rclone.conf \
  restic -r rclone:backblaze:restic-backups --password-file /root/.config/restic/password dump latest /home/alice/docker/vaultwarden/docker-compose.yml | head
rm -r /root/restore-test; exit
```
Expect `ok`, and a count close to the number of vault items. For Nextcloud, follow `docs/runbooks/restoring-from-backup.md`.

**29. Disk health.**
```bash
sudo apt install smartmontools
lsblk -o NAME,SIZE,MODEL,MOUNTPOINT
sudo smartctl -H -d sat /dev/sda; sudo smartctl -H -d sat /dev/sdb; sudo smartctl -H /dev/nvme0n1
sudo smartctl -A -d sat /dev/sdb | grep -E 'Reallocated|Pending|Uncorrectable|Power_On_Hours'
```

**23. Invidious Postgres into `~/docker`** (or accept the risk: Invidious is used seldom).
```bash
cd ~/docker/invidious
cp -p docker-compose.yml docker-compose.yml.bak-20261028
grep -n 'postgresdata' docker-compose.yml
sudo docker compose stop
sudo mkdir postgresdata && sudo cp -a /var/lib/docker/volumes/invidious_postgresdata/_data/. postgresdata/
nano docker-compose.yml   # invidious-db: - ./postgresdata:/var/lib/postgresql/data ; drop postgresdata: under top-level volumes:
sudo docker compose up -d && sudo docker compose logs --tail 20 invidious-db
```
Check: log in, and the subscriptions are there. Once a backup has run, `sudo docker volume rm invidious_postgresdata`.

**6. `backup/vns` and `media/games`:** a decision, not a fix. Size them with `du -sh` on the 4 TB disk (the backup disk is 24% used). To include them, add the paths to the script's `restic backup` line.

## 3. Maintenance

**15. Uncapped container logs:** `loki-storage-check.sh` lists them, and each one is fixed when it's next recreated (item 4's `up -d` covers most). Optional, untested: persistent Alloy storage. Add `--storage.path=/var/lib/alloy/data` to its `command:` and the volume `./alloy/data:/var/lib/alloy/data`, run `mkdir -p ~/docker/monitoring/alloy/data`, then `sudo docker compose up -d alloy`. The next morning, `sudo docker logs alloy --since 6h 2>&1 | grep -c 'no retries left'` should be about 0.

**20/25. Redlib healthcheck.**
```bash
cd ~/docker/redlib && cp -p docker-compose.yml docker-compose.yml.bak-20261028
grep -n -A6 'healthcheck' docker-compose.yml
```
If the compose file has a `healthcheck:` block, delete it. If not (it comes from the image), add `healthcheck: { disable: true }` to both services. Then `sudo docker compose up -d`, and check that `sudo docker ps --filter name=redlib` shows no "(unhealthy)".

**33. Redlib on the published image** (after the home-IP block lifts; pairs well with 20/25, same file). Back up the compose file, set the anchor's `image:` to `quay.io/redlib/redlib:latest`, delete the `build:` block and both `pull_policy:` lines, then `sudo docker compose pull && sudo docker compose up -d`. Check: `sudo docker exec redlib-shreyas redlib --version` is 0.40.0 or later, and `curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8943/r/selfhosted` is `200`. Then `sudo docker image rm redlib-local:latest`, and update the service page's Updating section and the runbook (no more "never pull"). Undo: restore the `.bak`, then `build --no-cache` and `up -d`.

**34. CGNAT check** (no change, a fact to record). On the server, `curl -s https://ifconfig.me; echo`; in the ISP's app, the WAN/Internet IP. Compare them by eye and don't paste either one. The same means a public IPv4 (no CGNAT); a `100.64.x.x`–`100.127.x.x` WAN address means CGNAT.

**11. More Kuma monitors** (tick "Kuma Alert" on each):
- `https://drive.example.com/status.php`
- `https://gitea.example.com/api/healthz`
- `https://journal.example.com/healthz`
- `https://ntfyhub.example.com/v1/health`
- `https://grafana.example.com/api/health`
- `https://dasha.example.com`, `https://youtube.example.com`, `https://rla.example.com`
- `http://localhost:9917/healthcheck` (Euro-Office)

**26. Invidious:** `grep -n -E 'registration_enabled|popular_enabled' ~/docker/invidious/docker-compose.yml`, set both to `false` once all accounts exist, then `up -d`. Companion: add `reverse_proxy /companion* localhost:8282` above the existing `reverse_proxy` in the Caddyfile's `youtube` block, then validate and reload (`docs/services/caddy.md`). Optional: playback works today.

**32. Slim Nextcloud's server side.** Read-only pre-check first; it decides the rest:
```bash
cd ~/docker/nextcloud
grep -n -E 'image:|REDIS' docker-compose.yml
O="sudo docker exec -u www-data nextcloud_app php occ"
$O status | grep -E 'versionstring|maintenance'
$O config:system:get memcache.locking; $O config:system:get memcache.local; $O config:system:get redis
$O config:app:get core backgroundjobs_mode
$O app:list --enabled | grep -E 'richdocuments|onlyoffice|eurooffice'
sudo docker exec nextcloud_db mariadb --version
```
Then one change per block, in this order:
- **Pin the image** to the running major (`nextcloud:<major>`; pinning to the running version doesn't change it), and pin MariaDB to its running tag.
- **Redis:** add a `redis` service (`redis:7-alpine`, pinned) to the stack. Point Nextcloud at it with `$O config:system:set redis host --value=redis`, `... redis port --value=6379 --type=integer` and `$O config:system:set memcache.locking --value='\OC\Memcache\Redis'`. Check: `$O config:system:get memcache.locking`, then a `files:scan` of one user. Undo: `$O config:system:delete memcache.locking`, then remove the service.
- **Connectors:** `$O app:disable richdocumentscode` (and `richdocuments`, `onlyoffice`), only if the user agrees; the page says they're "kept on purpose". Undo: `app:enable`.
- **MariaDB 10.6 → 10.11** (only if the pre-check shows 10.6): do it after a fresh backup and a `mariadb-dump`. Add `MARIADB_AUTO_UPGRADE=1` to `nextcloud_db`, or run `mariadb-upgrade` after the tag change. Riskiest step: last, on its own day.

Check: Uptime Kuma green, a document opens in Euro-Office from the web and the iOS app, `occ status` clean. Background jobs should be `cron`; if not, decide separately.

**1. Reserve the LAN address:** blocked, no admin access to the router (2026-10-30). Do 37 instead.

**37. Nextcloud ↔ Euro-Office off the LAN address.** Read-only first (`-o` prints only the match):
```bash
sudo grep -rno '198\.51\.100\.10[:0-9]*' ~/docker/nextcloud ~/docker/euro-office --include='*.yml' --include='.env' --include='*.json' 2>/dev/null | sort -u
O="sudo docker exec -u www-data nextcloud_app php occ"
$O config:system:get trusted_domains
$O config:app:get eurooffice DocumentServerInternalUrl; $O config:app:get eurooffice StorageUrl
sudo docker exec nextcloud_app curl -s -o /dev/null -w '%{http_code}\n' http://192.0.2.10:9917/healthcheck
sudo docker exec euro-office curl -s -o /dev/null -w '%{http_code}\n' http://192.0.2.10:8080/status.php
```
If both calls return `200`, the tailnet IP works from inside the containers: add `192.0.2.10` to `trusted_domains` (it's there with `:8080` already; check whether the port matters), then set both internal URLs to `http://192.0.2.10:<port>/` in Nextcloud's Euro-Office settings. The app id may not be `eurooffice`; read it from `app:list` first. Check: a document opens from the web and the iOS app. Undo: set the URLs back to `http://198.51.100.10:<port>/`. Follow `docs/runbooks/document-editing-broke-after-lan-ip-change.md` if it breaks.

**35. Detect a stuck Wi-Fi downlink.** Simplest first: an Uptime Kuma **Ping** monitor on `198.51.100.1`, retries 3, with "Kuma Alert" ticked. Kuma doesn't alert on latency alone, so also add a timer script, for example `/usr/local/sbin/wifi-rate-check.sh` every 5 minutes:
```bash
#!/bin/sh
# Alert when the router -> server Wi-Fi rate is stuck low (2026-10-30 incident)
r=$(iw dev wlp130s0 link | awk '/rx bitrate/{print int($3)}')
[ -n "$r" ] && [ "$r" -lt 50 ] && curl -s -d "homelab Wi-Fi rx bitrate ${r} Mbit/s; reconnect Wi-Fi" https://ntfyhub.example.com/<TOPIC>
```
`rx bitrate` is the rate of the last received frame, so it can dip briefly; alert only after two low readings in a row, or reconnect automatically (`nmcli connection down HomeWiFi; sleep 3; nmcli connection up HomeWiFi`) once the alert has proved reliable. The ntfy topic and token are in ntfy's config; don't print them. Check: the script stays quiet while `rx bitrate` is in the hundreds.

**36. MagicDNS SERVFAIL on the server.** Read-only:
```bash
for n in manga.example.com example.com homelab.tail0000.ts.net; do echo "$n: $(dig @100.100.100.100 $n +tries=1 +time=3 | grep -o 'status: [A-Z]*')"; done
tailscale dns status 2>/dev/null | head -30
```
If every public name fails, the tailnet has no global nameserver or MagicDNS forwarding is broken: check DNS in the Tailscale admin console. If only `example.com` fails, look for a split-DNS entry for that domain.

**Low priority or optional:**
- 17: Mindwtr CORS origin → `https://task.example.com`, only if the browser app is used.
- 24: `UDP_HOST_PORT=7359` in `~/docker/jellyfin/.env`, only if LAN discovery is wanted.
- 27: delete the `ND_LISTENBRAINZ_*` lines in Navidrome's compose.
- 31: `rclone config delete onedrive`; `rclone backend lifecycle backblaze:restic-backups`.
- 8: Playbook work, not a host change. Check whether `docs/runbooks/media-libraries-empty-after-reboot.md` already covers it.
