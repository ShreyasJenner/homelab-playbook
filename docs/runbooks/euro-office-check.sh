#!/usr/bin/env bash
# Euro-Office health check: reproduces "Nextcloud Office cannot be reached".
# Read-only. Prints no secrets: JWT values are compared, never shown.
# Written for docs/incidents/2026-10-28-euro-office-broken-after-funnel-switch.md.
# Run on homelab as your normal user (docker and tailscale go through sudo):
#   bash euro-office-check.sh
#
# Overrides (env):
#   NC_CONTAINER  Nextcloud app container   (default: nextcloud_app or nextcloud-app)
#   EO_CONTAINER  Euro-Office container     (default: first container matching euro|office)
#   NC_APP        connector app id in Nextcloud (default: auto-detect)
#   SKIP_HITL=1   skip the browser steps (automated checks only)

set -uo pipefail

step() {
  printf '\n>>> %s\n' "$1"
  read -r -p "    [Enter when done] " _
}

capture() {
  local var="$1" question="$2" answer
  printf '\n>>> %s\n' "$question"
  read -r -p "    > " answer
  printf -v "$var" '%s' "$answer"
}

RESULTS=()
FAILED=0
check() { # check NAME PASS|FAIL DETAIL
  RESULTS+=("$1=$2 ${3:-}")
  [[ $2 == FAIL ]] && FAILED=1
  return 0
}

sudo -v || exit 1

NC=${NC_CONTAINER:-$(sudo docker ps --format '{{.Names}}' | grep -iE '^nextcloud[-_]?app$' | head -n1)}
EO=${EO_CONTAINER:-$(sudo docker ps --format '{{.Names}}' | grep -iE 'euro|office' | head -n1)}
# config:app:get exits 1 for an unset key, so only stdout is kept; reachability is checked once below.
occ() { sudo docker exec -u www-data "$NC" php occ "$@" 2>/dev/null; }
if ! sudo docker exec -u www-data "$NC" php occ status >/dev/null; then
  printf 'occ does not work in container "%s"; set NC_CONTAINER.\n' "$NC"; exit 2
fi

printf '=== Containers ===\n'
sudo docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -iE "nextcloud|euro|office" || true
printf 'NC=%s  EO=%s\n' "$NC" "${EO:-<none found>}"

printf '\n=== Tailscale serve/funnel ===\n'
sudo tailscale funnel status 2>&1 || true

printf '\n=== Nextcloud document connector apps (enabled) ===\n'
ENABLED=$(occ app:list | awk '/^Enabled:/{e=1;next} /^Disabled:/{e=0} e' | grep -iE 'office|richdocuments|euro' || true)
printf '%s\n' "${ENABLED:-<none>}"
APP=${NC_APP:-$(printf '%s\n' "$ENABLED" | sed -E 's/^ *- *([^:]+):.*/\1/' | grep -iE 'euro|onlyoffice' | head -n1)}
printf 'Connector app used for checks: %s\n' "${APP:-<none>}"

printf '\n=== Connector config (%s) ===\n' "$APP"
DS_URL=$(occ config:app:get "$APP" DocumentServerUrl)
DS_INT=$(occ config:app:get "$APP" DocumentServerInternalUrl)
STORAGE=$(occ config:app:get "$APP" StorageUrl)
printf 'DocumentServerUrl (browser)        = %s\n' "${DS_URL:-<empty>}"
printf 'DocumentServerInternalUrl (NC->EO) = %s\n' "${DS_INT:-<empty>}"
printf 'StorageUrl (EO->NC)                = %s\n' "${STORAGE:-<empty>}"

printf '\n=== Nextcloud system config ===\n'
printf 'overwrite.cli.url = %s\n' "$(occ config:system:get overwrite.cli.url)"
printf 'overwriteprotocol = %s\n' "$(occ config:system:get overwriteprotocol)"
printf 'trusted_domains:\n%s\n' "$(occ config:system:get trusted_domains)"

printf '\n=== Euro-Office container env (non-secret) ===\n'
if [[ -n ${EO:-} ]]; then
  sudo docker exec "$EO" printenv | grep -E '^(JWT_ENABLED|JWT_HEADER|ALLOW_PRIVATE_IP_ADDRESS|ALLOW_META_IP_ADDRESS)=' || true
fi

# --- automated checks ---------------------------------------------------

# 0. Backend: the container serves api.js on its published port.
EO_PORT=$(sudo docker port "$EO" 80/tcp 2>/dev/null | head -n1 | sed 's/.*://')
code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "http://localhost:${EO_PORT}/web-apps/apps/api/documents/api.js" 2>&1)
[[ $code == 200 ]] && check api_js_backend PASS "localhost:$EO_PORT $code" || check api_js_backend FAIL "localhost:$EO_PORT $code"

