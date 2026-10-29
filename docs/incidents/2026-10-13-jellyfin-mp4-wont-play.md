# One MP4 wouldn't play in Jellyfin

- **Date:** 2026-10-13
- **Status:** resolved
- **Service:** Jellyfin
- **Runbook:** [Jellyfin shows wrong or missing episodes](../runbooks/jellyfin-wrong-episode-metadata.md)
- **Source:** chat "Jellyfin MP4 playback error" (2026-10-13). Unverified.

## Symptom

One 1.9 GB MP4 wouldn't play; other files were fine.

## Cause

The file's `moov` atom (its index) was at the end, so playback couldn't start until the whole file was read.

## Fix

```bash
ffmpeg -i in.mp4 -c copy -movflags +faststart out.mp4
```

This moves the index to the front without re-encoding.
