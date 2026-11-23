"""T-430 paso 3c (P90 1.5.0): deshace en memoria SOLO lo que añadió la publicación de la web al fusionar (salida y bloque `publicar_web`
de `cambios`, job `publicar_web`, el test nuevo en el job `web`) y el arreglo de `rc` del bloque de 3b bajo `bash -e`; después, `_t430c`
deshace 3b. Si algo no está exactamente una vez, falla (control negativo)."""
import copy

from tests import _t430c

BLOQUE_3C = """# T-430 3c (D-194, P7): push a main solo de la web (misma lista y mismo fallo cerrado): publicar la web sola (job `publicar_web`).
publicar_web=false
if [[ "$EVENTO" == "push" && "$files" != "todo" && -n "$files" ]]; then
  rc=0; ajeno="$(grep -vE "$RUTAS_WEB" <<<"$files")" || rc=$?  # 0: hay ajenos; 1: ninguno; >1: error de grep -> no se publica
  if (( rc > 1 )); then echo "::notice::No se pudo clasificar el push como solo web (grep rc=$rc): no se publica la web."
  elif [[ -z "$ajeno" ]] && grep -qE '^visor/v4/' <<<"$files"; then publicar_web=true; fi
fi
echo "publicar_web=$publicar_web" >> "$GITHUB_OUTPUT"
echo "publicar_web=$publicar_web"
"""
RC_NUEVO = 'rc=0; ajeno="$(grep -vE "$RUTAS_WEB" <<<"$files")" || rc=$?  # 0: hay ajenos; 1: ninguno; >1: error de grep -> batería completa'
RC_VIEJO = 'ajeno="$(grep -vE "$RUTAS_WEB" <<<"$files")"; rc=$?  # 0: hay ajenos; 1: ninguno; >1: error de grep -> batería completa'


def _uno(texto, viejo, nuevo, que):
    assert texto.count(viejo) == 1, f"falta {que} de T-430 3c"
    return texto.replace(viejo, nuevo)


def deshacer(p90):
    p = copy.deepcopy(p90)
    c = p["jobs"]["cambios"]
    assert c["outputs"].pop("publicar_web") == "${{ steps.f.outputs.publicar_web }}", "falta la salida publicar_web"
    paso = next(s for s in c["steps"] if s.get("id") == "f")
    paso["run"] = _uno(paso["run"], BLOQUE_3C, "", "el bloque de cambios")
    paso["run"] = _uno(paso["run"], RC_NUEVO, RC_VIEJO, "el arreglo de rc")
    w = p["jobs"]["web"]["steps"][-1]
    w["run"] = _uno(w["run"], " tests.test_t430_web_fusion", "", "el test en el job web")
    del p["jobs"]["publicar_web"]
    return _t430c.deshacer(p)
