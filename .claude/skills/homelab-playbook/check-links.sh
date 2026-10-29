#!/usr/bin/env bash
# Print every broken relative Markdown link under docs/ (or the given dirs). No output = no broken links.
# Run from the repo root: bash .claude/skills/homelab-playbook/check-links.sh [dir ...]
[[ $# -eq 0 ]] && set -- docs
find "$@" -name '*.md' | while IFS= read -r f; do
  dir=$(dirname "$f")
  grep -o -E '\]\([^)]+\)' "$f" | sed -E 's/^\]\(([^)#]*).*/\1/' | while IFS= read -r t; do
    [[ -z $t || $t == *://* || $t == mailto:* ]] && continue
    [[ -e "$dir/$t" ]] || echo "BROKEN $f -> $t"
  done
done
