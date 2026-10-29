# Names don't resolve: MagicDNS and the host's DNS

Covers `homelab.tail0000.ts.net` and `*.example.com` names failing to resolve, on a client or on homelab itself. These broke repeatedly in July and August 2026, each time because two programs disagreed about who writes `/etc/resolv.conf`.

## Symptom

- The browser says "server not found" (`NS_ERROR_UNKNOWN_HOST`), or `nslookup` returns NXDOMAIN, while native apps or IP addresses still work.
- `tailscale status` shows a health warning such as "dns-fight", "failed to fetch the DNS configuration" or "resolve1.service not found".
- On homelab, `curl` can't resolve its own `.ts.net` name, or MagicDNS works but ordinary internet names don't (or the other way round).

## Check

**On the device that fails:**

```bash
tailscale status | head -3; tailscale status | grep -i -A3 health   # on the tailnet at all? any DNS health warning?
nslookup homelab.tail0000.ts.net                             # takes a hostname, not a URL
nslookup homelab.tail0000.ts.net 100.100.100.100             # ask MagicDNS directly
nslookup example.com                                                 # ordinary names still work?
```

**On a Linux host, find out who owns `/etc/resolv.conf`:**

```bash
ls -l /etc/resolv.conf; cat /etc/resolv.conf     # a symlink into /run/systemd/resolve/ = systemd-resolved
systemctl is-active NetworkManager systemd-resolved dhcpcd
grep -rn -E '^\s*dns|rc-manager' /etc/NetworkManager/ 2>/dev/null
grep -n nohook /etc/dhcpcd.conf 2>/dev/null
```

Known good state on homelab (2026-10-28):
- `/etc/resolv.conf` is a plain file containing `nameserver 100.100.100.100` and `nameserver 8.8.8.8`.
- NetworkManager is active; dhcpcd and systemd-resolved are inactive.

## Likely causes

1. **The device isn't on the tailnet**, or Tailscale is off. Nothing resolves or routes.
2. **The device asks the router for DNS instead of MagicDNS** (`100.100.100.100`). The router returns NXDOMAIN for `.ts.net` names.
3. **A DHCP client or NetworkManager rewrites `/etc/resolv.conf`** after Tailscale wrote it ("dns-fight").
4. **No systemd-resolved, so Tailscale writes only `100.100.100.100`.** Depending on the setup, ordinary internet names may then stop resolving.

## Fix

- **Cause 1:** log the device into the tailnet (`sudo tailscale up` or the app), and check that it appears in `tailscale status`.
- **Cause 2:** let Tailscale manage DNS on the client (`--accept-dns=true`, the default), or point it at `100.100.100.100`.
- **Cause 3, dhcpcd:** add `nohook resolv.conf` to `/etc/dhcpcd.conf`, restart dhcpcd, then `sudo systemctl restart tailscaled`. This was the server fix on 2026-07-21.
- **Cause 3, NetworkManager:** either let systemd-resolved own DNS (`systemctl enable --now systemd-resolved`, and `dns=systemd-resolved` in NetworkManager's config), or stop NetworkManager writing the file (`dns=none`). Then restart NetworkManager and tailscaled.
- **Cause 4:** install and enable systemd-resolved, so Tailscale can do split DNS (MagicDNS for the tailnet, the normal resolver for everything else).

## Verify

- Both `nslookup homelab.tail0000.ts.net` and `nslookup example.com` answer.
- `tailscale status` shows no DNS health warning.
- `curl -sI https://music.example.com | head -1` returns 200 from the device.

## Related incidents

- [2026-07-18: laptop couldn't reach the server](../incidents/2026-07-18-laptop-not-on-tailnet.md)
- [2026-07-21: Tailscale and dhcpcd fought over the server's DNS](../incidents/2026-07-21-server-dns-fight-with-dhcpcd.md)
