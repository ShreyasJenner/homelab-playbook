# Open follow-ups: drafted commands

Drafted 2026-10-28 and untested; the numbers are those in `.scratch/playbook/plan.md`. The sections are in priority order, and a section is deleted once its follow-up is done. The user decided against clean-up for 27 and 31, so those are optional.

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

**12. `stacks.sh` and disk space.**
```bash
cp -p ~/docker/stacks.sh ~/docker/stacks.sh.bak-20261028
grep -n 'DEFAULT_STACKS' ~/docker/stacks.sh
nano ~/docker/stacks.sh            # add gitea vaultwarden
~/docker/stacks.sh list
sudo docker system df
sudo docker image prune -a         # every image no container uses; asks first
sudo docker builder prune
```
Then update Vaultwarden (`docs/runbooks/updating-containers.md`).

**15. Uncapped container logs:** `loki-storage-check.sh` lists them, and each one is fixed when it's next recreated (item 4's `up -d` covers most). Optional, untested: persistent Alloy storage. Add `--storage.path=/var/lib/alloy/data` to its `command:` and the volume `./alloy/data:/var/lib/alloy/data`, run `mkdir -p ~/docker/monitoring/alloy/data`, then `sudo docker compose up -d alloy`. The next morning, `sudo docker logs alloy --since 6h 2>&1 | grep -c 'no retries left'` should be about 0.

**20/25. Redlib healthcheck.**
```bash
cd ~/docker/redlib && cp -p docker-compose.yml docker-compose.yml.bak-20261028
grep -n -A6 'healthcheck' docker-compose.yml
```
If the compose file has a `healthcheck:` block, delete it. If not (it comes from the image), add `healthcheck: { disable: true }` to both services. Then `sudo docker compose up -d`, and check that `sudo docker ps --filter name=redlib` shows no "(unhealthy)".

**11. More Kuma monitors** (tick "Kuma Alert" on each):
- `https://drive.example.com/status.php`
- `https://gitea.example.com/api/healthz`
- `https://journal.example.com/healthz`
- `https://ntfyhub.example.com/v1/health`
- `https://grafana.example.com/api/health`
- `https://dasha.example.com`, `https://youtube.example.com`, `https://rla.example.com`
- `http://localhost:9917/healthcheck` (Euro-Office)

**26. Invidious:** `grep -n -E 'registration_enabled|popular_enabled' ~/docker/invidious/docker-compose.yml`, set both to `false` once all accounts exist, then `up -d`. Companion: add `reverse_proxy /companion* localhost:8282` above the existing `reverse_proxy` in the Caddyfile's `youtube` block, then validate and reload (`docs/services/caddy.md`). Optional: playback works today.

**1. Reserve the LAN address:** `ip link show wlp130s0 | awk '/ether/{print $2}'`, then reserve `198.51.100.10` for that MAC in the router.

**Low priority or optional:**
- 17: Mindwtr CORS origin → `https://task.example.com`, only if the browser app is used.
- 24: `UDP_HOST_PORT=7359` in `~/docker/jellyfin/.env`, only if LAN discovery is wanted.
- 27: delete the `ND_LISTENBRAINZ_*` lines in Navidrome's compose.
- 31: `rclone config delete onedrive`; `rclone backend lifecycle backblaze:restic-backups`.
- 8: Playbook work, not a host change. Check whether `docs/runbooks/media-libraries-empty-after-reboot.md` already covers it.
