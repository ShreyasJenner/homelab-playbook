# HDD not mounted after the automount test

- **Date:** 2026-10-11
- **Status:** resolved (automount dropped)
- **Service:** the 4 TB HDD, and everything on it
- **Runbook:** [Media libraries are empty, or nothing runs, after a reboot](../runbooks/media-libraries-empty-after-reboot.md)
- **Source:** chat "Media server file discovery issue" (2026-10-02, later messages). Unverified; end state verified 2026-10-28.

## Symptom

After a reboot to test `x-systemd.automount`, the HDD wasn't mounted.

## Cause

Not established. Claude's reply used the wrong unit name (`home-alice-media.automount`), and the chat ended there.

## Fix

Automount was dropped. On 2026-10-28 the fstab line has `nofail,x-systemd.device-timeout=5min` and no `x-systemd.automount`, and `docker.service` waits for the mount.
