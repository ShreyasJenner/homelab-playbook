# Anime season misidentified

- **Date:** 2026-10-22
- **Status:** resolved
- **Service:** Jellyfin
- **Runbook:** [Jellyfin shows wrong or missing episodes](../runbooks/jellyfin-wrong-episode-metadata.md)
- **Source:** a chat (2026-10-22). Unverified.

## Symptom

Jellyfin misidentified an anime season.

## Cause

The files used standard season naming, not the anime naming format (with absolute episode numbers).

## Fix

Renamed the files to the anime naming format ("It's been corrected now"). A related numbering problem the next day ("3.1, 3.2…") led to installing the TheTVDB plugin, which is installed on 2026-10-28.
