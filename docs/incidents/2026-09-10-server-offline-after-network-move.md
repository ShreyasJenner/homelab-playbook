# Server offline after moving to a new network

- **Date:** 2026-09-10
- **Status:** resolved
- **Service:** homelab (everything)
- **Runbook:** none
- **Source:** chat "Server network access tool" (2026-09-10). Unverified.

## Symptom

After the server moved to a new home network, it had no connectivity: the interfaces were down, with only link-local IPv6 addresses.

## Cause

Networking was still configured with ifupdown. Its Wi-Fi stanza named the old network's SSID, nothing ran a DHCP client on Ethernet, and NetworkManager wasn't managing `wlp130s0`.

## Fix

Removed the ifupdown Wi-Fi stanza and let NetworkManager manage `wlp130s0`. The server got `198.51.100.10` (it had been `203.0.113.10` on the old network).

## Follow-on effects

- The LAN address change broke Euro-Office for a while, because Nextcloud and Euro-Office call each other on the LAN address ([2026-09-12](2026-09-12-document-editing-broke-after-lan-ip-change.md)).
- The address still isn't reserved in the router (follow-up 1 in the plan).
