# Monitoring stack (Grafana, Prometheus, Loki, Alloy, node-exporter, cAdvisor)

```
Status:     live (since 2026-08-22; Loki and Alloy since 2026-08-29)
Host:       homelab
Exposure:   tailnet-only through Caddy (Grafana only), but every published port is open on the home LAN
URL:        https://grafana.example.com
Config:     ~/docker/monitoring/ (one Compose project: docker-compose.yml, .env, prometheus/prometheus.yml,
            loki/loki-config.yml, alloy/config.alloy; data in grafana/data, prometheus/data, loki/data)
Secrets:    Grafana admin password in ~/docker/monitoring/.env as GRAFANA_ADMIN_PASSWD (<GRAFANA_ADMIN_PASSWD>)
Depends on: read-only host mounts (docker.sock, /var/lib/docker, /sys, /proc, /var/log/journal); Caddy; Tailscale
Per-User:   no
Verified:   2026-10-28
```

One page for six containers: they're one Compose project, they start, stop, update and back up together, and only Grafana has a URL. **Alerts don't come from here.** [Uptime Kuma](uptime-kuma.md) and [ntfy](ntfy.md) do that; this stack is for looking things up after the fact, and it's rarely used.

## What it's for

- **Metrics:** host and per-container CPU, memory, disk and network, kept 30 days.
- **Logs:** every container's log plus the systemd journal, searchable in one place, kept 7 days.

## Which container is using the most memory

The one question this stack is used for.

**Quick answer, no Grafana** (on homelab):

```bash
sudo docker stats --no-stream --format '{{.MemPerc}}\t{{.MemUsage}}\t{{.Name}}' | sort -rn | head
```

**Over time, in Grafana:** open `https://grafana.example.com` → **Explore** → data source **Prometheus** → switch the query editor to **Code**, and run:

```
topk(5, container_memory_working_set_bytes{name!=""})
```

- Checked 2026-10-28: it returns the same top containers as `docker stats` (Euro-Office 1.4 GiB, cAdvisor, Jellyfin, Prometheus).
- Set the unit to bytes (Options → Unit → Data → bytes(IEC)) and widen the time range to see when it grew.
- `name` is the container name. `name!=""` drops cAdvisor's per-cgroup series that aren't containers.
- Use **working set**, not `container_memory_usage_bytes`. Usage includes page cache the kernel can drop, which makes anything that reads lots of files (Jellyfin, Navidrome, restic) look far bigger than it is. Working set is roughly what `docker stats` shows.
- For the whole host, the **Node Exporter Full** dashboard has the RAM and swap panels. The two cAdvisor dashboards ("cAdvisor dashboard", "cAdvisor exporter v2") show the same per-container data as panels.

CPU tip: in `docker stats`, 100% means one full core, and the host has 10 cores, so a container can show up to 1000%.

## Why this one

- Prometheus with node-exporter (host) and cAdvisor (containers), drawn by Grafana, is the standard pairing. Nothing else (Netdata, InfluxDB) was compared.
- **Alloy rather than Promtail** was the user's own call: Promtail is feature-complete and being replaced by Alloy.
- It was built in August 2026 as a learning project. Kuma turned out to be the part that's actually needed.

## How it's set up

All six are on the Docker network `monitoring_default` and reach each other by container name. Every image follows `latest`. The uids in the Data column are what each container runs as (verified 2026-10-28; Prometheus runs as `nobody` = 65534), so a fresh data folder needs `chown` to it.

| Container | Image | Host port → container | Role | Data |
|---|---|---|---|---|
| `grafana` | `grafana/grafana` | `4710 → 3000` | dashboards; data sources `http://prometheus:9090` and `http://loki:3100` | `grafana/data` (uid 472) |
| `prometheus` | `prom/prometheus` | `9090 → 9090` | scrapes every 15 s; retention 30 days, no size cap (2.3 GB) | `prometheus/data` (uid 65534), `.nobackup` |
| `node-exporter` | `prom/node-exporter` | not published | host metrics, `node-exporter:9100` | none |
| `cadvisor` | `gcr.io/cadvisor/cadvisor` | `8186 → 8080` | per-container metrics, `cadvisor:8080`; `privileged` | none |
| `loki` | `grafana/loki` (3.7.7) | `3517 → 3100` | log store, `auth_enabled: false` | `loki/data` (uid 10001), `.nobackup` |
| `alloy` | `grafana/alloy` | `12761 → 12345` | ships logs to Loki | none (see below) |

