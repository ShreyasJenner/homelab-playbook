# A new container won't start or crash-loops

For a service you've just set up, or whose config you've just changed: it exits straight away, or `docker ps` shows it "Restarting". For an established service that stops answering, start with [A service URL returns 502](service-url-returns-502.md) instead.

## Symptom

- `docker compose up -d` fails with a mount error, or the container keeps restarting.
- Another service (Grafana, a browser) says it can't connect, because the container never stays up.

## Check

```bash
cd ~/docker/<stack>
sudo docker compose ps -a                          # Restarting / Exited (1)?
sudo docker compose logs --tail 50 <service>       # the last lines before each exit
ls -la <each bind-mount source>                    # a directory where a file should be? who owns it?
sudo docker image inspect <image> --format '{{.Config.User}}'   # the uid it runs as (empty = root)
sudo ss -tlnp | grep ':<host port>\b'              # is the host port already taken?
```

## Likely causes

| Log or error | Cause |
|---|---|
| `error mounting "…/<file>" … not a directory` | The config file didn't exist at the first `up`, so Docker created a **directory** at that path. |
| `permission denied` on `mkdir` or open, under a data path | The data folder isn't owned by the container's uid (Grafana 472, Prometheus 65534, Loki 10001), **or** the config points a writable path outside the mounted volume. |
| `invalid … config`, `field … not found`, `Mismatched type for flag` | The config doesn't match what this version expects. Images on `latest` change their config format between releases (Loki 3.x needs `delete_request_store` when retention is on). In YAML, a setting that takes a list must be a list. |
| `missing port in address`, `bind: address already in use` | A listen address was written without its colon (`80` instead of `:80`), or the host port is held by another container or Tailscale Serve. |

## Fix

- **Directory instead of file:** `sudo docker compose down <service>`, `sudo rmdir <path>`, create the real file, then `sudo docker compose up -d`.
- **Ownership:** `sudo chown -R <uid>:<uid> <data folder>`. In the app's config, keep every writable path (data, WAL, compactor, cache) under the mounted folder, never under `/tmp` or `/var/…` inside the container.
- **Config format:** validate before restarting when the image has a check mode (Loki: `-verify-config`; see the 2026-10-28 Loki incident for the command). Read the release notes of the version `latest` just pulled.
- **Port:** write listen addresses as `:<port>`; pick a host port that `ss -tlnp` shows free.

Then `sudo docker compose up -d` and watch `sudo docker compose logs -f <service>` until it settles.

**Prevention:** create config files and data folders (with the right owner) before the first `up`.

## Verify

`sudo docker compose ps` shows the container "Up" for more than a minute (or "healthy"), and whatever depends on it connects (for example, Grafana's data source "Save & test" passes).

## Related incidents

- [2026-08-22: Grafana's port already in use, then a crash loop](../incidents/2026-08-22-grafana-port-in-use-then-crash-loop.md)
- [2026-08-29: Loki's config file mounted as a directory](../incidents/2026-08-29-loki-config-mounted-as-directory.md)
- [2026-08-29: Loki crash-looped on its compactor config](../incidents/2026-08-29-loki-crash-loop-compactor-config.md)
- [2026-08-30: ntfy `auth-users` type mismatch](../incidents/2026-08-30-ntfy-auth-users-type-mismatch.md)
- [2026-08-30: ntfy listen address missing its colon](../incidents/2026-08-30-ntfy-listen-address-missing-colon.md)
