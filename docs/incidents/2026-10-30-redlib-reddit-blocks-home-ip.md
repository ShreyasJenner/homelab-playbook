# Redlib: Reddit refuses the home IP

- **Date:** 2026-10-30
- **Status:** open (waiting for Reddit to lift the block)
- **Service:** Redlib (both instances)
- **Runbook:** [Redlib is broken or won't update](../runbooks/redlib-broken-or-wont-update.md)

## Symptom

Every page on https://rla.example.com failed with "Failed to parse page JSON data: expected value at line 1 column 1 | /r/…/hot.json?&raw_json=1", served as HTTP 404. The log showed "Got an invalid response from reddit … Status code: 403 Forbidden" on every request, not only at startup. No configuration had changed since it last worked.

A public instance (redlib-1.privadency.com, v0.40.0) worked at the same time (user).

The second message on the error page, "Error checking update status: TypeError: … getElementById(...) is null", is the page's update-check script finding no element on an error page. It's noise.

## Cause

Reddit refuses Redlib's requests from the home IP. Ruled out, in order:

1. **A stale build.** The image was the polak14 fork (v0.36.0), built 2026-10-22. Upstream `redlib-org/redlib` had released v0.40.0 the same day ("fix #562!"), so the build context was moved back to upstream and rebuilt. v0.40.0 got the same 403s.
2. **Something about the server.** The published `quay.io/redlib/redlib:latest` (v0.40.0, the same commit), run untouched on the laptop on home Wi-Fi, got the same 403s. The only thing it shares with the server is the home network.
3. **A container on an old image.** Both containers ran the current `redlib-local:latest`.

Not the cause: the startup "Rate limit check failed" 403, which also happened on 2026-10-28 while browsing worked.

Plain `curl` to `www.reddit.com/…/hot.json` got "blocked by network security" from home, so it can't tell a blocked IP from a working one; Redlib uses Reddit's OAuth API instead.

Why Reddit blocked the address isn't known. The home connection has been with the current ISP since the 2026-09-10 network move; the "behind CGNAT" notes elsewhere in the Playbook may describe the old network (follow-up 34). The containers had restarted about 8 hours before the check, without a host reboot (up since 2026-10-11); why is also unknown.

## Fix

Not fixed yet. Waiting for Reddit to lift the block, using a public instance meanwhile. A router restart wasn't tried: the ISP usually hands back the same public IP, and `198.51.100.10` isn't reserved in the router yet (follow-up 1).

Done along the way, and kept:
- `~/docker/redlib/docker-compose.yml`: `build: context:` changed from `https://github.com/polak14/redlib.git#main` to `https://github.com/redlib-org/redlib.git#main`, then `build --no-cache` and `up -d --force-recreate`. Both instances run v0.40.0. Backup: `docker-compose.yml.bak-20261030`.

To check whether the block has lifted: `curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8943/r/selfhosted` on the server returns `200`. A `sudo docker compose restart` first gets a fresh token.
