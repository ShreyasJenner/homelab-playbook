# `occ files:scan` says another process is already scanning

## Symptom

```
Starting scan for user 3 out of 3 (alice)
Another process is already scanning '/alice'
```

The scan stops for that user every time it's run.

## Check

Is a scan really running?

```bash
sudo docker exec nextcloud_app ps aux | grep -i '[o]cc'
```

If a `files:scan` is listed, let it finish or kill it (`sudo docker exec nextcloud_app kill <PID>`). Check other terminals and tmux sessions too.

## Likely causes

1. **A stale lock from an interrupted scan** (Ctrl+C, an SSH disconnect, a container restart). Nextcloud has no Redis here, so locks live in the database table `oc_file_locks`. They expire after about an hour, but they don't always clear cleanly.
2. **A real scan is still running**, or a desktop client syncing a large folder is holding locks.
3. **The scan overlapped the nightly backup** (about 02:30), which stops every stack.

## Fix

If nothing is running, clear the stale locks, then scan again. This is what worked in 2026-10. The first command prompts for the MariaDB root password, which lives in `~/docker/nextcloud`'s compose or `.env`; don't paste it on the command line.

```bash
sudo docker exec -it nextcloud_db mysql -u root -p nextcloud -e "DELETE FROM oc_file_locks WHERE 1;"
cd ~/docker/nextcloud && sudo docker compose restart
sudo docker exec -u www-data nextcloud_app php occ files:scan --all     # or --path="/<user>/files"
```

If the table name differs (the prefix isn't `oc_`), find it with `SHOW TABLES LIKE '%file_locks';`.

**Prevention (suggested, not done):** add a Redis container and set `memcache.locking` in Nextcloud's config, so locks clean up properly.

## Verify

The scan runs through every user with no "already scanning" line.

## Related incidents

- [2026-09-28: files:scan blocked by a stale lock](../incidents/2026-09-28-nextcloud-scan-blocked-by-stale-lock.md)
- [2026-10-04: files:scan blocked by a stale lock again](../incidents/2026-10-04-nextcloud-scan-blocked-by-stale-lock-again.md)
