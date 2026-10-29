# Collabora Online

```
Status:     retired (→ ONLYOFFICE 2026-08-14, then Euro-Office 2026-08-24)
Host:       homelab
Config:     ~/docker/collabora/ (left in place)
Nextcloud:  `richdocuments` connector and `richdocumentscode` (built-in CODE server) still installed
```

## Why retired

Every configuration problem got fixed, but the rendering process still died on every document open. The editor loaded showing "Viewing" with a blank page, and the logs had `Child … was killed, with status 9`. It wasn't out of memory: about 737 MiB of 15 GiB were in use, and dmesg was clean. A retest on 2026-08-15 with `seccomp=unconfined` and `apparmor=unconfined` changed nothing.

The built-in CODE server (`richdocumentscode`) was tried too and dropped on 2026-08-08. Its connection check always calls Nextcloud's own public URL, which times out over Funnel. It came back enabled on 2026-08-14 and timed out again.

## What replaced it

[ONLYOFFICE](onlyoffice.md) on 2026-08-14, then [Euro-Office](euro-office.md) on 2026-08-24.

## Leftovers

Kept on purpose, with no clean-up planned:
- the `~/docker/collabora/` folder
- the `richdocuments` and `richdocumentscode` apps in Nextcloud. `richdocumentscode` is enabled. Neither was involved in any later incident.
- `richdocuments`' `wopi_url` and `wopi_callback_url`, which still hold the old LAN address `203.0.113.10`

To clean up later:

```bash
sudo docker exec -u www-data nextcloud_app php occ app:disable richdocumentscode
sudo docker exec -u www-data nextcloud_app php occ app:disable richdocuments
```

## If it's ever tried again

- **Keep separate internal and public WOPI URLs, and set them with `occ`.** `wopi_url` is `http://<LAN_IP>:9980`; `public_wopi_url` is the Funnel URL. The admin UI's "Use your own server" field overwrites `public_wopi_url` when you save.
- **Give it its own Funnel port.** A path such as `/collabora` breaks the internal discovery call.
- **Set `server_name`** (`--o:server_name=<host>:<port>`), or Collabora sends the browser its internal LAN address. The ground truth is `curl http://<LAN_IP>:9980/hosting/discovery | grep urlsrc`.
- **Index every `storage.wopi.host` entry** (`[0]`, `[1]`). An entry without an index is silently ignored.
- **Never run `occ richdocuments:activate-config` after setting `wopi_callback_url`.** It resets the callback to autodetect.
- **Put the LAN address in Nextcloud's `trusted_domains`**, or CheckFileInfo returns 400.
- **It needs `cap_add: [MKNOD, SYS_ADMIN]`.** `mount_jail_tree=false` never took effect.
- `docker inspect … .Config.Env` prints the admin password. Never paste its output anywhere.
- The kit crash was never explained. Untried ideas: pin an older or newer `collabora/code` tag, look at kernel or seccomp, turn on trace-level logging.
