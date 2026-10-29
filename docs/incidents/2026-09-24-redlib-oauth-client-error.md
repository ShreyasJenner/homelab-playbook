# Redlib: OAuth client error with the published image

- **Date:** 2026-09-24
- **Status:** resolved
- **Service:** Redlib
- **Runbook:** [Redlib is broken or won't update](../runbooks/redlib-broken-or-wont-update.md)
- **Source:** chat "Redlib container setup error" (2026-09-24). Unverified.

## Symptom

The published Redlib image failed at startup: "Failed to create OAuth client: expected value at line 1 column 1".

## Cause

A change on Reddit's side that the published image didn't handle (upstream issue #551).

## Fix

Built the image from source as `redlib-local`. Since 2026-10-21 it's built from the polak14 fork, after "Failed to parse page JSON data" errors on 2026-10-20 that also hit public instances. Updating means rebuilding, never pulling.
