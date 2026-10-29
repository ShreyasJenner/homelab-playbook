# Updating containers

A procedure rather than a fix. Containers are updated with `~/docker/stacks.sh`.

## Before

- **Not around 02:30**, when the nightly backup stops every stack.
- **Know what a plain `update` covers.** It acts on `DEFAULT_STACKS` in the script, which (2026-10-28) **doesn't include `gitea` or `vaultwarden`**. Name those explicitly.
- **Know the special cases:**
  - Gitea is pinned to a version tag, so `update` doesn't change it; edit the tag to upgrade.
  - Redlib is built locally; `pull` can't update it. Use the [Redlib update steps](../services/redlib.md#updating).
  - Caddy may be built from a Dockerfile (unverified); if so, it needs `docker compose build --pull`.
  - Everything else follows `latest` (Uptime Kuma `:2`, Memos `:stable`), so an update can bring breaking changes, as happened with a Loki config change.

## Run

```bash
cd ~/docker
./stacks.sh update                          # the default list
./stacks.sh update gitea vaultwarden    # the ones the list misses
```

Read the output for `!! <stack> failed` lines. The script carries on after a failure and exits with 1.

## After

```bash
sudo docker ps -a --filter status=exited --filter status=restarting --format '{{.Names}}\t{{.Status}}'   # anything down?
sudo docker ps --filter health=unhealthy --format '{{.Names}}'   # redlib-* always shows here (broken healthcheck)
```

- Check Uptime Kuma is all green, and open a few `https://<name>.example.com` pages.
- Reclaim space from old images, if wanted. The script doesn't do this:
  ```bash
  sudo docker image prune -f
  ```

## Roll back

Pin the previous image tag in the stack's compose file (`image: <name>:<old version>`), then `sudo docker compose up -d`. The nightly backup writes `~/docker/.image-manifest.txt`, which records the image digests that were running; restic keeps older copies.

## Related incidents

- [2026-10-04: `stacks.sh` found no compose files](../incidents/2026-10-04-stacks-sh-no-compose-file-found.md)
