#!/usr/bin/env bash
# Loki / Docker log storage check: reproduces "Loki's storage grows without limit".
# Read-only. Prints no secrets: no .env files, no container environment.
# Written for docs/incidents/2026-10-28-loki-debug-logging-filled-disk.md.
# Run on homelab as your normal user (docker and du go through sudo):
#   bash loki-storage-check.sh
#
# Overrides (env):
#   MON_DIR     monitoring stack dir            (default: ~/docker/monitoring)
#   LOKI_URL    Loki HTTP address on the host   (default: http://localhost:3517)
#   MAX_TABLES  most daily index tables allowed (default: 9 = 7-day retention + today + 1 pending delete)
#   MAX_LOG_KIB Loki's own log growth, KiB/min  (default: 100; it was 1129 at debug level)

set -uo pipefail

MON=${MON_DIR:-$HOME/docker/monitoring}
LOKI=${LOKI_URL:-http://localhost:3517}
MAX_TABLES=${MAX_TABLES:-9}
MAX_LOG_KIB=${MAX_LOG_KIB:-100}

RESULTS=()
FAILED=0
check() { # check NAME PASS|FAIL DETAIL
  RESULTS+=("$1=$2 ${3:-}")
  [[ $2 == FAIL ]] && FAILED=1
  return 0
}

sudo -v || exit 1

printf '=== Disk ===\n'
df -h /
sudo du -sh /var/lib/docker/containers "$MON/loki/data" "$MON/loki/data/chunks" "$MON/prometheus/data" 2>/dev/null

# 1. Docker daemon default log rotation.
if sudo grep -q '"max-size"' /etc/docker/daemon.json 2>/dev/null; then
  check daemon_log_opts PASS "$(sudo tr -d ' \n' </etc/docker/daemon.json)"
else
  check daemon_log_opts FAIL "/etc/docker/daemon.json missing or has no max-size"
fi

# 2. Containers still without a log size limit (created before daemon.json, not recreated since).
UNCAPPED=$(sudo docker ps -aq | xargs -r sudo docker inspect --format '{{.Name}} {{json .HostConfig.LogConfig.Config}}' | awk '$2=="{}"{print $1}' | tr '\n' ' ')
RESULTS+=("uncapped_containers=${UNCAPPED:-none}")

# 3. Biggest container log files.
printf '\n=== Largest container logs ===\n'
sudo sh -c 'ls -s --block-size=M /var/lib/docker/containers/*/*-json.log*' | sort -rn | head -5

# 4. Loki's own log: capped, and quiet.
LOG=$(sudo docker inspect --format '{{.LogPath}}' loki)
CFG=$(sudo docker inspect --format '{{json .HostConfig.LogConfig.Config}}' loki)
[[ $CFG == *max-size* ]] && check loki_log_capped PASS "$CFG" || check loki_log_capped FAIL "$CFG"
S1=$(sudo stat -c %s "$LOG"); sleep 60; S2=$(sudo stat -c %s "$LOG")
KIB=$(( (S2 - S1) / 1024 ))
(( KIB <= MAX_LOG_KIB )) && check loki_log_growth PASS "${KIB} KiB/min" || check loki_log_growth FAIL "${KIB} KiB/min"

# 5. Loki effective config.
CONF=$(curl -s "$LOKI/config")
LEVEL=$(awk '/^server:/{s=1;next} /^[^ ]/{s=0} s&&/^  log_level:/{print $2;exit}' <<<"$CONF")
[[ $LEVEL != debug ]] && check loki_log_level PASS "$LEVEL" || check loki_log_level FAIL "$LEVEL"
RET=$(awk '/^limits_config:/{s=1;next} /^[^ ]/{s=0} s&&/^  retention_period:/{print $2;exit}' <<<"$CONF")
[[ -n $RET && $RET != 0s ]] && check loki_retention_period PASS "$RET" || check loki_retention_period FAIL "${RET:-<none>}"

# 6. Retention actually deletes: count daily index tables.
TABLES=$(sudo ls "$MON/loki/data/chunks/index" | grep -c '^index_')
(( TABLES <= MAX_TABLES )) && check loki_index_tables PASS "$TABLES" || check loki_index_tables FAIL "$TABLES (max $MAX_TABLES)"
printf '\n=== Compactor ===\n'
curl -s "$LOKI/metrics" | grep -E '^loki_compactor_' | grep -vE 'missing_chunks|locked_table|grpc_'

# 7. Loki ready.
READY=$(curl -s "$LOKI/ready")
[[ $READY == ready ]] && check loki_ready PASS || check loki_ready FAIL "$READY"

# 8. Alloy pushes Loki rejected in the last 24 h (non-zero right after 02:30 is a known replay; see the incident).
DROPS=$(sudo docker logs alloy --since 24h 2>&1 | grep -c 'no retries left')
RESULTS+=("alloy_dropped_batches_24h=$DROPS")

# 9. Restic skips logs and metrics.
for d in loki prometheus; do
  sudo test -e "$MON/$d/data/.nobackup" && check "${d}_nobackup" PASS || check "${d}_nobackup" FAIL "no $MON/$d/data/.nobackup"
done

printf '\n--- Captured ---\n'
printf '%s\n' "${RESULTS[@]}"
if (( FAILED )); then printf 'VERDICT=RED\n'; exit 1; else printf 'VERDICT=GREEN\n'; fi
