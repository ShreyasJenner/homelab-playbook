# Homepage couldn't bind port 3000

- **Date:** 2026-10-22
- **Status:** resolved
- **Service:** Homepage
- **Runbook:** [Connection reset after choosing or changing a port](../runbooks/connection-reset-after-port-change.md)
- **Source:** chat "Homepage dashboard via Docker" (2026-10-22). Unverified.

## Symptom

Homepage logged `IPv6 bind failed: listen EADDRINUSE :::3000` and fell back to IPv4.

## Cause

Homepage runs on the host network, so its default port 3000 is a host port, and Invidious already publishes 3000 (probably what held it).

## Fix

It ran on the IPv4 fallback at first. Since the two-instance setup (2026-10-24), each instance sets `PORT` (9640, 9641).
