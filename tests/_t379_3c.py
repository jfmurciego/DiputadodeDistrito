"""T-379 3c-ii (P40 1.4.1): deshace en memoria SOLO lo que la 3c-ii añadió a los pasos de `publicar` (lote `<run>:<espacio>`),
para que las equivalencias con publicadores anteriores sigan comparando todo lo demás. Cada sustitución debe aparecer
exactamente una vez en el conjunto de pasos (si no, falla: control negativo)."""
import copy

# (texto de la 1.4.1, texto anterior), con la sangría del contenido de `run:` ya quitada (10 espacios).
_LOTE_NUEVO = '''# T-379 3c-ii: un elemento es `<run>` o `<run>:<espacio de campaña>` (campaign-<run>-<i>--<hueco>--<territorio>).
run_de() { echo "${1%%:*}"; }
ns_de() { if [[ "$1" == *:* ]]; then echo "${1#*:}"; fi; }
terr_de() { local ns; ns="$(ns_de "$1")"; if [[ -n "$ns" ]]; then echo "${ns##*--}"; fi; }
clave() { echo "${1/:/--}"; }
raiz_run() { if (( ${#LOTE[@]} == 1 )); then echo /tmp/production; else echo "/tmp/production/$(clave "$1")"; fi; }
evidencia_run() { if (( ${#LOTE[@]} == 1 )); then echo .ddd-publication/publicacion_visor.json; else echo ".ddd-publication/publicacion_visor_$(clave "$1").json"; fi; }
territorio_args() { local t; t="$(terr_de "$1")"; if [[ -n "$t" ]]; then echo "--territory-id $t"; fi; }'''
_LOTE_VIEJO = '''raiz_run() { if (( ${#LOTE[@]} == 1 )); then echo /tmp/production; else echo "/tmp/production/$1"; fi; }
evidencia_run() { if (( ${#LOTE[@]} == 1 )); then echo .ddd-publication/publicacion_visor.json; else echo ".ddd-publication/publicacion_visor_$1.json"; fi; }'''

_CAMPANA = '''
if [[ -n "$ns" ]]; then
  # T-379 3c-ii: solo los artefactos de este territorio en el run compartido de la campaña.
  pats=()
  for p in "ddd-audit-$run-$ns" "ddd-audit-electoral-$run-$ns" "ddd-decision-$run-$ns" "ddd-state-$run-M06-$ns" "ddd-state-$run-M08-$ns"; do
    pats+=(--pattern "$p")
  done
  t="$(terr_de "$item")"; man="territorios/$t/evidencia/ejecuciones_completas/$run.json"
  [[ -f "$man" ]] || { echo "sin manifiesto de la campaña $man" > ".ddd-publication/descargas/$k.fallo"; exit 1; }
  if ! gh run download "$run" "${pats[@]}" --dir "$root"; then
    echo "el run $run no se pudo descargar para $ns" > ".ddd-publication/descargas/$k.fallo"; exit 1
  fi
  mkdir -p "$root/ddd-full-run-manifest-$run-$ns" && cp "$man" "$root/ddd-full-run-manifest-$run-$ns/manifest.json"
  lista_completa || { echo "el run $run no trae estado, decisión, auditoría y producto de $ns" > ".ddd-publication/descargas/$k.fallo"; exit 1; }
  echo "DESCARGA run=$run espacio=$ns modo=campana segundos=$(( $(date +%s) - inicio )) mb=$(du -sm "$root" | cut -f1)"
  touch ".ddd-publication/descargas/$k.ok"
  exit 0
fi'''

PARES = [
    (_LOTE_NUEVO, _LOTE_VIEJO),
    ('''item="$1"; run="$(run_de "$item")"; ns="$(ns_de "$item")"; k="$(clave "$item")"
root="$(raiz_run "$item")"; inicio="$(date +%s)"; modo=selectiva''',
     '''run="$1"; root="$(raiz_run "$run")"; inicio="$(date +%s)"; modo=selectiva'''),
    (_CAMPANA, ""),
    ('''  if [[ ! -f ".ddd-publication/descargas/$(clave "$run").ok" ]]; then
    if [[ -f ".ddd-publication/descargas/$(clave "$run").fallo" ]]; then fallos+=("$(cat ".ddd-publication/descargas/$(clave "$run").fallo")"); else''',
     '''  if [[ ! -f ".ddd-publication/descargas/$run.ok" ]]; then
    if [[ -f ".ddd-publication/descargas/$run.fallo" ]]; then fallos+=("$(cat ".ddd-publication/descargas/$run.fallo")"); else'''),
    ('''  # shellcheck disable=SC2046
  python herramientas/evaluar_publicacion_visor.py --requested-run-id "$(run_de "$run")" --production-root "$(raiz_run "$run")" \\
    --phase source --output "$(evidencia_run "$run")" --strict-request $(territorio_args "$run") || fallos+=("$run")''',
     '''  python herramientas/evaluar_publicacion_visor.py --requested-run-id "$run" --production-root "$(raiz_run "$run")" \\
    --phase source --output "$(evidencia_run "$run")" --strict-request || fallos+=("$run")'''),
    ('''out="/tmp/product-descriptors-$(clave "$run").json"''', '''out="/tmp/product-descriptors-$run.json"'''),
    ('''--run-id "$(run_de "$run")"             --output "$out"''', '''--run-id "$run"             --output "$out"'''),
    ('''    # shellcheck disable=SC2046
    python herramientas/evaluar_publicacion_visor.py --requested-run-id "$(run_de "$run")" --registry /tmp/site-candidate/data/viewer-results.json \\
      --phase prepared --output "$(evidencia_run "$run")" --production-root "$(raiz_run "$run")" --strict-request $(territorio_args "$run")''',
     '''    python herramientas/evaluar_publicacion_visor.py --requested-run-id "$run" --registry /tmp/site-candidate/data/viewer-results.json \\
      --phase prepared --output "$(evidencia_run "$run")" --production-root "$(raiz_run "$run")" --strict-request'''),
    ('''args=(--requested-run-id "$(run_de "$run")" --registry''', '''args=(--requested-run-id "$run" --registry'''),
    ('''
    [[ -z "$(terr_de "$run")" ]] || args+=(--territory-id "$(terr_de "$run")")''', ""),
    ('''args=(--requested-run-id "${PRODUCTION_RUN_ID%%:*}" --registry''', '''args=(--requested-run-id "$PRODUCTION_RUN_ID" --registry'''),
]


def _con_sangria(texto, run):
    """Las sustituciones del heredoc llevan además la sangría del bloque donde están (se busca la que casa)."""
    for pre in ("", "  ", "    "):
        t = "\n".join(pre + l if l else l for l in texto.split("\n"))
        if t in run:
            return pre
    return None


def deshacer(steps):
    steps = copy.deepcopy(steps)
    for nuevo, viejo in PARES:
        vistos = 0
        for s in steps:
            run = s.get("run")
            if not isinstance(run, str):
                continue
            pre = _con_sangria(nuevo, run)
            if pre is None:
                continue
            ind = lambda t: "\n".join(pre + l if l else l for l in t.split("\n"))  # noqa: E731
            vistos += run.count(ind(nuevo))
            s["run"] = run.replace(ind(nuevo), ind(viejo))
        assert vistos == 1, f"falta (o se repite) un cambio de la 3c-ii: {nuevo[:80]!r} ({vistos})"
    return steps
