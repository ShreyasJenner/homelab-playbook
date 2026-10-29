# Connection reset after choosing or changing a port

## Symptom

- After setting up a service or changing its port, `curl` gets "Connection reset by peer" or "connection refused", even on `localhost`.
- The container is "Up", and its log may look healthy.

## Check

```bash
sudo docker port <container>                                          # host port -> container port
sudo docker logs <container> 2>&1 | grep -i -E 'listen|port|running on' | tail -5   # the port the app actually listens on
sudo docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' <container> | grep -i -E '(^|_)PORT='
```

If the app listens on a different port from the right-hand side of `ports:`, that's the problem.

## The rule

**An app's own port setting (`PORT`, `MEMOS_PORT`, `HTTP_PORT`…) is the port it listens on inside the container.** It must equal the right-hand side of `ports: "<host>:<container>"`. Only the left-hand side is the host port.

Exceptions:
- **Host network** (`network_mode: host`, as for Homepage and Uptime Kuma): there's no mapping, so the app's port setting *is* the host port, and it must not clash with anything else on the host.
- **Container-to-container URLs use the container port** (for example `http://jellyfin:8096`), not the published one.

## Likely causes

1. **The app's port variable was set to the host port**: Memos `MEMOS_PORT`, Gitea `HTTP_PORT`. Or the container side of the mapping was changed away from the image's default (`GRAFANA_DOCKER_PORT`, Prometheus's internal port), while the app still listens on its default.
2. **On host networking, the port was already in use** by another service.
3. **The app wrote the setting into its own config** (Gitea's `app.ini`), so changing the env var back didn't undo it.
4. **A container-to-container URL uses the host port.** A Prometheus scrape target or a Grafana data source pointed at `cadvisor:8186` gets "connection refused": inside the Docker network it's `cadvisor:8080`. Check with `sudo docker exec prometheus wget -qO- http://localhost:9090/api/v1/targets | grep -o '"lastError":"[^"]*"'`.

## Fix

Set the app's port variable back to the container side of the mapping (or, for host networking, pick a free host port), then `sudo docker compose up -d`. For Gitea, edit `[server] HTTP_PORT` in `app.ini` and restart.

## Verify

`curl -sI http://localhost:<host port>` answers, and the Caddy URL loads.

## Related incidents

- [2026-08-22: Grafana and Prometheus reset every connection](../incidents/2026-08-22-grafana-prometheus-connection-reset.md)
- [2026-08-29: cAdvisor dashboards empty](../incidents/2026-08-29-cadvisor-dashboards-empty.md)
- [2026-10-21: Memos connection reset from a port mismatch](../incidents/2026-10-21-memos-connection-reset-port-mismatch.md)
- [2026-10-22: Homepage couldn't bind port 3000](../incidents/2026-10-22-homepage-port-3000-in-use.md)
- [2026-10-24: Gitea down after `app.ini` edits](../incidents/2026-10-24-gitea-down-after-app-ini-edits.md)
