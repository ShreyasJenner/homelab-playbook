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
5. **The app saved the setting in its own config file**, which now wins over the env var: Gitea's `app.ini` and Vaultwarden's admin-panel `data/config.json`. Changing or removing the env var doesn't change anything.
6. **A YAML anchor merge (`<<:`) is shallow:** a service's own `environment:` replaces the anchor's instead of adding to it.

## Fix

```bash
cd ~/docker/<stack>
sudo docker compose up -d          # recreates any container whose config changed
```

For causes 2 and 3, fix the file and run `up -d` again. For cause 4, change the user or password inside Postgres, or recreate the volume (which loses the data). For cause 5, edit the app's own config file and restart. For cause 6, merge the shared anchor inside `environment:` (as Homepage's compose does).

To check what compose will substitute without printing secrets, use `sudo docker compose config --quiet`: it prints only warnings such as "variable is not set". Never paste the full `docker compose config` output: it includes every secret.

## Verify

Repeat the `inspect` checks: the mount, variable and creation time should all match the edit.

## Related incidents

- [2026-09-23: Invidious database login failed](../incidents/2026-09-23-invidious-database-login-failed.md)
