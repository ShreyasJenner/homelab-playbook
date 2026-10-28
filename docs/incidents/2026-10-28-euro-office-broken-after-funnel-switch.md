# Euro-Office broken after switching it to Funnel

- **Date:** recorded 2026-10-28; the break happened before that (exact day unknown)
- **Status:** open
- **Service:** Euro-Office (and Nextcloud document editing, which depends on it)
- **Runbook:** none yet

## Symptom

Euro-Office is not working. Its intended Exposure is public (ADR 0004), but it is currently tailnet-only.

## What changed

Euro-Office was tailnet-only and working. It broke after an attempt to move it to Funnel so that outsiders could edit shared documents.

## Leads (unverified, from chat history)

These come from the "Enabling document editing in Nextcloud" chat (2026-08-07 to 2026-09-12) and have not been checked against the host (ADR 0002).

- Euro-Office was earlier funnelled on `:8443`, pointing at a local port. The chat mentions both `9917` and `9918` at different points, so check which one the container actually listens on.
- Nextcloud stores two internal addresses for the document server (Admin Settings → Nextcloud Office): the Euro-Office address for internal requests from Nextcloud, and the Nextcloud address for internal requests from Euro-Office. Both contain the host's LAN IP, which changed once already (2026-09-12).
- Nextcloud's `trusted_domains` has to include whatever address the requests arrive with.
- JWT secrets must match exactly between the Euro-Office container and Nextcloud's connector. Leading whitespace in the env value broke this once.
- Euro-Office blocks requests to private IPs by default (`ALLOW_PRIVATE_IP_ADDRESS`).

## Cause

Unknown.

## Fix

Not fixed yet. To be investigated in a separate `/diagnosing-bugs` session, which closes this note.
