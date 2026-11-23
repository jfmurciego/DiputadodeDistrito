"""T-430 paso 3b (P90 1.4.0): deshace en memoria SOLO lo que añadió el atajo de CI de la web a `cambios` y `pruebas`, para que la
equivalencia con pruebas-plataforma siga comparando todo lo demás (si algo no está exactamente una vez, falla: control negativo)."""
import copy

BLOQUE_CAMBIOS = """# T-430 3b (D-194, P6): PR que solo toca la web (y toca visor/v4/): pruebas de la web en vez de la batería completa.
web=false
if [[ "$EVENTO" == "pull_request" && "$files" != "todo" && -n "$files" ]]; then
  ajeno="$(grep -vE "$RUTAS_WEB" <<<"$files" || true)"
  if [[ -z "$ajeno" ]] && grep -qE '^visor/v4/' <<<"$files"; then web=true; fi
fi
echo "web=$web" >> "$GITHUB_OUTPUT"
echo "web=$web"
"""
NUEVO_PRUEBAS = """# ...o en una PR que solo toca la web (T-430 3b): entonces el job `web` tiene que estar en verde.
if [[ "$ES_WEB" == "true" && "$WEB" != "success" ]]; then
  echo "::error::pruebas en rojo: PR solo de la web y web=$WEB."; exit 1
fi
if [[ "$SUITE" != "success" && ! ( "$SUITE" == "skipped" && "$ROBOT" == "true" ) && ! ( "$SUITE" == "skipped" && "$ES_WEB" == "true" && "$WEB" == "success" ) ]]; then
  echo "::error::pruebas en rojo: suite=$SUITE (robot=$ROBOT, web=$ES_WEB/$WEB)."; exit 1
fi
"""
VIEJO_PRUEBAS = """if [[ "$SUITE" != "success" && ! ( "$SUITE" == "skipped" && "$ROBOT" == "true" ) ]]; then
  echo "::error::pruebas en rojo: suite=$SUITE (robot=$ROBOT)."; exit 1
fi
"""


def _uno(texto, viejo, nuevo, que):
    assert texto.count(viejo) == 1, f"falta {que} de T-430 3b"
    return texto.replace(viejo, nuevo)


def deshacer(p90):
    p = copy.deepcopy(p90)
    c = p["jobs"]["cambios"]
    assert c["outputs"].pop("web") == "${{ steps.f.outputs.web }}", "falta la salida web"
    paso = next(s for s in c["steps"] if s.get("id") == "f")
    assert paso["env"].pop("RUTAS_WEB").startswith("^(visor/v4/"), "falta RUTAS_WEB"
    paso["run"] = _uno(paso["run"], BLOQUE_CAMBIOS, "", "el bloque de cambios")
    pr = p["jobs"]["pruebas"]
    assert pr["needs"][-1] == "web", "falta web en needs"
    pr["needs"] = pr["needs"][:-1]
    s = pr["steps"][0]
    assert s["env"].pop("ES_WEB") and s["env"].pop("WEB"), "faltan ES_WEB/WEB"
    s["run"] = _uno(s["run"], NUEVO_PRUEBAS, VIEJO_PRUEBAS, "la agregación de pruebas")
    p["jobs"]["suite"]["if"] = _uno(p["jobs"]["suite"]["if"], " && needs.cambios.outputs.web != 'true'", "", "el if de suite")
    del p["jobs"]["web"]
    return p
