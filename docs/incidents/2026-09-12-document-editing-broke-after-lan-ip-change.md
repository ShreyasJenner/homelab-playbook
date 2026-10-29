# Document editing broke after the LAN address changed

- **Date:** 2026-09-12
- **Status:** resolved
- **Service:** Euro-Office (document editing in Nextcloud)
- **Runbook:** [Document editing broke after the host's LAN address changed](../runbooks/document-editing-broke-after-lan-ip-change.md)
- **Source:** chat "Enabling document editing in Nextcloud" (last messages, 2026-09-12). Unverified; end state verified 2026-10-28.

## Symptom

After homelab moved to a new network ([2026-09-10](2026-09-10-server-offline-after-network-move.md)), Euro-Office stopped working from Nextcloud.

## Cause

Nextcloud and Euro-Office call each other on the LAN address, and the address had changed from `203.0.113.10` to `198.51.100.10`. Both internal addresses in the connector, and the `trusted_domains` entry, still held the old one.

## Fix

Updated both internal addresses and `trusted_domains` to `198.51.100.10`, then restarted both containers. How exactly isn't recorded, but on 2026-10-28 all three hold the new address.

The address still isn't reserved in the router, so this will happen again on the next change (follow-up 1).
