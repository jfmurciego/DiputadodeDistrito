#!/usr/bin/env bash
# Resto del despliegue nacional del 31-10-2026: territoriales de las 17 provincias con puentes y,
# para todas las pendientes, legislatura + 00 electoral cuando termina su territorial.
# Uso en el Mac: caffeinate -i bash ~/lanzar_resto.sh | tee ~/lanzar_resto.log
set -u
R=jfmurciego/DiputadodeDistrito
PROVINCIAS=("Congreso Ávila" "Congreso Palencia" "Congreso Segovia" "Congreso Soria" "Congreso Teruel"
            "Congreso Zamora" "Congreso Ceuta" "Congreso Melilla" "Congreso Cuenca" "Congreso Guadalajara")
ultimo() { gh api "repos/$R/actions/workflows/$1/runs?per_page=1&event=workflow_dispatch" --jq '.workflow_runs[0].id' 2>/dev/null; }
lanzar() {
  local wf=$1; shift; local antes; antes=$(ultimo "$wf")
  local args=() a
  for a in "$@"; do [[ "$a" == "-f" ]] && continue; args+=(-f "inputs[${a%%=*}]=${a#*=}"); done
  gh api -X POST "repos/$R/actions/workflows/$wf/dispatches" -f ref=main "${args[@]}" >/dev/null 2>&1 || { echo "ERROR_DISPATCH"; return; }
  for _ in $(seq 1 30); do sleep 5; local id; id=$(ultimo "$wf"); [[ -n "$id" && "$id" != "$antes" ]] && { echo "$id"; return; }; done
  echo "ERROR_SIN_RUN"
}
espera() {
  [[ "$1" =~ ^[0-9]+$ ]] || { echo FALLO; return; }
  while :; do
    s=$(gh api "repos/$R/actions/runs/$1" --jq '.status+" "+(.conclusion//"")' 2>/dev/null)
    case "$s" in "completed success") echo OK; return;; completed*) echo "FALLO"; return;; esac
    sleep 60
  done
}
declare -A T03 T00
T00["Congreso Melilla"]=41236482346
T00["Congreso Cuenca"]=41236647382
T00["Congreso Guadalajara"]=41236816482
T00["Congreso Santa Cruz de Tenerife"]=41239505387
T00["Congreso Álava"]=41240137880
T00["Congreso Albacete"]=41240260992
T00["Congreso Cáceres"]=41240512324
T00["Congreso La Rioja"]=41240637295
T00["Congreso Lugo"]=41240766116
T00["Congreso Orense"]=41240887712
T00["Congreso Salamanca"]=41241010241
T00["Congreso León"]=41241377284
T00["Congreso Castellón"]=41241768943
T00["Congreso Jaén"]=41241896061
T00["Congreso Almería"]=41242160179
T00["Congreso Córdoba"]=41242424551
T00["Congreso Toledo"]=41242809451
T00["Congreso Tarragona"]=41243062797
T00["Congreso Granada"]=41243199582
T00["Congreso Asturias"]=41243326722
T00["Congreso Zaragoza"]=41243577758
T00["Congreso La Coruña"]=41243697404
T00["Congreso Cádiz"]=41243953699
T00["Congreso Sevilla"]=41244347546
T00["Congreso Barcelona"]=41244711464
T00["Congreso Madrid"]=41244835816
T00["Congreso Baleares"]=41250230577; T03["Congreso Baleares"]=41250238804
T00["Congreso Las Palmas"]=41250283081; T03["Congreso Las Palmas"]=41250292326
PUENTES=("Congreso Palencia" "Congreso Ciudad Real" "Congreso Cantabria" "Congreso Gerona" "Congreso Guipúzcoa" "Congreso Huelva" "Congreso Lérida" "Congreso Navarra" "Congreso Burgos" "Congreso Valladolid" "Congreso Vizcaya" "Congreso Badajoz" "Congreso Pontevedra" "Congreso Málaga" "Congreso Murcia" "Congreso Alicante" "Congreso Valencia")
echo "== Fase A: territoriales con puentes $(date +%H:%M)"
for P in "${PUENTES[@]}"; do
  T00[$P]=$(lanzar ejecucion-completa-proyecto.yml -f territory_id="$P" -f data_edition=2025 \
    -f execution_mode="Ejecutar desde el principio" -f optimization_algorithm="Canónico" \
    -f publication_mode=territorial_only -f publish_result=false)
  echo "$P · 00=${T00[$P]}"
  sleep 90
done
echo "== Fase B: legislatura + 00 electoral $(date +%H:%M)"
ORDEN=()
ORDEN=("Congreso Soria" "Congreso Teruel" "Congreso Zamora" "Congreso Ceuta" "Congreso Melilla" "Congreso Cuenca" "Congreso Guadalajara" "Congreso Santa Cruz de Tenerife" "Congreso Álava" "Congreso Albacete" "Congreso Cáceres" "Congreso La Rioja" "Congreso Lugo" "Congreso Orense" "Congreso Salamanca" "Congreso León" "Congreso Castellón" "Congreso Jaén" "Congreso Almería" "Congreso Córdoba" "Congreso Toledo" "Congreso Tarragona" "Congreso Granada" "Congreso Asturias" "Congreso Zaragoza" "Congreso La Coruña" "Congreso Cádiz" "Congreso Sevilla" "Congreso Barcelona" "Congreso Madrid")
ORDEN+=("Congreso Baleares" "Congreso Las Palmas" "${PUENTES[@]}")
for P in "${ORDEN[@]}"; do
  case "$P" in "Congreso Soria"|"Congreso Teruel"|"Congreso Zamora"|"Congreso Ceuta") continue;; esac
  a=$(espera "${T00[$P]}"); b=OK
  [[ -n "${T03[$P]:-}" ]] && b=$(espera "${T03[$P]}")
  if [[ $a != OK || $b != OK ]]; then echo "$P · PARADA (00=$a ${T00[$P]})"; continue; fi
  L=$(lanzar preparacion-legislatura-vigente.yml -f territory="$P" -f operation=prepare_one)
  if [[ $(espera "$L") != OK ]]; then echo "$P · PARADA legislatura $L"; continue; fi
  E=$(lanzar ejecucion-completa-proyecto.yml -f territory_id="$P" -f data_edition=2025 \
    -f execution_mode="Reutilizar progreso existente" -f optimization_algorithm="Canónico" \
    -f publication_mode=electoral -f publish_result=true)
  echo "$P · legislatura=$L OK · 00 electoral=$E"
done
echo "== Fin $(date +%H:%M). Pásame este log."
