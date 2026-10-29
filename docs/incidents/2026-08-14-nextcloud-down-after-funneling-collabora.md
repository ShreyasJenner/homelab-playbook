# Nextcloud down after funneling Collabora

- **Date:** 2026-08-14
- **Status:** resolved
- **Service:** Nextcloud (and Collabora, since retired)
- **Runbook:** [A service URL returns 502 or closes the connection](../runbooks/service-url-returns-502.md)
- **Source:** chat "Enabling document editing in Nextcloud" (2026-08-07 onwards). Unverified.

## Symptom

Nextcloud became unreachable right after Collabora was moved onto Funnel `:8443`.

## Cause

`tailscale funnel --bg 8443` (a bare number) rewrote Nextcloud's 443 handler to `127.0.0.1:8443`, on top of an earlier bad `127.0.0.1:443` target. This was the third time the bare-number form broke Nextcloud.

## Fix

Re-entered every mapping in the explicit form, `tailscale funnel --bg --https=<port> <target>`, after which "the funnel status is now fine".
