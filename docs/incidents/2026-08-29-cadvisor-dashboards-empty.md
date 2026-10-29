# cAdvisor dashboards empty

- **Date:** 2026-08-29
- **Status:** resolved
- **Service:** cAdvisor → Prometheus → Grafana (monitoring stack)
- **Runbook:** [A Grafana panel or Explore query shows no data](../runbooks/grafana-panel-shows-no-data.md); also [Connection reset after choosing or changing a port](../runbooks/connection-reset-after-port-change.md)
- **Source:** chat "Understanding Grafana's purpose and use cases" (2026-08-24; messages from 2026-08-29). Unverified; the end state was verified on 2026-10-28.

## Symptom

Both cAdvisor dashboards in Grafana showed no data, while the node-exporter one worked. `curl` to cAdvisor's host port got "connection reset". Once that was fixed, the Prometheus target `cadvisor:8186` was "connection refused".

## Cause

Two port mistakes in a row:
1. The container side of cAdvisor's mapping wasn't 8080, where cAdvisor listens.
2. The scrape target then used the **host** port (8186). Inside the Docker network, Prometheus has to use the container port.

## Fix

Mapping `8186 → 8080`, and the target `cadvisor:8080` in `prometheus.yml`. `privileged: true`, a `/sys/fs/cgroup` mount and a `v0.49.1` image pin were added along the way, but weren't the fix. The pin isn't live (2026-10-28: the image is `latest`). Verified 2026-10-28: the `cadvisor` target is `up`.
