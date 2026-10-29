# Tailscale and dhcpcd fought over the server's DNS

- **Date:** 2026-07-21
- **Status:** resolved
- **Service:** homelab (name resolution for every service)
- **Runbook:** [Names don't resolve](../runbooks/names-dont-resolve.md)
- **Source:** chats "Browser connectivity issues with services" and "Resolving DNS conflicts…" (2026-07-21). Unverified.

## Symptom

Tailscale reported a "dns-fight" health warning. On the server, `curl` couldn't resolve the server's own `.ts.net` name. Later the same day, the server could resolve either MagicDNS names or ordinary internet names, but not both, with the health message `setLinkDNS … resolve1.service not found`.

## Cause

dhcpcd rewrote `/etc/resolv.conf` from the Wi-Fi (`wlp130s0`) DHCP lease, overwriting what Tailscale had written. With no systemd-resolved, Tailscale could only write `100.100.100.100` on its own.

## Fix

Added `nohook resolv.conf` to `/etc/dhcpcd.conf`, so dhcpcd stopped touching the file and Tailscale could write it. Installing systemd-resolved was also suggested for the second symptom, but there's no record it was done.

## Since then

Verified 2026-10-28:
- `/etc/resolv.conf` is a plain file last changed on 2026-07-21, with `nameserver 100.100.100.100` and `nameserver 8.8.8.8`, and both kinds of name resolve.
- On 2026-09-10 the server moved from ifupdown/dhcpcd to NetworkManager ([incident](2026-09-10-server-offline-after-network-move.md)). dhcpcd is now inactive, so its `nohook` line is a leftover.
