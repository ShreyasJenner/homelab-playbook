# An Uptime Kuma alert is wrong or didn't arrive

Two problems with one alert path: [Uptime Kuma](../services/uptime-kuma.md) → "Kuma Alert" → [ntfy](../services/ntfy.md) → ntfy.sh → the iPhone app. Only the first has actually happened (once); the second is written down because the whole path depends on it.

## A. Kuma says DOWN, but the service works

### Check

Kuma is on the host network, so the same URL from the host shows what Kuma sees:

```bash
curl -si http://localhost:<port><path> | head -5      # the monitor's exact URL
```

In the Kuma UI, open the monitor: the URL, the accepted status codes, and the error message of the last failed beat.

### Likely causes

1. **The URL hits a redirect or login page.** `/` often returns 302 (Nextcloud does). Monitor the health endpoint instead (the table is on the Uptime Kuma page).
2. **The app rejects the host name.** Nextcloud answers `status.php` with a trusted-domain error for names not in `trusted_domains`, such as `host.docker.internal`. Use `localhost`.
3. **The URL is stale.** A port changed, or the URL is an old Serve address (`homelab.tail0000.ts.net:<port>`); those were retired on 2026-10-21.
4. **Kuma isn't on the host network** any more (someone changed the compose), so `localhost` is its own container. Check with `sudo docker inspect -f '{{.HostConfig.NetworkMode}}' uptime-kuma`: it must say `host`.

### Fix

Edit the monitor's URL or accepted codes in the UI, then save. Its next beat should be green.

## B. Something went down and no alert reached the phone

### Check, in order

1. **Is the monitor attached to the alert?** Monitor → Edit → Notifications: "Kuma Alert" must be ticked. It isn't the default, so new monitors start without it.
2. **Does Kuma reach ntfy?** Settings → Notifications → "Kuma Alert" → **Test**. If it errors, ntfy is down or Kuma's stored credentials are wrong.
3. **Is ntfy up?**
   ```bash
   curl -s http://localhost:10230/v1/health; echo           # {"healthy":true}
   sudo docker logs ntfy --since 1h 2>&1 | tail -20
   ```
4. **Did the message reach ntfy?** (the cache keeps 12 h; prints topics and counts, not message text)
   ```bash
   sudo sqlite3 -readonly ~/docker/ntfy/cache/cache.db \
     "select topic, count(*), datetime(max(time),'unixepoch') from messages group by topic;"
   ```
5. **Is the phone on the tailnet?** With Tailscale off, nothing arrives. That's by design (ADR 0004).
6. **iOS push settings:** `NTFY_UPSTREAM_BASE_URL=https://ntfy.sh` is required for instant delivery, and `NTFY_BASE_URL` must be `https://ntfyhub.example.com`:
   ```bash
   sudo docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' ntfy | grep -E '^NTFY_(BASE_URL|UPSTREAM_BASE_URL)='
   ```
7. **Was it 02:30–02:34?** The nightly backup stops Kuma and ntfy, so nothing is checked or sent then.

### Fix

Tick the notification, fix the ntfy credentials in Kuma (re-enter them in the "Kuma Alert" settings), or start ntfy (`cd ~/docker/ntfy && sudo docker compose up -d`). In the iOS app, check that the server URL is `https://ntfyhub.example.com` and that notifications are allowed for the ntfy app.

## Verify

Kuma's **Test** button produces a notification on the phone within a few seconds, with Tailscale on.

## Related incidents

- [2026-08-19: Nextcloud monitor down although Nextcloud worked](../incidents/2026-08-19-uptime-kuma-nextcloud-false-down.md)
