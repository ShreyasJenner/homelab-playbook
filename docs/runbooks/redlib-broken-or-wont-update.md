# Redlib is broken or won't update

## Symptom

- Pages fail with "Failed to create OAuth client: expected value at line 1 column 1", "Failed to parse page JSON data", or Reddit 403 errors in the log.
- An update fails with "pull access denied for redlib-local".

## Check

```bash
cd ~/docker/redlib
sudo docker compose logs --tail 30 2>&1 | grep -i -E 'oauth|error|403|running redlib'
grep -n -E 'image:|build:|context|pull_policy' docker-compose.yml
```

Also check a public Redlib instance: if it fails there too, Reddit is blocking Redlib in general and only an upstream fix will help.

## Likely causes

1. **Reddit changed something or rejects the instance's token**, which needs a newer Redlib build.
2. **`docker compose pull` was run** on an image that only exists locally.
3. The `build:` section or `pull_policy` was lost from the compose file.

## Fix

```bash
cd ~/docker/redlib
sudo docker compose build --no-cache
sudo docker compose up -d --force-recreate
sudo docker compose logs --tail 20 2>&1 | grep -i -E 'oauth|error'
```

A plain restart sometimes clears a temporary token error; try it first.

If the build context is wrong, the first instance needs `pull_policy: build` with `build: context: https://github.com/polak14/redlib.git#main`, and the second `pull_policy: never`.

**"Unhealthy" in `docker ps` doesn't mean broken:** the healthcheck uses `wget`, which the image doesn't have.

## Verify

The log shows "Running Redlib … on [::]:8080" without OAuth or 403 errors, and https://rla.example.com loads a subreddit.

## Related incidents

- [2026-09-24: OAuth client error with the published image](../incidents/2026-09-24-redlib-oauth-client-error.md)
