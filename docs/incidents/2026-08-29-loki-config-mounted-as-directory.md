# Loki's config file mounted as a directory

- **Date:** 2026-08-29
- **Status:** resolved
- **Service:** Loki (monitoring stack)
- **Runbook:** [A new container won't start or crash-loops](../runbooks/new-container-crash-loops.md)
- **Source:** chat "Resume improvement phase 2 next steps" (2026-08-09; messages from 2026-08-29). Unverified.

## Symptom

`docker compose up` failed: `error mounting "/home/alice/docker/monitoring/loki/loki-config.yml" … not a directory`.

## Cause

`loki-config.yml` didn't exist at the first `up`. When a bind-mount source is missing, Docker creates it as an empty **directory**, which then can't be mounted onto a file inside the container.

## Fix

Remove the directory, create the real `loki-config.yml`, and `docker compose up -d`.
