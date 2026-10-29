# Loki crash-looped on its compactor config

- **Date:** 2026-08-29
- **Status:** resolved
- **Service:** Loki (monitoring stack); seen in Grafana
- **Runbook:** [A new container won't start or crash-loops](../runbooks/new-container-crash-loops.md); also [A Grafana panel or Explore query shows no data](../runbooks/grafana-panel-shows-no-data.md)
- **Source:** chat "Resume improvement phase 2 next steps" (2026-08-09; messages from 2026-08-29). Unverified; the end state was verified on 2026-10-28.

## Symptom

Grafana: "Unable to connect with Loki". Loki was crash-looping, first on an invalid compactor config, then on `mkdir /var/loki: permission denied`.

## Cause

1. Loki 3.x requires `compactor.delete_request_store` when `retention_enabled` is on.
2. `compactor.working_directory` was set to `/var/loki/compactor`, outside the mounted `/loki` volume, where Loki's user (uid 10001) can't write.

## Fix

`delete_request_store: filesystem`, and the working directory moved under `/loki`. The user got Loki running without recording the final file, and at the time some paths were thought to still point at `/tmp/loki`.

Verified 2026-10-28: no `/tmp` paths; `path_prefix /loki`, compactor in `/loki/compactor`, `delete_request_store: filesystem`. **The `retention_period: 720h` from this session never took effect,** though: the live value was `0s` (keep forever) until the [2026-10-28 fix](2026-10-28-loki-debug-logging-filled-disk.md).
