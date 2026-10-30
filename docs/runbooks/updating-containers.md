# Updating containers

A procedure rather than a fix. Containers are updated with `~/docker/stacks.sh`.

## Before

- **Not around 02:30**, when the nightly backup stops every stack.
- **Know what a plain `update` covers.** It acts on `DEFAULT_STACKS` in the script, which covers every live stack since 2026-10-30 (`gitea` and `vaultwarden` were added; follow-up 12). `./stacks.sh list` prints it.
- **Know the special cases:**
  - Gitea is pinned to a version tag, so `update` doesn't change it; edit the tag to upgrade.
  - Redlib is built locally; `pull` can't update it. Use the [Redlib update steps](../services/redlib.md#updating).
  - Caddy may be built from a Dockerfile (unverified); if so, it needs `docker compose build --pull`.
  - Everything else follows `latest` (Uptime Kuma `:2`, Memos `:stable`), so an update can bring breaking changes, as happened with a Loki config change.

## Run

```bash
cd ~/docker
./stacks.sh update                # every stack in the default list
./stacks.sh update vaultwarden    # or just the ones named
```

Read the output for `!! <stack> failed` lines. The script carries on after a failure and exits with 1.

After the loop, `update` runs `docker image prune -f` (`==> prune: dangling images`). That removes the old images the update left untagged, so the previous version is gone locally; see [Roll back](#roll-back). It runs even if a stack failed. Added 2026-10-30, verified that day.

## After

```bash
sudo docker ps -a --filter status=exited --filter status=restarting --format '{{.Names}}\t{{.Status}}'   # anything down?
sudo docker ps --filter health=unhealthy --format '{{.Names}}'   # redlib-* always shows here (broken healthcheck)
```

- Check Uptime Kuma is all green, and open a few `https://<name>.example.com` pages.
- Images that no container uses at all (retired stacks) aren't dangling, so the script's prune leaves them. Check `sudo docker system df` now and then; on 2026-10-30 `sudo docker image prune -a -f` and `sudo docker builder prune -f` reclaimed 51 GB and 20 GB.

## Roll back

Pin the previous image tag in the stack's compose file (`image: <name>:<old version>`), then `sudo docker compose up -d`, which pulls it again (the script's prune deleted the local copy). The nightly backup writes `~/docker/.image-manifest.txt`, which records the image digests that were running; restic keeps older copies.

## Related incidents

- [2026-10-04: `stacks.sh` found no compose files](../incidents/2026-10-04-stacks-sh-no-compose-file-found.md)
