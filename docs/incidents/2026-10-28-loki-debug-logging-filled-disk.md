# Loki logged at debug level into an unrotated Docker log, and kept everything forever

- **Date:** found 2026-10-28; building up since the Loki container was created on 2026-10-04
- **Status:** resolved 2026-10-28 (one check left: the next restic run skips the data directories)
- **Service:** Loki (monitoring stack on homelab), with Alloy and the nightly restic backup affected
- **Runbook:** none (first occurrence). Check script: [`loki-storage-check.sh`](../runbooks/loki-storage-check.sh)

## Symptom

- One container's Docker log, `/var/lib/docker/containers/<CONTAINER_ID>…/…-json.log`, was **38 GB** and growing by about 1.1 MiB/min. The next largest was 26 MB.
- `~/docker/monitoring/loki/data` was **17 GB** (all in `chunks/`) and growing. Its daily index tables went back to 2026-08-22.
- About 19 GB of logs and metrics (Loki 17 GB, Prometheus 2.3 GB) went to the backup HDD and to Backblaze B2 every night.
- Loki's `/ready` never passed ("Pattern Ingester not ready" or "Ingester not ready: waiting for 15s after being ready").
- Alloy logged about 41 `final error sending batch, no retries left, dropping data` a day.

## Cause

Three settings combined, and each one alone would have been mild:

1. **`server.log_level: debug`** in `~/docker/monitoring/loki/loki-config.yml`. More than 95% of the output was `mock.go` "Get" and "Get - deadline exceeded" lines, from the in-memory ring polling itself: about 6,000 lines a minute.
2. **No Docker log rotation.** There was no `/etc/docker/daemon.json`, and the Loki service in compose had no `logging:` block. Its `json-file` log grew from 2026-10-04 to 38 GB.
3. **Alloy ships every container's logs, Loki's included,** and Loki's **effective `limits_config.retention_period` was `0s`** (keep forever). The compactor had `retention_enabled: true` and ran every 15 minutes, but with no period it never marked anything. So Loki stored its own debug output, about 2.3 GB a day of ingest, and never deleted it.

**The dropped Alloy batches** come from the 02:30 restic backup, not from data loss in normal operation:
- The backup stops and starts the monitoring stack (Alloy and Loki were last started at 02:33:56 PDT = 09:33:56 UTC).
- All 41 drops were in the next hour, and every one was an HTTP 400 for old timestamps: "entry too far behind" (hours old), or "timestamp too old" (more than a week; jellyfin, euro-office, kavita). Loki was rejecting old lines that Alloy was re-sending after the restart. Alloy doesn't retry 400s.
- There were no final errors on 429s, which Alloy does retry. So no new logs were lost.
- Why Alloy re-sends old lines after a plain restart isn't known. Its compose `command:` sets no `--storage.path`, so its read positions live inside the container.

The pattern ingester was turned on in `loki-config.yml` (it's off by default in Loki 3.7), along with `limits_config.metric_aggregation_enabled`. It failed `/ready` and logged `ResourceExhausted … received message larger than max`. Nothing used it.

## Fix (run on homelab, 2026-10-28, about 17:00 PDT)

```bash
# 1. Default log rotation for new containers, then restart Docker (every service restarted and came back)
printf '%s\n' '{' '  "log-driver": "json-file",' '  "log-opts": { "max-size": "10m", "max-file": "3" }' '}' > ~/daemon.json.new
sudo dockerd --validate --config-file ~/daemon.json.new
sudo install -m 644 -o root -g root ~/daemon.json.new /etc/docker/daemon.json
sudo systemctl restart docker

# 2. Loki: info logging, 7-day retention, pattern ingester and metric aggregation off
cd ~/docker/monitoring
cp -p loki/loki-config.yml loki/loki-config.yml.bak-20261028
#   server.log_level: debug -> info
#   limits_config: + retention_period: 168h ; metric_aggregation_enabled: true -> false
#   pattern_ingester.enabled: true -> false
sudo docker run --rm -v "$PWD/loki/loki-config.yml:/etc/loki/local-config.yaml:ro" \
  "$(sudo docker inspect --format '{{.Image}}' loki)" -config.file=/etc/loki/local-config.yaml -verify-config
sudo docker compose up -d --force-recreate loki   # removes the old container and its 38 GB log

# 3. Keep logs and metrics out of restic (the script uses --exclude-if-present .nobackup)
sudo touch ~/docker/monitoring/loki/data/.nobackup ~/docker/monitoring/prometheus/data/.nobackup
```

Backup of the Loki config: `~/docker/monitoring/loki/loki-config.yml.bak-20261028`. `daemon.json` didn't exist before.

**Undo:**
- Rotation: `sudo rm /etc/docker/daemon.json && sudo systemctl restart docker`.
- Loki: copy the `.bak` back, then `docker compose up -d --force-recreate loki`.
- Backups: `sudo rm` the two `.nobackup` files.

**Decided against:** an Alloy drop rule for noisy logs. Once the source was fixed, total ingest was about 45 KiB/min (about 65 MB a day), so there's nothing worth filtering.

## Verified (2026-10-28)

- The new Loki container has `{"max-file":"3","max-size":"10m"}`. `/var/lib/docker/containers` went from 38 GB to 97 MB, and `/` from 218 GB used to 181 GB.
- Loki's own log grows 11 KiB/min (was 1,129). Ingest is about 45 KiB/min (was about 2.3 GB a day).
- `/config` shows `log_level: info`, `retention_period: 1w` and `metric_aggregation_enabled: false`. `/ready` returns `ready` every time. The only error after startup was one `empty ring`.
- All containers are running after the Docker restart.

About 2½ h later (about 19:30 PDT), `loki-storage-check.sh` returned `VERDICT=GREEN`:
- **Retention deleted the existing data.** Daily index tables went from 56 to 8, and `loki/data` from 17 GB to 2.6 GB. `/` is now 167 GB used, 51 GB less than before. The Loki 3.7 retention docs say period changes "are not retroactive", but on this setup (tsdb on the filesystem store) they were applied to data already stored. It took one apply run (every 15 min) plus `retention_delete_delay` (2 h).
- Loki's own log grows 6 KiB/min. The largest container log anywhere is 27 MB.

**Still to confirm:** that the 2026-10-29 02:30 restic run skips both data directories.

## Left over

- **Containers created before 2026-10-28 still have no log limit** (`{}`). Each one picks up the default when it's next recreated, for example when `stacks.sh update` pulls a new image. `loki-storage-check.sh` lists the ones still uncapped. invidious (4 × 1 GB) and uptime-kuma (3 × 10 MB) set their own limits in compose.
- **Alloy replays old lines after the nightly restart**, which adds about 40 rejected batches a day. It's harmless. A persistent `--storage.path` volume might stop it, but that isn't tested.

## Lesson

Nothing should run at debug level by default. Every log has to end somewhere: Docker needs a `max-size`, and Loki needs a non-zero `retention_period`. `retention_enabled: true` on its own does nothing. And the monitoring stack ships its own logs too, so a noisy monitoring component fills both the Docker log and Loki.
