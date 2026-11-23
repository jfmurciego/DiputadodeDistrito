#!/usr/bin/env bash
# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato
# ANTERIOR: ninguna (fichero nuevo)
# CAMBIOS: 1.0.0: fichero nuevo (tabla de población de T-358 o de T-364).
# MOTIVO: T-365 (D-125). Baja las fuentes de una elección y provincia del histórico por época y comprueba su sha256 contra el
#   contrato versionado (configuracion/historico_epoca/contrato_<AAAA_MM>.json). Falla si una huella no coincide.
#   Desde la sesión cloud (16-11) bajan www.ine.es y nazioenbehatokia.eus (HTTP 200); R2 solo desde Actions (secretos).
# USO: bash docs/ESTUDIOS/T365_HISTORICO_POR_EPOCA/bajar_fuentes.sh 2019-11 22 DESTINO
#   Después: python herramientas/contrato_historico_epoca.py cadena --eleccion 2019-11 --territorio nac22 --fuentes DESTINO
set -euo pipefail
E="${1:?elección AAAA-MM}"; CPRO="${2:?provincia 2 cifras}"; D="${3:?carpeta destino}"
RAIZ="$(cd "$(dirname "$0")/../../.." && pwd)"
C="$RAIZ/configuracion/historico_epoca/contrato_${E/-/_}.json"
mkdir -p "$D"
leer() { python3 -c "import json,sys;c=json.load(open(sys.argv[1]));print(eval(sys.argv[2]))" "$C" "$1"; }
bajar() {  # url destino sha256
  if [[ -f "$2" ]] && [[ "$(sha256sum "$2" | cut -d' ' -f1)" == "$3" ]]; then echo "ya está: $2"; return; fi
  code=$(curl -sS -L -o "$2" -w "%{http_code}" "$1" || true)
  [[ "$code" == "200" ]] || { echo "ERROR HTTP $code: $1" >&2; exit 1; }
  got=$(sha256sum "$2" | cut -d' ' -f1)
  [[ "$got" == "$3" ]] || { echo "ERROR sha256 $2: $got != $3" >&2; exit 1; }
  echo "OK $2"
}
bajar "$(leer "c['seccionado']['origen_url']")" "$D/$(leer "c['seccionado']['fichero']")" "$(leer "c['seccionado']['sha256']")"
RUTA="$(leer "c['provincias']['$CPRO']['votos']['ruta']")"
mkdir -p "$D/nazioenbehatokia/$(dirname "$RUTA")"
bajar "https://nazioenbehatokia.eus/$RUTA" "$D/nazioenbehatokia/$RUTA" "$(leer "c['provincias']['$CPRO']['votos']['sha256']")"
# Población por sección: la tabla del contrato se reconstruye desde las fuentes del INE con la herramienta declarada en
# c['poblacion']['origen'] (hoy T-358; T-364 la sustituirá). Huellas de las fuentes en el propio contrato.
bajar https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/30832.csv "$D/30832.csv" "$(leer "c['poblacion']['fuentes']['30832.csv']")"
bajar https://www.ine.es/censos2011_datos/indicadores_seccion_censal_csv.zip "$D/indicadores_seccion_censal_csv.zip" \
  "$(leer "c['poblacion']['fuentes']['indicadores_seccion_censal_csv.zip']")"
TABLA="$D/$(leer "c['poblacion']['fichero']")"
if [[ "$(leer "c['poblacion']['origen']")" == T-364* ]]; then
  # T-364 (D-128, #840): padrón municipal 29005 y los seccionados de 2015, 2016, 2019 y 2020 (huellas de T-357/T-364)
  bajar https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/29005.csv "$D/29005.csv" 8d568dbb14ba1e6cd9d5d3f7db6516842806ce3ba4bdf52938482d2adca50635
  mkdir -p "$D/seccionados"
  for y in 2015 2016 2019 2020; do
    sha=$(awk -v f="seccionado_$y.zip" '$3 ~ f"$" {print $1}' "$RAIZ/docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020/SHA256SUMS.txt")
    bajar "https://www.ine.es/prodyser/cartografia/seccionado_$y.zip" "$D/seccionados/seccionado_$y.zip" "$sha"
  done
  python3 -I "$RAIZ/herramientas/poblacion_seccion_historica.py" --atlas "$D/30832.csv" --censo "$D/indicadores_seccion_censal_csv.zip" \
    --oficial "$D/29005.csv" --seccionados "$D/seccionados" --sumas "$RAIZ/docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020/SHA256SUMS.txt" \
    "$RAIZ/docs/ESTUDIOS/T364_POBLACION_SECCION_INTERPOLADA/SHA256SUMS.txt" --salida "$D"
elif [[ "$(leer "c['poblacion']['origen']")" == T-358* ]]; then
  python3 -I "$RAIZ/herramientas/poblacion_seccion_historica.py" --atlas "$D/30832.csv" --censo "$D/indicadores_seccion_censal_csv.zip" \
    --sumas "$RAIZ/docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020/SHA256SUMS.txt" --tabla "$TABLA" --informe "$D/informe_provincias.csv"
fi
got=$(sha256sum "$TABLA" | cut -d' ' -f1)
[[ "$got" == "$(leer "c['poblacion']['sha256']")" ]] || { echo "ERROR sha256 tabla de población: $got" >&2; exit 1; }
echo "Fuentes de $E/$CPRO listas en $D"
