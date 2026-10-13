#!/bin/bash
# DDD installer wrapper 1.2.0; 2026-10-10; local candidate.
# Scope: existing launcher; change/reason: requested script with dry-run/backup.
# Origin: instalar_actualizacion.py; new file, no predecessor.
set -euo pipefail
ddd_bundle_root="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ddd_bundle_root/infraestructura/ordenes-manuales/instalar_actualizacion.py" "$@"
