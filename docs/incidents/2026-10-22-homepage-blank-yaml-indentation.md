# Homepage blank from a YAML indentation error

- **Date:** 2026-10-22
- **Status:** resolved
- **Service:** Homepage
- **Runbook:** [Homepage is blank, or a tile is red](../runbooks/homepage-blank-or-tile-red.md)
- **Source:** chat "Homepage dashboard via Docker" (2026-10-22). Unverified.

## Symptom

A blank page. The log said `Error parsing service "Nextcloud" from config. Ensure required fields are present.`

## Cause

In `services.yaml`, the Nextcloud tile's fields were indented at the same level as `- Nextcloud:`.

## Fix

Re-indented: groups at column 0, services 4 spaces, fields 8 spaces, spaces only.
