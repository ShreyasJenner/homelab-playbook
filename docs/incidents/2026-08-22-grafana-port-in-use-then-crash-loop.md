# Grafana's port already in use, then a crash loop

- **Date:** 2026-08-22
- **Status:** resolved (how isn't recorded)
- **Service:** Grafana (monitoring stack)
- **Runbook:** [A new container won't start or crash-loops](../runbooks/new-container-crash-loops.md)
- **Source:** chat "Resume improvement phase 2 next steps" (2026-08-09; messages from 2026-08-22). Unverified.

## Symptom

On the first `up`, the Grafana host port was "already in use". After the port was changed, connections were refused and `ss` showed nothing listening: the container was crash-looping.

## Cause

The first host port was one Tailscale Serve already held. The crash loop's cause wasn't recorded. The suspects were the data folder's owner (Grafana runs as uid 472) and an unset `.env` variable.

## Fix

The user reported it fixed without saying how. Grafana has been on host port `4710` since, and Serve no longer fronts it (Caddy since 2026-10-21).
