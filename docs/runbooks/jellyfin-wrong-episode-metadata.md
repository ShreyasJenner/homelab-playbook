# Jellyfin shows wrong or missing episodes

## Symptom

- A season is misidentified, or anime episodes are numbered oddly ("3.1, 3.2…").
- A show is "unable to find media file", or seasons are empty.
- One file won't play while others do.

## Check

1. **The names:** does the folder name end with `[tvdbid-…]`, and do the file names have `SxxExx`?
2. **In Jellyfin:** Dashboard → Libraries → the library's path must be the full host path (for example `/mnt/hdd-4tb/media/anime`), not `/media`. Is TheTVDB first among the metadata downloaders for that library?
3. **On disk:**
   ```bash
   sudo docker exec jellyfin ls -l "<path to the show>" | head
   find /mnt/hdd-4tb/media/movies -maxdepth 2 -type l | head       # symlinks whose targets must be mounted
   ```

## Likely causes

1. **An anime uses standard naming** instead of the anime format (absolute episode numbers).
2. **TVDB and TMDb number seasons and episodes differently.**
3. **The library points at a path that doesn't exist in the container**, or a symlink's target isn't mounted at the same absolute path.
4. **For one unplayable MP4:** the `moov` atom is at the end of a large file.

## Fix

- **Causes 1 and 2:** rename the files to the anime naming format. In Jellyfin, put TheTVDB first for that library, then the show's ⋯ → Identify, or Refresh metadata → Replace all metadata.
- **Cause 3:** point the library at the identity-mounted path. For symlinks, mount the target folder at its own host path in `~/docker/jellyfin/docker-compose.yml`, then `sudo docker compose up -d`.
- **Cause 4:**
  ```bash
  ffmpeg -i in.mp4 -c copy -movflags +faststart out.mp4
  ```

## Related incidents

- [2026-09-04: symlinked show not found](../incidents/2026-09-04-jellyfin-symlinked-show-not-found.md)
- [2026-10-13: one MP4 wouldn't play](../incidents/2026-10-13-jellyfin-mp4-wont-play.md)
- [2026-10-22: anime season misidentified](../incidents/2026-10-22-jellyfin-anime-season-misidentified.md)
