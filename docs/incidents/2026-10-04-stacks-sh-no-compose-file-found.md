# `stacks.sh` found no compose files

- **Date:** 2026-10-04
- **Status:** resolved
- **Service:** `stacks.sh` (the update script)
- **Runbook:** [Updating containers](../runbooks/updating-containers.md)
- **Source:** chat "Docker compose wrapper script" (2026-10-04). Unverified; the fixed check is in the live script (2026-10-28).

## Symptom

Every stack failed with `!! <stack>: no compose file found`.

## Cause

The first version checked for a compose file with one `ls` over four filename patterns. `ls` exits with an error if any one of them doesn't exist, so every stack failed the check.

## Fix

Check each filename with its own `[[ -f … ]]` test. That's how the live script does it.
