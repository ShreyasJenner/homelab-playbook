# Document editing broke after the host's LAN address changed

Nextcloud and Euro-Office call each other on homelab's LAN address, because a container can't reliably reach its own host's Funnel URL. The router doesn't reserve that address, so it can change on a DHCP renewal or a network move, and document editing then breaks.

## Symptom

- Documents don't open from Nextcloud, or the Euro-Office settings page hangs while saving and then errors (`cURL error 28` to the old address).
- Everything else in Nextcloud works.
- Happens after a router change, a move, or a reboot that picked up a new address.

## Check

```bash
ip -4 addr show wlp130s0 | grep inet                     # the current LAN address
sudo docker exec -u www-data nextcloud_app php occ config:app:get eurooffice DocumentServerInternalUrl
sudo docker exec -u www-data nextcloud_app php occ config:app:get eurooffice StorageUrl
sudo docker exec -u www-data nextcloud_app php occ config:system:get trusted_domains
```

To see all the connector's settings: `occ config:list eurooffice | grep -v -i secret` (the filter keeps the JWT secret out of the output).

## Likely cause

The two internal addresses and the `trusted_domains` entry still hold the old IP.

## Fix

With `<NEW_IP>` as the current address:

```bash
sudo docker exec -u www-data nextcloud_app php occ config:app:set eurooffice DocumentServerInternalUrl --value="http://<NEW_IP>:9917/"
sudo docker exec -u www-data nextcloud_app php occ config:app:set eurooffice StorageUrl --value="http://<NEW_IP>:8080/"
sudo docker exec -u www-data nextcloud_app php occ config:system:get trusted_domains   # find the old IP's index
sudo docker exec -u www-data nextcloud_app php occ config:system:set trusted_domains <index> --value=<NEW_IP>
cd ~/docker/nextcloud && sudo docker compose restart
cd ~/docker/euro-office && sudo docker compose restart
```

The same fields can be changed in Admin settings → Nextcloud Office.

**Prevention:** reserve the address for homelab in the router (follow-up 1 in the plan). That removes the cause.

## Verify

```bash
curl -s http://<NEW_IP>:9917/healthcheck; echo     # true
curl -s http://<NEW_IP>:8080/status.php; echo      # JSON with "installed":true
bash docs/runbooks/euro-office-check.sh            # VERDICT=GREEN
```

## Related incidents

- [2026-09-12: document editing broke after the LAN address changed](../incidents/2026-09-12-document-editing-broke-after-lan-ip-change.md)
