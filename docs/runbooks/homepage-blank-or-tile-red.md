# Homepage is blank, or a tile is red

## Symptom

- The page is blank, or says "Host validation failed".
- A tile shows a red dot or "500" although the service works in the browser.

## Check

```bash
sudo docker logs homepage-homepage-a-1 --tail 30 2>&1      # or -b-1; YAML parse errors show here
sudo docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' homepage-homepage-a-1 | grep -E '^(PORT|HOMEPAGE_ALLOWED_HOSTS)='
grep -n -B1 -A3 '<service>' ~/docker/homepage/config_a/services.yaml
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:<port>/<path>   # what the status dot sees (host network)
grep -n -P '\t' ~/docker/homepage/config_*/services.yaml    # tabs are not allowed
```

## Likely causes

1. **"Host validation failed":** the address in the browser isn't in `HOMEPAGE_ALLOWED_HOSTS`, for example after a hostname change.
2. **Blank page:** a YAML error in `services.yaml`, such as fields indented at the same level as the service name, or a tab.
3. **Red tile or 500:** the `siteMonitor` URL returns an error even though the app works. Some front pages do; use the app's health endpoint (Nextcloud: `/status.php`).
4. **The instance isn't running**, or its port clashes with another host-network service.

## Fix

- Cause 1: add the hostname to `HOMEPAGE_ALLOWED_HOSTS` in `.env`, then `sudo docker compose up -d`.
- Cause 2: fix the indentation: groups at column 0, services 4 spaces, fields 8 spaces. Refresh the page.
- Cause 3: point `siteMonitor` at a health URL. Refresh.
- Cause 4: `sudo docker compose up -d`, and check the port.

## Related incidents

- [2026-10-22: Homepage couldn't bind port 3000](../incidents/2026-10-22-homepage-port-3000-in-use.md)
- [2026-10-22: blank page from a YAML indentation error](../incidents/2026-10-22-homepage-blank-yaml-indentation.md)
- [2026-10-22: Nextcloud tile showed 500](../incidents/2026-10-22-homepage-nextcloud-tile-500.md)
