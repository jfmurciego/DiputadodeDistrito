#!/usr/bin/env bash
set -euo pipefail

for attempt in 1 2 3; do
  if git pull --rebase origin main && git push origin HEAD:main; then
    exit 0
  fi
  git rebase --abort >/dev/null 2>&1 || true
  if [[ "$attempt" == 3 ]]; then
    echo "::error::No se pudo sincronizar el estado operativo antes de publicar." >&2
    exit 48
  fi
  sleep $((attempt * 2))
done
