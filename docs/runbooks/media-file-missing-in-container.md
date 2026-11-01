# A container says a media file is missing

## Symptom

- A media app (Jellyfin, Kavita) lists an item as "missing file" or "unable to find media file", although the file plays or opens on the host.

## Check

Run on homelab. Replace `<app>` and `<folder>` with the container and the media folder as the container sees it, for example `kavita` and `/manga`.

```bash
{
echo '--- links dangling inside the container'; sudo docker exec <app> find <folder> -xtype l
echo '--- the same links on the host (control)'; find /mnt/hdd-4tb/media -xtype l
echo '--- link targets'; find /mnt/hdd-4tb/media -type l -printf '%p -> %l\n' | head -20
echo '--- unreadable files as 1000'; sudo docker exec -u 1000:1000 <app> find <folder> -type f ! -readable | head
} 2>&1 | tee ~/media-missing-check.txt
```

## Likely causes

1. **An absolute symlink whose target isn't mounted at the same path inside the container.** The link dangles in the container, but not on the host. That happens when the container mounts the disk at `/data` and the link points at `/mnt/hdd-4tb/…`.
2. **The symlink's target is gone on the host too.** It dangles in both places. For example, the target file was deleted or moved.
3. **The app's library path doesn't exist in the container** (Jellyfin pointed at `/media`).
4. **Permissions:** the file isn't readable as uid 1000.

## Fix

- **Causes 1 and 2:** replace the symlinks with hardlinks; the links and their targets are on one disk. Write a manifest first, so that the links can be restored:
  ```bash
  cd /mnt/hdd-4tb/media
  find <subfolder> -type l -printf '%p\t%l\n' > ~/symlinks-manifest-YYYYMMDD.tsv
  while IFS=$'\t' read -r p t; do
    [ -e "$t" ] || { echo "SKIP $p"; continue; }
    if [ -d "$t" ]; then cp -al "${t%/}" "$p.hl-tmp" && rm "$p" && mv "$p.hl-tmp" "$p"
    else ln "$t" "$p.hl-tmp" && mv -f "$p.hl-tmp" "$p"; fi
  done < ~/symlinks-manifest-YYYYMMDD.tsv
  ```
  For a target that's gone (cause 2), put the file back, then rescan in the app.
  Undo: `while IFS=$'\t' read -r p t; do [ -L "$p" ] || { rm -rf "$p" && ln -s "$t" "$p"; }; done < ~/symlinks-manifest-YYYYMMDD.tsv`. That removes only the new links, never the originals.
- **Cause 3:** point the library at a path that exists in the container. See [Jellyfin shows wrong or missing episodes](jellyfin-wrong-episode-metadata.md).
- **Cause 4:** `ls -l` the file, then fix its owner on the host (`chown 1000:1000`).

## Related incidents

- [2026-09-04: Jellyfin symlinked show not found](../incidents/2026-09-04-jellyfin-symlinked-show-not-found.md)
