#!/bin/bash
# Resto del despliegue nacional (31-10-2026). Compatible con el bash 3.2 de macOS (sin arrays asociativos).
# Uso: caffeinate -i bash ~/lanzar_resto.sh | tee ~/lanzar_resto.log
set -u
R=jfmurciego/DiputadodeDistrito
IDS=$(mktemp)   # líneas «Provincia|run 00|run 03»
ultimo() { gh api "repos/$R/actions/workflows/$1/runs?per_page=1&event=workflow_dispatch" --jq '.workflow_runs[0].id' 2>/dev/null; }
lanzar() {
  local wf=$1; shift; local antes; antes=$(ultimo "$wf"); local args=(); local a
  for a in "$@"; do [ "$a" = "-f" ] && continue; args+=(-f "inputs[${a%%=*}]=${a#*=}"); done
  gh api -X POST "repos/$R/actions/workflows/$wf/dispatches" -f ref=main "${args[@]}" >/dev/null 2>&1 || { echo "ERROR_DISPATCH"; return; }
  local i id; for i in $(seq 1 30); do sleep 5; id=$(ultimo "$wf"); if [ -n "$id" ] && [ "$id" != "$antes" ]; then echo "$id"; return; fi; done
  echo "ERROR_SIN_RUN"
}
espera() {
  case "$1" in ''|*[!0-9]*) echo FALLO; return;; esac
  local s; while :; do
    s=$(gh api "repos/$R/actions/runs/$1" --jq '.status+" "+(.conclusion//"")' 2>/dev/null)
    case "$s" in "completed success") echo OK; return;; completed*) echo FALLO; return;; esac
    sleep 60
  done
}
run00() { grep "^$1|" "$IDS" | tail -1 | cut -d'|' -f2; }
run03() { grep "^$1|" "$IDS" | tail -1 | cut -d'|' -f3; }
cat > "$IDS" <<'LISTA'
Congreso Melilla|41236482346|
Congreso Cuenca|41236647382|
Congreso Guadalajara|41236816482|
Congreso Santa Cruz de Tenerife|41239505387|
Congreso Álava|41240137880|
Congreso Albacete|41240260992|
Congreso Cáceres|41240512324|
Congreso La Rioja|41240637295|
Congreso Lugo|41240766116|
Congreso Orense|41240887712|
Congreso Salamanca|41241010241|
Congreso León|41241377284|
Congreso Castellón|41241768943|
Congreso Jaén|41241896061|
Congreso Almería|41242160179|
Congreso Córdoba|41242424551|
Congreso Toledo|41242809451|
Congreso Tarragona|41243062797|
Congreso Granada|41243199582|
Congreso Asturias|41243326722|
Congreso Zaragoza|41243577758|
Congreso La Coruña|41243697404|
Congreso Cádiz|41243953699|
Congreso Sevilla|41244347546|
Congreso Barcelona|41244711464|
Congreso Madrid|41244835816|
Congreso Baleares|41250230577|41250238804
Congreso Las Palmas|41250283081|41250292326
LISTA
PUENTES="Congreso Palencia;Congreso Ciudad Real;Congreso Cantabria;Congreso Gerona;Congreso Guipúzcoa;Congreso Huelva;Congreso Lérida;Congreso Navarra;Congreso Burgos;Congreso Valladolid;Congreso Vizcaya;Congreso Badajoz;Congreso Pontevedra;Congreso Málaga;Congreso Murcia;Congreso Alicante;Congreso Valencia"
echo "== Fase A: territoriales con puentes $(date +%H:%M)"
IFS=';'; for P in $PUENTES; do unset IFS
  id=$(lanzar ejecucion-completa-proyecto.yml -f territory_id="$P" -f data_edition=2025 \
    -f execution_mode="Ejecutar desde el principio" -f optimization_algorithm="Canónico" \
    -f publication_mode=territorial_only -f publish_result=false)
  echo "$P|$id|" >> "$IDS"; echo "$P · 00=$id"
  sleep 90; IFS=';'
done; unset IFS
echo "== Fase B: legislatura + 00 electoral $(date +%H:%M)"
while IFS= read -r P <&3; do
  a=$(espera "$(run00 "$P")"); b=OK; t3=$(run03 "$P"); [ -n "$t3" ] && b=$(espera "$t3")
  if [ "$a" != OK ] || [ "$b" != OK ]; then echo "$P · PARADA (00=$a $(run00 "$P"))"; continue; fi
  L=$(lanzar preparacion-legislatura-vigente.yml -f territory="$P" -f operation=prepare_one)
  if [ "$(espera "$L")" != OK ]; then echo "$P · PARADA legislatura $L"; continue; fi
  E=$(lanzar ejecucion-completa-proyecto.yml -f territory_id="$P" -f data_edition=2025 \
    -f execution_mode="Reutilizar progreso existente" -f optimization_algorithm="Canónico" \
    -f publication_mode=electoral -f publish_result=true)
  echo "$P · legislatura=$L OK · 00 electoral=$E"
done 3< <(cut -d'|' -f1 "$IDS")
echo "== Fin $(date +%H:%M). Pásame este log."
