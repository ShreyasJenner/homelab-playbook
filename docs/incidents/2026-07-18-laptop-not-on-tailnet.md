# Laptop couldn't reach the server

- **Date:** 2026-07-18
- **Status:** resolved
- **Service:** every service (from one client)
- **Runbook:** [Names don't resolve](../runbooks/names-dont-resolve.md)
- **Source:** chat "Setting up home server music streaming" (2026-07-18). Unverified.

## Symptom

From the laptop, Navidrome on the server's tailnet address timed out, and so did `ping`.

## Cause

The laptop had never been added to the tailnet. Tailnet addresses are only reachable from devices that are logged in to it.

## Fix

Logged the laptop in to Tailscale. Any new device has to be added to the tailnet before it can reach the homelab.