**Prometheus:** `prometheus.yml` is plain (no templating). Jobs `prometheus`, `node-exporter` and `cadvisor`, all up. The targets use container ports (`cadvisor:8080`), not host ports ([2026-08-29 incident](../incidents/2026-08-29-cadvisor-dashboards-empty.md)). `/targets` in a browser is a JavaScript page; from a shell use `sudo docker exec prometheus wget -qO- http://localhost:9090/api/v1/targets`.

**Loki** (since the [2026-10-28 fix](../incidents/2026-10-28-loki-debug-logging-filled-disk.md)): `log_level: info`, `limits_config.retention_period: 168h`, compactor with `retention_enabled: true` and `delete_request_store: filesystem`, all paths under `/loki`, pattern ingester and metric aggregation off. `/ready` answers `ready`. The image has no shell, so `docker exec loki sh` fails. Check its storage with [`loki-storage-check.sh`](../runbooks/loki-storage-check.sh) (read-only; prints `VERDICT=GREEN` or `RED`).

**Alloy** sends two sources to `http://loki:3100/loki/api/v1/push`:
- every container's log (`discovery.docker` → `loki.source.docker`, label `container`)
- the systemd journal (`max_age 12h`, label `unit`). The config sets `job=systemd-journal`, but that isn't applied: the only `job` value in Loki is `loki.source.journal.journal` (2026-10-28)

It mounts `docker.sock` (ro), `/var/lib/docker/containers`, `/var/log/journal` and `/etc/machine-id`. It has no `--storage.path`, so its read positions live inside the container. After every restart (including the nightly backup's) it re-sends old lines, and Loki rejects about 40 batches as too old. That's harmless: no new logs are lost.

**Finding logs in Grafana:** Explore → Loki → `{container="nextcloud_app"}` or `{unit="tailscaled.service"}`. Anything older than 7 days is gone.

**Grafana:** `GRAFANA_DOCKER_PORT=3000`, the image default ([2026-08-22 incident](../incidents/2026-08-22-grafana-prometheus-connection-reset.md)). The admin password in `.env` only applies when Grafana first creates its database; to change it later, run `sudo docker exec -it grafana grafana cli admin reset-admin-password <NEW_PASSWORD>`. No alert rules are used.

### Backups and the nightly gap

- `grafana/data` is backed up by restic. `loki/data` and `prometheus/data` have `.nobackup` files (since 2026-10-28), so about 19 GB of logs and metrics are no longer copied every night. Old snapshots keep them until retention prunes them.
- The backup stops the stack from 02:30 to about 02:34, so expect a short hole in every graph at that time.

## Known gaps

- **Prometheus `9090`, Loki `3517`, cAdvisor `8186` and the Alloy UI `12761` have no authentication and are open on the home LAN.** Nothing outside the Docker network needs them, so drop those `ports:` entries (follow-up 10, part of the [LAN-exposure incident](../incidents/2026-10-28-services-reachable-from-home-lan.md)). Grafana `4710` is LAN-reachable too, behind its login.
- **Alloy (`docker.sock`) and cAdvisor (`privileged`) are effectively root on the host.** Read-only on the socket doesn't change that.
- **Everything follows `latest`**, so `stacks.sh update` can pull a Loki or Alloy release with breaking config changes. A Loki 3.x config change has already broken it once ([2026-08-29](../incidents/2026-08-29-loki-crash-loop-compactor-config.md)).
- Containers created before 2026-10-28 have uncapped Docker logs until they're recreated (`loki-storage-check.sh` lists them).

## Runbooks

- [A Grafana panel or Explore query shows no data](../runbooks/grafana-panel-shows-no-data.md)
- [A new container won't start or crash-loops](../runbooks/new-container-crash-loops.md)
- [Connection reset after choosing or changing a port](../runbooks/connection-reset-after-port-change.md)
- [Loki storage check](../runbooks/loki-storage-check.sh) (script)
- [Updating containers](../runbooks/updating-containers.md)

## Incidents

- [2026-08-22: Grafana's port already in use, then a crash loop](../incidents/2026-08-22-grafana-port-in-use-then-crash-loop.md)
- [2026-08-22: Grafana and Prometheus reset every connection](../incidents/2026-08-22-grafana-prometheus-connection-reset.md)
- [2026-08-29: cAdvisor dashboards empty](../incidents/2026-08-29-cadvisor-dashboards-empty.md)
- [2026-08-29: Loki's config file mounted as a directory](../incidents/2026-08-29-loki-config-mounted-as-directory.md)
- [2026-08-29: Loki crash-looped on its compactor config](../incidents/2026-08-29-loki-crash-loop-compactor-config.md)
- [2026-10-28: Loki's debug logging filled the disk](../incidents/2026-10-28-loki-debug-logging-filled-disk.md)
