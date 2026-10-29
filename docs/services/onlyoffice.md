# ONLYOFFICE Document Server

```
Status:     retired (→ Euro-Office 2026-08-24)
Host:       homelab
Config:     ~/docker/onlyoffice/ (left in place)
Nextcloud:  `onlyoffice` connector app still installed
Port:       9917→80, Funnel :8443 (both now used by Euro-Office)
```

## Why retired

Editing documents in the ONLYOFFICE mobile app is behind a paywall (2026-08-15). Everything else worked.

## What replaced it

[Euro-Office](euro-office.md), a fork of ONLYOFFICE's open-source code, on the same port and with the same connector concepts. Mobile editing now goes through the Nextcloud app.

## Leftovers

Kept on purpose, with no clean-up planned: the `~/docker/onlyoffice/` folder and the `onlyoffice` Nextcloud app. To remove the app later: `sudo docker exec -u www-data nextcloud_app php occ app:disable onlyoffice`.

## Lessons (they all apply to Euro-Office)

These are from the setup, 2026-08-14 to 08-15:
- **The connector has fields for the internal and public addresses** (under advanced settings). "Error while downloading the document file to be converted" means they're empty or wrong.
- **It blocks private IP addresses by default.** The fix was `ALLOW_PRIVATE_IP_ADDRESS=true`.
- **`- KEY= value` in compose puts a leading space in the value.** The JWT secret differed by one leading space, and Nextcloud logged "Download empty without jwt". Write `- KEY=value`, then `down` and `up`.
- **A 403 from Nextcloud on the document fetch means a JWT mismatch; a 400 means `trusted_domains`.**
- **uBlock Origin blocked the editor from loading.** Test in a browser without an ad blocker before digging into servers.
