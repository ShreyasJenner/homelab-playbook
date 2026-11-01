# Jellyfin: symlinked show not found

- **Date:** 2026-09-04
- **Status:** resolved
- **Service:** Jellyfin
- **Runbook:** [Jellyfin shows wrong or missing episodes](../runbooks/jellyfin-wrong-episode-metadata.md), [A container says a media file is missing](../runbooks/media-file-missing-in-container.md)
- **Source:** chat "Jellyfin symlinks configuration" (2026-09-04). Unverified.

## Symptom

A show built from symlinks said "unable to find media file", and its seasons were empty.

## Cause

The compose file uses identity mounts (each folder mounted at its own host path, so absolute symlinks resolve), but the library in Jellyfin pointed at `/media`, which doesn't exist in the container.

## Fix

Pointed the library at the real container path, the same as the host path.
