# A service URL returns 502 or closes the connection

Covers both ways into a service:
- **Caddy routes** (`https://<name>.example.com`)
- **Tailscale Serve/Funnel entries** (Nextcloud `:10000`, Euro-Office `:8443`, Gitea SSH `:8313`)

Wrong Serve/Funnel targets are the most common cause of outages in this homelab so far: at least four times.

## Symptom

- The browser shows 502 Bad Gateway, or a blank page.
- Nextcloud document editing says "cannot be reached".
- `git clone`/`ssh` says "Connection closed by … port …".
- Off the tailnet, a public service doesn't load at all.
- The service's own `docker logs` show nothing, because the request never reached it.

## Check

**1. Is the backend itself up?** This is the fastest split.

```bash
sudo docker ps --format '{{.Names}}\t{{.Status}}' | grep -i <service>    # Up? restarting? unhealthy?
curl -sI http://localhost:<port> | head -1                                # answers locally?
sudo docker logs <container> --tail 30
```

If the backend doesn't answer on localhost, it's the service, not the proxy. Fix the service.

**2. Caddy route** (for `*.example.com`):

```bash
grep -n -A2 '<name>' ~/docker/caddy/Caddyfile        # right host matcher, right port?
sudo docker logs caddy --since 15m 2>&1 | tail -20   # "dial tcp … connection refused" = wrong port or backend down
```

The port table is on the [Caddy page](../services/caddy.md#routes).

**3. Tailscale Serve/Funnel entry** (for `homelab.tail0000.ts.net:<port>`):

```bash
sudo tailscale serve status                                         # expect exactly the three entries below
sudo tailscale serve status --json | grep -E '"Proxy"|"TCPForward"'  # the exact targets: look for typos
sudo tailscale funnel status                                        # "(Funnel on)" for :10000 and :8443
```

Expected:

| Entry | Target | Mode |
|---|---|---|
| `:10000` | `http://localhost:8080` | Funnel |
| `:8443` | `http://localhost:9917` | Funnel |
| `:8313` | `tcp://localhost:8312` | Serve TCP |

## Likely causes

1. **A typo in the Serve/Funnel target.** For example, `locahost` doesn't resolve, so every request gets a 502 before it reaches the container.
2. **A bare-number `funnel` command overwrote another handler.** `tailscale funnel --bg 10000` means "funnel public 443 to `localhost:10000`", not "turn on Funnel for port 10000". Before Caddy this rewrote Nextcloud's 443 handler to `127.0.0.1:443` or `127.0.0.1:8443` three times. Today it would hijack Caddy's 443.
3. **Funnel is off.** It works on the tailnet but not from outside.
4. **The wrong mode.** SSH through an `--https` entry closes immediately; it needs `--tcp`.
5. **The backend is down or crash-looping**, or listening on a different port from the one in the route. An app's own port setting is the port inside the container, so it must match the right-hand side of `ports:`.
6. **A `serve reset` removed entries** that weren't added back.
7. **Caddy itself is down.** Every `*.example.com` URL fails at once, while the Serve/Funnel entries still work. If `sudo docker ps | grep caddy` shows it restarting, see [A new container won't start or crash-loops](new-container-crash-loops.md).

Not this runbook: document editing says "cannot be reached" right after the host's LAN address changed. See [Document editing broke after the host's LAN address changed](document-editing-broke-after-lan-ip-change.md).

## Fix

**Recreate the Serve/Funnel entries** with explicit ports and targets. Run all three; it's safe to re-run them:

```bash
sudo tailscale funnel --bg --https=10000 http://localhost:8080
sudo tailscale funnel --bg --https=8443  http://localhost:9917
sudo tailscale serve  --bg --tcp=8313    tcp://localhost:8312
```

To remove a single entry: `sudo tailscale serve --https=<port> off` (or `--tcp=<port> off`). Never use a bare number with `funnel`.

**For a Caddy route:** fix the Caddyfile, then `caddy validate` and `caddy reload` (see the [Caddy page](../services/caddy.md#adding-or-changing-a-route)).

**For a backend:** fix the container (logs, ports, permissions), then check it locally before checking the URL.

## Verify

- `curl -sI https://<name>.example.com | head -1` from a tailnet device returns 200 (or a normal redirect).
- For the Funnel services, also test off the tailnet (a phone on mobile data). For Euro-Office, `docs/runbooks/euro-office-check.sh` checks everything end to end.
- Gitea SSH: `ssh -T gitea` from the laptop greets you by name.

## Related incidents

- [2026-07-19: Nextcloud 502 after turning on Funnel](../incidents/2026-07-19-nextcloud-502-after-enabling-funnel.md)
- [2026-08-05: Nextcloud 502 after re-enabling Funnel](../incidents/2026-08-05-nextcloud-502-after-re-enabling-funnel.md)
- [2026-08-14: Nextcloud down after funneling Collabora](../incidents/2026-08-14-nextcloud-down-after-funneling-collabora.md)
- [2026-10-22: Gitea SSH clone closed the connection](../incidents/2026-10-22-gitea-ssh-clone-connection-closed.md)
- [2026-10-24: Gitea down after `app.ini` edits](../incidents/2026-10-24-gitea-down-after-app-ini-edits.md)
- [2026-10-28: Euro-Office broken after switching it to Funnel](../incidents/2026-10-28-euro-office-broken-after-funnel-switch.md)
