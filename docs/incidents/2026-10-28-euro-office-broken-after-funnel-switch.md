# Euro-Office broken after switching it to Funnel

- **Date:** recorded and fixed 2026-10-28; the break happened before that (exact day unknown: shell history has no timestamps)
- **Status:** resolved
- **Service:** [Euro-Office](../services/euro-office.md) (and [Nextcloud](../services/nextcloud.md) document editing, which depends on it)
- **Runbook:** [A service URL returns 502 or closes the connection](../runbooks/service-url-returns-502.md). Rerunnable check: `docs/runbooks/euro-office-check.sh`

## Symptom

Opening a document in Nextcloud showed "Nextcloud Office cannot be reached. Please contact admin." `docker logs` for Euro-Office printed nothing during the attempt. Off the tailnet, the Euro-Office URL (`:8443`) could not be reached at all. Its intended Exposure is public (ADR 0004), but it was tailnet-only.

## What changed

Euro-Office was tailnet-only and working. It broke after an attempt to move it to Funnel so that outsiders could edit shared documents. Shell history on homelab shows the sequence:

```
sudo tailscale funnel --bg --https=8443 http://locahost:9917
sudo tailscale funnel --bg --https=8443 http://locahost:9917 off
sudo tailscale serve  --bg --https=8443 http://locahost:9917
```

## Leads checked on the host (2026-10-28)

- Port: the container listens on `9917` (`0.0.0.0:9917->80/tcp`), not `9918`.
- Internal addresses: the browser address is `https://homelab.<tailnet>.ts.net:8443/`. Nextcloud reaches Euro-Office at `http://198.51.100.10:9917/` and Euro-Office reaches Nextcloud at `http://198.51.100.10:8080/`. The LAN IP is current, and both directions work.
- `trusted_domains`: fine for the Euro-Office → Nextcloud path.
- JWT: the secrets match (compared on the host, never printed), with no stray whitespace.
- `ALLOW_PRIVATE_IP_ADDRESS`: not involved. The internal requests succeed.
- The Euro-Office logs are empty on a document open even when everything works, so an empty log is not evidence either way.

## Cause

The Tailscale handler for `:8443` proxied to `http://locahost:9917`. `locahost` is a typo and does not resolve, so every request to the browser-facing Euro-Office address got a 502 before it reached the container. Without `api.js`, the editor page could not load, and the connector showed "cannot be reached". The typo came from the Funnel attempt and was copied into the rollback to Serve. As a result, `:8443` was also left tailnet-only, so browsers off the tailnet could not connect at all.

The hypotheses were tested one at a time. Fixing only the target fixed the tailnet case, and the public case stayed red until Funnel was turned on.

## Fix

```bash
sudo tailscale serve --https=8443 off
sudo tailscale funnel --bg --https=8443 http://localhost:9917
```

Verified with `docs/runbooks/euro-office-check.sh`, which returned `VERDICT=GREEN`: documents open on the tailnet and off it (mobile data), and `:8443` shows `(Funnel on)`.

## Follow-ups

- `richdocumentscode` (the built-in Collabora server) is still enabled, although Collabora is retired. It was not involved in this incident. Consider disabling it.