# 0b. Exposure: DocumentServerUrl's port must be Funnel-on (ADR 0004) and proxy to the backend port.
DS_PORT=$(sed -E 's#^https?://[^:/]+:?([0-9]*).*#\1#' <<<"$DS_URL"); DS_PORT=${DS_PORT:-443}
SERVE=$(sudo tailscale funnel status 2>&1)
grep -qE ":${DS_PORT} \(Funnel on\)" <<<"$SERVE" && check ds_port_funnel_on PASS ":$DS_PORT" || check ds_port_funnel_on FAIL ":$DS_PORT not Funnel on"
target=$(awk -v p=":${DS_PORT} " 'index($0,p){f=1;next} f&&/proxy/{print $NF;exit}' <<<"$SERVE")
[[ $target == "http://localhost:${EO_PORT}" || $target == "http://127.0.0.1:${EO_PORT}" ]] \
  && check ds_port_proxy_target PASS "$target" || check ds_port_proxy_target FAIL "${target:-<none>}"

# 1. Browser path: the editor page loads api.js from DocumentServerUrl.
if [[ -n $DS_URL ]]; then
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "${DS_URL%/}/web-apps/apps/api/documents/api.js" 2>&1)
  [[ $code == 200 ]] && check api_js_from_host PASS "$code" || check api_js_from_host FAIL "$code"
else
  check api_js_from_host FAIL "DocumentServerUrl empty"
fi

# 2. Nextcloud -> Euro-Office (internal address, or the public one if unset).
NC_TO_EO=${DS_INT:-$DS_URL}
if [[ -n $NC_TO_EO ]]; then
  out=$(sudo docker exec "$NC" curl -sS --max-time 10 "${NC_TO_EO%/}/healthcheck" 2>&1 \
     || sudo docker exec "$NC" php -r 'echo @file_get_contents($argv[1]) ?: "unreachable";' "${NC_TO_EO%/}/healthcheck" 2>&1)
  [[ $out == true ]] && check nc_to_eo PASS || check nc_to_eo FAIL "$out"
fi

# 3. Euro-Office -> Nextcloud (StorageUrl, or overwrite.cli.url if unset).
EO_TO_NC=${STORAGE:-$(occ config:system:get overwrite.cli.url)}
if [[ -n ${EO:-} && -n $EO_TO_NC ]]; then
  out=$(sudo docker exec "$EO" curl -sS --max-time 10 "${EO_TO_NC%/}/status.php" 2>&1)
  [[ $out == *'"installed":true'* ]] && check eo_to_nc PASS || check eo_to_nc FAIL "$(head -c 200 <<<"$out")"
fi

# 4. JWT secrets match (compared in-process, never printed).
if [[ -n ${EO:-} ]]; then
  nc_secret=$(occ config:app:get "$APP" jwt_secret)
  eo_secret=$(sudo docker exec "$EO" printenv JWT_SECRET 2>/dev/null)
  if [[ -z $nc_secret || -z $eo_secret ]]; then
    check jwt_match FAIL "missing (nc:${#nc_secret} chars, eo:${#eo_secret} chars)"
  elif [[ $nc_secret == "$eo_secret" ]]; then
    check jwt_match PASS
  else
    ws=""; [[ $eo_secret =~ ^[[:space:]]|[[:space:]]$ ]] && ws=" (EO value has leading/trailing whitespace)"
    check jwt_match FAIL "MISMATCH$ws"
  fi
  unset nc_secret eo_secret
fi

# --- human-in-the-loop: the user's exact symptom ------------------------

if [[ ${SKIP_HITL:-0} != 1 ]]; then
  step "On a device ON the tailnet, open a .docx in Nextcloud in the browser."
  capture SYMPTOM_TAILNET "What happened? (y = 'Nextcloud Office cannot be reached' / n = opened and editable / or paste what you saw)"
  [[ $SYMPTOM_TAILNET == n ]] && check document_opens_tailnet PASS || check document_opens_tailnet FAIL "$SYMPTOM_TAILNET"
  step "On a device OFF the tailnet (phone on mobile data, Tailscale off), open: ${DS_URL%/}/web-apps/apps/api/documents/api.js"
  capture API_JS_BROWSER "Did it show JavaScript source? (y/n, or paste the error)"
  step "In Nextcloud (same device), open a .docx in the browser. Keep 'sudo docker logs -f ${EO:-<eo>}' open in another terminal."
  capture SYMPTOM "Did it show 'Nextcloud Office cannot be reached. Please contact admin'? (y = that error / n = document opened and is editable / or paste what you saw)"
  capture EO_LOGGED "Did the Euro-Office logs print anything during the open? (y/n)"
  [[ $API_JS_BROWSER == y ]] && check api_js_from_browser PASS || check api_js_from_browser FAIL "$API_JS_BROWSER"
  [[ $SYMPTOM == n ]] && check document_opens_public PASS || check document_opens_public FAIL "$SYMPTOM"
  RESULTS+=("eo_logged_on_open=$EO_LOGGED")
fi

printf '\n--- Captured ---\n'
printf '%s\n' "${RESULTS[@]}"
if (( FAILED )); then printf 'VERDICT=RED\n'; exit 1; else printf 'VERDICT=GREEN\n'; fi
