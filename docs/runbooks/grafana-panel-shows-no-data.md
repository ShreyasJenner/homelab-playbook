# A Grafana panel or Explore query shows no data

For the [monitoring stack](../services/monitoring.md). Work down the chain: the source is scraped or shipped → the store is up → the data source connects → the query is right.

## Symptom

A dashboard panel says "No data", Explore returns nothing, or Grafana says "Unable to connect with Loki" or Prometheus.

## Check

```bash
cd ~/docker/monitoring
sudo docker compose ps                                   # all six Up? Loki or Prometheus restarting?

# Metrics: every target "up", and the last error if not
sudo docker exec prometheus wget -qO- http://localhost:9090/api/v1/targets \
  | grep -o -E '"(job|scrapeUrl|health|lastError)":"[^"]*"'

# Logs: Loki ready, and Alloy delivering
curl -s http://localhost:3517/ready; echo
sudo docker logs alloy --since 1h 2>&1 | grep -i -E 'error|dropping' | tail -5
sudo docker logs loki --since 1h 2>&1 | grep -i -E 'level=(error|warn)' | tail -5
```

Then in Grafana: Connections → Data sources → Prometheus or Loki → **Save & test**.

## Likely causes

1. **A scrape target is down or uses the wrong port.** Targets must use the container port (`cadvisor:8080`), not the host port (`8186`).
2. **Loki is crash-looping**, usually after a config change or an image update (see [A new container won't start or crash-loops](new-container-crash-loops.md)).
3. **The query filters on a label that doesn't exist.** A dashboard imported from grafana.com may filter on a `job` name that differs from the `job_name` in `prometheus.yml`: edit the panel and compare. For logs, query by `{container="…"}` or `{unit="…"}`, not `job`: the config's `job=systemd-journal` isn't applied, and the only `job` value in Loki is `loki.source.journal.journal` (2026-10-28).
4. **The time range is outside retention**: 7 days for Loki, 30 days for Prometheus. Data from 02:30 to 02:34 is always missing (the nightly backup stops the stack).
5. **The thing never logged there.** Alloy ships container stdout and the journal. An app that logs only to its own file needs a file source in `config.alloy`.

## Fix

Fix the target in `prometheus.yml` (then `sudo docker compose restart prometheus`), fix Loki's config (then `sudo docker compose up -d --force-recreate loki`), or edit the panel's query.

## Verify

Every target shows `"health":"up"`, both data sources pass Save & test, and the panel draws.

## Related incidents

- [2026-08-29: cAdvisor dashboards empty](../incidents/2026-08-29-cadvisor-dashboards-empty.md)
- [2026-08-29: Loki crash-looped on its compactor config](../incidents/2026-08-29-loki-crash-loop-compactor-config.md)
