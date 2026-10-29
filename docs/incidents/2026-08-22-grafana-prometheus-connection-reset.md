# Grafana and Prometheus reset every connection

- **Date:** 2026-08-22
- **Status:** resolved
- **Service:** Grafana and Prometheus (monitoring stack)
- **Runbook:** [Connection reset after choosing or changing a port](../runbooks/connection-reset-after-port-change.md)
- **Source:** chat "Resume improvement phase 2 next steps" (2026-08-09; messages from 2026-08-22). Unverified; the end state was verified on 2026-10-28.

## Symptom

`curl` to Grafana's host port gave `(56) Recv failure: Connection reset by peer`. The container was up, and its logs looked healthy. Prometheus did the same.

## Cause

`.env` had changed the container side of each mapping (`GRAFANA_DOCKER_PORT`, and Prometheus's equivalent) to a non-default port. The apps still listened on their defaults, 3000 and 9090, so Docker forwarded to a port where nothing listened.

## Fix

Set the container side back to the image defaults, and change only the host side. `curl` then got Grafana's 302 to `/login`. Verified 2026-10-28: `GRAFANA_DOCKER_PORT=3000`, Grafana `4710 → 3000`, Prometheus `9090 → 9090`.
