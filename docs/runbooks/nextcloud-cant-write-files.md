# Nextcloud can't create, move or delete files

## Symptom

- "Creating new folder failed", or "you don't have access to this resource" (403) in the web UI or the desktop client.
- Files can be read but not moved or deleted.
- The Nextcloud log shows `Sabre\DAV\Exception\Forbidden`, `mkdir(): Read-only file system` or "permission denied".

It usually happens in an external storage folder or after an import.

## Check

**1. Ask PHP directly.** It prints the real reason:

```bash
sudo docker exec -u www-data nextcloud_app php -r "var_dump(mkdir('<container path>/t')); var_dump(error_get_last());"
sudo docker exec -u www-data nextcloud_app rmdir '<container path>/t'   # clean up if it worked
```

**2. Is the mount read-only?**

```bash
sudo docker inspect --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} rw={{.RW}}{{"\n"}}{{end}}' nextcloud_app
findmnt /mnt/hdd-4tb          # the host disk itself mounted ro?
```

**3. Who owns it, and can uid 33 write to it?** Nextcloud runs as `www-data`, uid 33. Moving or deleting needs write access on the **parent folder**, not just the file.

```bash
stat -c '%U:%G (%u:%g) %A %n' <host path> <host path>/..
getfacl -p <host path> 2>/dev/null | head
```

**4. Nextcloud's own settings.** Is the external storage marked read-only, or not shared with that user? (Admin settings → External storage.) Is the share itself read-only?

## Likely causes

1. **The volume is mounted read-only** (`:ro` in compose), or the host disk went read-only.
2. **uid 33 has no write permission** on the folder or its parent. The host folders belong to `alice` (uid 1000).
3. **Files imported with `docker cp` are owned by root or 1000**, not `www-data`.
4. **A Nextcloud setting**: the external storage is read-only, or the share has no edit permission.

## Fix

- **Cause 1:** remove `:ro` from the volume in `~/docker/nextcloud/docker-compose.yml`, then `sudo docker compose up -d` (not `restart`).
- **Cause 2:** give uid 33 write access. Both of these have been used here:
  ```bash
  sudo chmod -R o+rwX <host path>                     # simplest; anyone on the host can write
  # or a shared group:
  sudo chgrp -R www-data <host path>
  sudo chmod -R g+rwX <host path>
  sudo find <host path> -type d -exec chmod g+s {} +  # new files inherit the group
  ```
  ACLs (`setfacl -R -m u:33:rwx` plus a default ACL `-d -m u:33:rwx`) are the tidier option. Don't `chown -R 33:33` a folder you also use from the host or another container.
- **Cause 3:** `sudo docker exec nextcloud_app chown -R www-data:www-data /var/www/html/data/<user>/files/`
- Afterwards, `sudo docker exec -u www-data nextcloud_app php occ files:scan --path="/<user>/files"` (or `--all`).

Rootless Docker won't fix this. It remaps uids and makes it worse.

## Verify

The PHP `mkdir` test returns `bool(true)`, and the action works in the client.

## Related incidents

- [2026-08-23: external storage folder was read-only](../incidents/2026-08-23-nextcloud-external-storage-read-only.md)
- [2026-09-02: couldn't create folders in new external storage](../incidents/2026-09-02-nextcloud-external-storage-permission-denied.md)
- [2026-09-30: couldn't move or delete files in external storage](../incidents/2026-09-30-nextcloud-cant-move-or-delete-files.md)
- [2026-10-06: imported files had the wrong owner](../incidents/2026-10-06-nextcloud-files-imported-with-wrong-owner.md)
