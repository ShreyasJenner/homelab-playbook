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

Also check a public Redlib instance: if it fails there too, Reddit is blocking Redlib in general and only an upstream fix will help. Note its version (page footer).

If the public instance works on the same version as ours, run the published image on another machine at home (a laptop on home Wi-Fi). Avoid `path` as a loop variable: in zsh it overwrites `PATH`.

```bash
docker run -d --rm --name redlib-test -p 127.0.0.1:8295:8080 quay.io/redlib/redlib:latest
sleep 8
curl -s -w '\nHTTP %{http_code}\n' http://127.0.0.1:8295/r/selfhosted | grep -o -E '<h1>[^<]*</h1>|HTTP [0-9]+|class="post"' | sort | uniq -c
docker stop redlib-test
```

A 404 with "Failed to parse page JSON data" there means the home IP is blocked, not the server. A plain `curl` to `reddit.com/…/hot.json` doesn't tell you: Reddit blocks plain `curl` either way.

## Likely causes

1. **Reddit changed something or rejects the instance's token**, which needs a newer Redlib build.
2. **Reddit refuses the home IP.** Every request gets a 403, on any version, from any machine at home, while public instances work.
3. **`docker compose pull` was run** on an image that only exists locally.
4. The `build:` section or `pull_policy` was lost from the compose file.

## Fix

```bash
cd ~/docker/redlib
sudo docker compose build --no-cache
sudo docker compose up -d --force-recreate
sudo docker compose logs --tail 20 2>&1 | grep -i -E 'oauth|error'
```

A plain restart sometimes clears a temporary token error; try it first.

If the build context is wrong, the first instance needs `pull_policy: build` with `build: context: https://github.com/redlib-org/redlib.git#main`, and the second `pull_policy: never`.

If the home IP is blocked (cause 2), no build fixes it. Wait, and use a public instance meanwhile. A router restart rarely changes the ISP's address; if you try it, reserve the server's LAN address first (follow-up 1).

**"Unhealthy" in `docker ps` doesn't mean broken:** the healthcheck uses `wget`, which the image doesn't have.

## Verify

The log shows "Running Redlib … on [::]:8080" without OAuth or 403 errors, and https://rla.example.com loads a subreddit.

## Related incidents

- [2026-09-24: OAuth client error with the published image](../incidents/2026-09-24-redlib-oauth-client-error.md)
- [2026-10-30: Reddit refuses the home IP](../incidents/2026-10-30-redlib-reddit-blocks-home-ip.md)
