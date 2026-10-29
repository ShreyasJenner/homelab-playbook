# Certificate blocked by a stale ACME TXT record

- **Date:** 2026-10-21
- **Status:** resolved
- **Service:** Caddy (the `*.example.com` wildcard certificate)
- **Runbook:** none
- **Source:** chat "Port allocation on self-hosted servers" (2026-10-21). Unverified.

## Symptom

Caddy couldn't get its certificate. The DNS provider's API refused it: a record with the same name and content already existed.

## Cause

A failed earlier attempt had left an `_acme-challenge` TXT record at the DNS provider, so the DNS-01 challenge couldn't create its own.

## Fix

Deleted the stale `_acme-challenge` TXT records in the DNS provider's dashboard and restarted Caddy. The log then showed "certificate obtained successfully".

If certificate renewal ever fails, check for leftover `_acme-challenge` records first.
