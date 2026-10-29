# Donetick

```
Status:     retired 2026-08-18 (→ Mindwtr)
Host:       homelab
Config:     ~/docker/donetick/ (left in place)
```

## Why retired

Another task-manager experiment that didn't fit: "the UI isn't very good". Its mobile app also needed a public HTTPS address (Funnel), against the tailnet-only rule.

## What replaced it

[Mindwtr](mindwtr.md). Donetick's old Funnel port `:10000` now belongs to Nextcloud.

## Leftovers

The `~/docker/donetick/` folder (its compose warns that `DOCKER_PATH` isn't set). The usage examples in `stacks.sh` still mention it.
