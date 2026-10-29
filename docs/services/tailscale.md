# Tailscale

```
Status:     live
Host:       homelab (native install, not a container), version 1.102.2
Exposure:   n/a: it is the access layer. Funnel makes two services public.
URL:        homelab.tail0000.ts.net, 192.0.2.10
Config:     no config file; Serve/Funnel state lives in tailscaled (`sudo tailscale serve status`).
            Admin console: MagicDNS on, HTTPS certificates on, `funnel` node attribute in the ACLs
Depends on: Tailscale's coordination servers; the host's DNS setup (/etc/resolv.conf)
Verified:   2026-10-28
```

## What it's for

The private network that lets your own devices reach the homelab without opening any port on the router. Every service URL needs it (ADR 0004):

- **Caddy** answers `*.example.com` only on `tailscale0`, so those names only work for tailnet devices.
- **Serve and Funnel** handle the three exceptions that bypass Caddy (below).
- **SSH** to homelab (port 2207) goes over the tailnet as well. Tailscale limits *who can even try*; the SSH key decides *who gets in*.

Devices on the tailnet (2026-10-28): `homelab`, `desktop-pc` (Windows), `laptop-2`, `laptop-1` (Linux), `phone`.

## Why this one

- Chosen on day one (2026-07-18) as a secure way to reach the server from outside the home network without port forwarding. The home connection is behind CGNAT, so port forwarding wouldn't have worked anyway.
- **Headscale was considered and rejected** (2026-08): it doesn't provide Serve, Funnel or managed HTTPS certificates, which this setup relies on.
- Funnel is the only way to make something public without a router port. It works only on the `.ts.net` name and on ports 443, 8443 and 10000.

## How it's set up

Installed with the official script (`curl -fsSL https://tailscale.com/install.sh | sh`, then `sudo tailscale up`). MagicDNS and HTTPS certificates are switched on in the admin console. Funnel needs the `funnel` node attribute in the ACLs.

### Serve and Funnel entries

These three are the complete Serve/Funnel config. Caddy holds 443, which is why the two public services use 10000 and 8443.

| Entry | Target | Mode | Service |
|---|---|---|---|
| `https://homelab.tail0000.ts.net:10000` | `http://localhost:8080` | Funnel (public) | Nextcloud |
| `https://homelab.tail0000.ts.net:8443` | `http://localhost:9917` | Funnel (public) | Euro-Office |
| `tcp://homelab.tail0000.ts.net:8313` | `tcp://localhost:8312` | Serve TCP (tailnet-only) | Gitea SSH |

To recreate them, for example after a `serve reset`, run all three lines. A reset wipes every entry, TCP ones included:

```bash
sudo tailscale funnel --bg --https=10000 http://localhost:8080
sudo tailscale funnel --bg --https=8443  http://localhost:9917
sudo tailscale serve  --bg --tcp=8313    tcp://localhost:8312
```

### Gotchas

These caused most of the past outages. See the [runbook](../runbooks/service-url-returns-502.md).

- **Always give Funnel both the port and the target.** `tailscale funnel --bg <N>` with a bare number doesn't mean "turn on Funnel for port N". It means "funnel public 443 to `localhost:N`", and it overwrites the 443 handler. This broke Nextcloud three times.
- **Check the target for typos.** `locahost` doesn't resolve, and the result is a 502 with nothing in the service's logs.
- **`--https` speaks HTTP behind TLS, so SSH through it closes at once.** SSH needs `--tcp`. Funnel can't carry SSH at all.
- **A container can't reliably reach its own host's Funnel URL** (the request times out). That's why Nextcloud and Euro-Office call each other on the LAN address, and only the browser uses the Funnel URL.
- **`--set-path` doesn't strip the path prefix,** so apps without a base-URL setting break under a subpath. This sank the Collabora `/collabora` attempt.
- **Funnel exposes Nextcloud's whole login page**, not only share links. Nextcloud 2FA is off (follow-up in the plan).
- When the text output of `serve status` is unclear, `sudo tailscale serve status --json` shows the exact `Proxy` target.

### DNS on homelab

`/etc/resolv.conf` is a plain file with `nameserver 100.100.100.100` (MagicDNS) and `nameserver 8.8.8.8`, last changed on 2026-07-21. NetworkManager is active; dhcpcd and systemd-resolved are inactive. `/etc/dhcpcd.conf` still has `nohook resolv.conf` from the [2026-07-21 fix](../incidents/2026-07-21-server-dns-fight-with-dhcpcd.md).

## Retired

- **One Serve HTTPS port per service** (`:6743` Navidrome, `:7843` Vaultwarden/Kavita, `:9343` Memos, `:10000` Donetick, `:3407` Invidious, and others). Retired on 2026-10-21 with a `serve reset`, because ports drifted from the notes without any error, port numbers got reused, Bitwarden treated every port as the same site, Funnel only allows three ports, and the reset scripts were fragile. Replaced by [Caddy](caddy.md) on `*.example.com`.
- **Nextcloud on Funnel `:443`.** It moved to `:10000` on 2026-10-21 so Caddy could have 443.

Some app settings still carry the old `ts.net:<port>` addresses: Vaultwarden's `DOMAIN`, Mindwtr's CORS origin and Gitea's `ROOT_URL` (follow-ups 16–18 in the plan).

## Gaps

- Is node key expiry turned off for homelab? If its key expires, every service drops off the tailnet until someone re-authenticates on the host. Check the Machines page in the admin console.
- What keeps NetworkManager from rewriting `/etc/resolv.conf`? It hasn't changed since 2026-07-21 even though NetworkManager is active. Check `grep -rn dns /etc/NetworkManager/` and `lsattr /etc/resolv.conf`.

## Runbooks

- [A service URL returns 502 or closes the connection](../runbooks/service-url-returns-502.md)
- [Names don't resolve: MagicDNS and the host's DNS](../runbooks/names-dont-resolve.md)

## Incidents

- [2026-07-18: laptop couldn't reach the server](../incidents/2026-07-18-laptop-not-on-tailnet.md)
- [2026-07-19: Nextcloud 502 after turning on Funnel](../incidents/2026-07-19-nextcloud-502-after-enabling-funnel.md)
- [2026-07-21: Tailscale and dhcpcd fought over the server's DNS](../incidents/2026-07-21-server-dns-fight-with-dhcpcd.md)
- [2026-08-05: Nextcloud 502 after re-enabling Funnel](../incidents/2026-08-05-nextcloud-502-after-re-enabling-funnel.md)
- [2026-08-14: Nextcloud down after funneling Collabora](../incidents/2026-08-14-nextcloud-down-after-funneling-collabora.md)
- [2026-10-28: Euro-Office broken after switching it to Funnel](../incidents/2026-10-28-euro-office-broken-after-funnel-switch.md)
