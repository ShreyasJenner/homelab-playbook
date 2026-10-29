#!/usr/bin/env bash
# Print every identifying detail left in the given blog drafts. No output = clean.
# Run from the repo root: bash .claude/skills/homelab-blog/check-public.sh blog/drafts/<post>.md [...]
# Allowlists (committed, first field per line, # comments): blog/public-domains.txt, blog/public-ports.txt.
# Denylist (real names and values, never committed): .scratch/blog/denylist.txt, one string per line.
deny=.scratch/blog/denylist.txt
[[ -s $deny ]] || { echo "MISSING $deny"; exit 1; }

fields() { grep -vE '^\s*(#|$)' "$1" 2>/dev/null | awk '{print $1}'; }
mapfile -t domains < <(fields blog/public-domains.txt)
mapfile -t ports < <(fields blog/public-ports.txt)
ext='yml|yaml|ini|json|md|php|conf|cfg|sh|txt|env|toml|log|js|ts|py|db|sqlite|service|mount|timer|socket|network|xml|html|css|lock|bak|pem|crt|key|csv|mp4|mkv|jpg|png|gz|tar|zip|sql'

# allowed KIND MATCH: succeeds for stand-ins, well-known public values and allowlisted entries
allowed() {
  local kind=$1 m=${2,,} x
  case $kind in
    IPV4) [[ $m =~ ^(192\.0\.2|198\.51\.100|203\.0\.113)\. || $m =~ ^(127\.0\.0\.1|0\.0\.0\.0|8\.8\.8\.8|1\.1\.1\.1|100\.100\.100\.100)$ ]] ;;
    IPV6) [[ ( ! $m =~ [a-f] && $m != *::* ) || $m == 2001:db8:* || $m == ::1 ]] ;;
    EMAIL) [[ $m =~ @(.+\.)?example\.(com|net|org)$ ]] ;;
    DOMAIN)
      [[ $m == *ts.net ]] && return 1
      [[ ${m##*.} =~ ^($ext)$ || $m =~ (^|\.)example\.(com|net|org)$ || $m =~ \.(example|test|invalid|localhost)$ ]] && return 0
      for x in "${domains[@]}"; do [[ $m == "${x,,}" ]] && return 0; done; return 1 ;;
    PORT) for x in "${ports[@]}"; do [[ $m == "$x" ]] && return 0; done; return 1 ;;
    *) return 1 ;;
  esac
}

for f in "$@"; do
  while read -r kind re; do
    grep -noP -- "$re" "$f" | while IFS=: read -r line m; do
      allowed "$kind" "$m" || echo "$kind $f:$line: $m"
    done
  done <<'EOF'
IPV4 \b(?:\d{1,3}\.){3}\d{1,3}\b
IPV6 (?i)(?<![\w:])(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}(?![\w:])
MAC (?i)\b(?:[0-9a-f]{2}-){5}[0-9a-f]{2}\b
EMAIL [\w.+-]+@[\w-]+(?:\.[\w-]+)+
DOMAIN (?i)\b(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}\b
PORT (?<=:)\d{2,5}\b
PORT (?i)(?<=\bport )\d{2,5}\b
PORT (?i)(?<=\bports )\d{2,5}\b
PORT \b\d{2,5}(?=:\d)
UUID (?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b
KEY (?<![A-Za-z0-9+/])(?=[A-Za-z0-9+/]*\d)(?=[A-Za-z0-9+/]*[A-Z])(?=[A-Za-z0-9+/]*[a-z])[A-Za-z0-9+/]{32,}={0,2}
KEY \b[0-9a-fA-F]{32,}\b
KEY \b(?:tskey|ghp|gho|glpat|xox[bp])[-_]\S+
CONTAINER_ID \b(?=[0-9a-f]{0,11}[a-f])(?=[0-9a-f]{0,11}\d)[0-9a-f]{12}\b
PATH (?:/home/|/Users/|/root/)\S*
PATH /mnt/(?!media\b|backup\b)\S+
DATE \b20\d{2}-\d{2}-\d{2}\b
DATE \b20\d{6}\b
EOF
  grep -vE '^\s*(#|$)' "$deny" | grep -noiF -f - "$f" | sed -E "s|^([0-9]+):|DENYLIST $f:\1: |"
done
