#!/usr/bin/env bash
# PROYECTO: Diputado de Distrito
# COMPONENTE: operación local
# VERSIÓN: 1.0.0
# NOMBRE DE VERSIÓN: Lanzador local reproducible
# FECHA: 2026-09-14
# ESTADO: candidato
# QUÉ HACE: comprueba, construye, admite, prueba o ejecuta DDD mediante el Docker fijado del repositorio.
# CAMBIOS: primera versión.
# MOTIVO: permitir una operación local en macOS sin instalar ni modificar Python, Conda o Miniforge.
# ANTERIOR: ninguno — componente nuevo.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
IMAGE="${DDD_LOCAL_IMAGE:-ddd-local:1.0}"

usage() {
  cat <<'EOF'
Uso:
  ./ddd-local.sh comprobar
  ./ddd-local.sh construir
  ./ddd-local.sh admitir <territorio|ruta-yaml>
  ./ddd-local.sh probar
  ./ddd-local.sh ejecutar <territorio|ruta-yaml> [desde] [hasta] --autorizar

Ejemplos:
  ./ddd-local.sh admitir aragon
  ./ddd-local.sh ejecutar aragon M01 M08 --autorizar
EOF
}

die(){ echo "[FATAL] $*" >&2; exit 2; }
need_docker(){ command -v docker >/dev/null 2>&1 || die "Docker no está disponible. Instala y abre Docker Desktop."; }
need_image(){ docker image inspect "$IMAGE" >/dev/null 2>&1 || die "Falta la imagen $IMAGE. Ejecuta primero: ./ddd-local.sh construir"; }

params_path() {
  local value="${1:-}"
  [[ -n "$value" ]] || die "Falta territorio o ruta YAML"
  if [[ "$value" == *.yaml || "$value" == */* ]]; then
    printf '%s\n' "$value"
  else
    printf 'territorios/%s/config/%s_2025.yaml\n' "$value" "$value"
  fi
}

command_name="${1:-}"
case "$command_name" in
  comprobar)
    need_docker
    test -f Dockerfile || die "Falta Dockerfile"
    test -f requirements.lock || die "Falta requirements.lock"
    test -f procedimiento.sh || die "Falta procedimiento.sh"
    bash -n procedimiento.sh
    docker version >/dev/null
    echo "[OK] Repositorio y Docker preparados. No se ha ejecutado ningún módulo."
    ;;
  construir)
    need_docker
    docker build --pull -t "$IMAGE" .
    echo "[OK] Imagen local construida: $IMAGE"
    ;;
  admitir)
    need_docker; need_image
    params="$(params_path "${2:-}")"
    test -f "$params" || die "No existe $params"
    tmp_dir="$(mktemp -d)"
    trap 'rm -rf "$tmp_dir"' EXIT
    docker run --rm -v "$ROOT:/app" -v "$tmp_dir:/ddd-out" -w /app \
      --entrypoint python "$IMAGE" herramientas/resolver_ejecucion_territorial.py \
      --params "$params" --run-id local-admission --output /ddd-out/decision.json
    cat "$tmp_dir/decision.json"
    echo
    echo "[OK] Contrato evaluado. No se ha ejecutado ningún módulo."
    ;;
  probar)
    need_docker; need_image
    docker run --rm -v "$ROOT:/app" -w /app --entrypoint python "$IMAGE" \
      -m unittest discover -s tests -p 'test_*.py' -v
    ;;
  ejecutar)
    need_docker; need_image
    params="$(params_path "${2:-}")"
    test -f "$params" || die "No existe $params"
    from_stage="${3:-M01}"
    to_stage="${4:-M08}"
    authorization="${5:-}"
    [[ "$authorization" == "--autorizar" ]] || die "La ejecución requiere terminar el comando con --autorizar"
    run_id="local-$(date -u +%Y%m%dT%H%M%SZ)"
    docker run --rm -v "$ROOT:/app" -w /app \
      -e DDD_PARAMS="$params" -e DDD_RUN_ID="$run_id" \
      -e DDD_FROM_STAGE="$from_stage" -e DDD_TO_STAGE="$to_stage" \
      "$IMAGE"
    ;;
  *)
    usage
    [[ -z "$command_name" ]] && exit 0
    exit 2
    ;;
esac
