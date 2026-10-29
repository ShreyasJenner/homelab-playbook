# A compose or `.env` change didn't take effect

## Symptom

You changed a volume, port, environment variable or network in `docker-compose.yml` or `.env`, and the container still behaves as before: a new folder isn't visible, a new setting is ignored, files go to the old path.

## Check

What the running container actually has:

```bash
sudo docker inspect --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} rw={{.RW}}{{"\n"}}{{end}}' <container>
sudo docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' <container> | grep -E '^<VAR>='   # never dump the whole env: it has secrets
sudo docker inspect -f '{{.Created}}' <container>                                                  # older than your edit?
cd ~/docker/<stack> && sudo docker compose config --quiet   # prints warnings such as unset variables
```

## Likely causes

1. **`docker compose restart` was used.** Restart reuses the existing container, so compose and `.env` changes are ignored.
2. **The variable is unset** (a typo in `.env`, or the wrong `.env` folder), and compose silently substitutes an empty string.
3. **A value has a leading space**: `- KEY= value` in compose makes the space part of the value.
4. **Postgres** reads `POSTGRES_*` only when it first initialises its data. Later changes do nothing.

## Fix

```bash
cd ~/docker/<stack>
sudo docker compose up -d          # recreates any container whose config changed
```

For causes 2 and 3, fix the file and run `up -d` again. For cause 4, change the user or password inside Postgres, or recreate the volume (which loses the data).

## Verify

Repeat the `inspect` checks: the mount, variable and creation time should all match the edit.

## Related incidents

- [2026-09-23: Invidious database login failed](../incidents/2026-09-23-invidious-database-login-failed.md)
