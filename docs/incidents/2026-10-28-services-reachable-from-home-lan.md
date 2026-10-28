# Tailnet-only services are reachable from the home LAN

- **Date:** found 2026-10-28
- **Status:** open
- **Service:** every service whose container publishes on `0.0.0.0` (most of them; Vaultwarden and invidious-companion bind `127.0.0.1` and are not affected)
- **Runbook:** none

## Symptom

With Tailscale turned off, a device on the home Wi-Fi can open services directly at `http://198.51.100.10:<port>`, bypassing Caddy and Tailscale. Their intended Exposure is tailnet-only, which per the glossary excludes the home LAN.

## Cause (probable)

Ports published by Docker get Docker's own iptables rules, which apply before ufw's. So ufw's `deny (incoming)` doesn't cover them. Caddy runs in host network mode, isn't published by Docker, and is filtered correctly (`443/tcp on tailscale0` only).

## Fix (planned, not applied)

Bind each published port to loopback (`"127.0.0.1:<host>:<container>"` in each compose file), so Caddy, which reaches services on `localhost`, is the only way in. Exceptions to check before changing anything:

- **Nextcloud `8080` and Euro-Office `9917`**: they call each other on the LAN IP (`198.51.100.10`). Those internal addresses would have to move to something else first.
- **Jellyfin `7359/udp`** (client discovery on the LAN) and anything else that's meant to be found on the LAN.
