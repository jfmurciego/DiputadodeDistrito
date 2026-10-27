#!/bin/bash
# DDD installer wrapper 1.3.0; 2026-10-11; local candidate.
# Scope: existing launcher; change/reason: requested script with dry-run/backup.
# Origin: instalar_actualizacion.py; predecessor: infraestructura/ordenes-manuales/legacy/1.2.0/instalar-ddd-auto.sh.
set -euo pipefail
ddd_bundle_root="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ddd_bundle_root/infraestructura/ordenes-manuales/instalar_actualizacion.py" "$@"
