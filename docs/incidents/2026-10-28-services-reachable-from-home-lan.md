# Tailnet-only services are reachable from the home LAN

- **Date:** found 2026-10-28
- **Status:** open
- **Service:** every service whose container publishes on `0.0.0.0` (most of them; Vaultwarden and invidious-companion bind `127.0.0.1` and are not affected)
- **Runbook:** none

## Symptom

With Tailscale turned off, a device on the home Wi-Fi can open services directly at `http://198.51.100.10:<port>`, bypassing Caddy and Tailscale. Their intended Exposure is tailnet-only, which per the glossary excludes the home LAN.

Ports recorded so far (2026-10-28; all published on `0.0.0.0` and `[::]`):

| Port | Service | Tested from the LAN | Authentication |
|---|---|---|---|
| `4710` | Grafana | loads | Grafana login |
| `10230` | ntfy | loads | `deny-all` for anonymous |
| `9090` | Prometheus | not tested | **none** |
| `3517` | Loki | not tested | **none** |
| `8186` | cAdvisor | not tested | **none** |
| `12761` | Alloy UI | not tested | **none** |
| `8310`, `8312` | Gitea web and **SSH** | not tested | Gitea login, SSH keys |
| `9418` | Memos | not tested | Memos login |
| `6301`, `6302` | Mindwtr app and cloud | not tested | |
| `5006` | Actual Budget | not tested | Actual login |
| `3000` | Invidious | not tested | |

Not affected: host-network services behind ufw (Caddy, Uptime Kuma `3001` (tested: times out), Homepage `9640`/`9641` (tested)), and services bound to `127.0.0.1` (Vaultwarden, invidious-companion). The four monitoring ports with no authentication are needed by nothing outside their Docker network, so they can simply be unpublished ([monitoring stack](../services/monitoring.md), follow-up 10).

## Cause (probable)

Ports published by Docker get Docker's own iptables rules, which apply before ufw's. So ufw's `deny (incoming)` doesn't cover them. Caddy runs in host network mode, isn't published by Docker, and is filtered correctly (`443/tcp on tailscale0` only).

## Fix (planned, not applied)

Bind each published port to loopback (`"127.0.0.1:<host>:<container>"` in each compose file), so Caddy, which reaches services on `localhost`, is the only way in. Exceptions to check before changing anything:

- **Nextcloud `8080` and Euro-Office `9917`**: they call each other on the LAN IP (`198.51.100.10`). Those internal addresses would have to move to something else first.
- **Jellyfin `7359/udp`** (client discovery on the LAN) and anything else that's meant to be found on the LAN.
