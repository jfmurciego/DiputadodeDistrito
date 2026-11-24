"""T-430 paso 3c (P90 1.5.0 y 1.5.1): deshace en memoria SOLO lo que añadió la publicación de la web al fusionar (salida y bloque `publicar_web`
de `cambios`, job `publicar_web`, el test nuevo en el job `web`) y el arreglo de `rc` del bloque de 3b bajo `bash -e`; después, `_t430c`
deshace 3b. Si algo no está exactamente una vez, falla (control negativo)."""
import copy

from tests import _t430c

BLOQUE_3C = """# T-430 3c (D-194, P7): push a main solo de la web (misma lista y mismo fallo cerrado): publicar la web sola (job `publicar_web`).
publicar_web=false
if [[ "$EVENTO" == "push" && "$files" != "todo" && -n "$files" ]]; then
  rc=0; ajeno="$(grep -vE "$RUTAS_WEB" <<<"$files")" || rc=$?  # 0: hay ajenos; 1: ninguno; >1: error de grep -> no se publica
  if (( rc > 1 )); then echo "::notice::No se pudo clasificar el push como solo web (grep rc=$rc): no se publica la web."
  elif [[ -z "$ajeno" ]] && grep -qE '^visor/v4/' <<<"$files"; then publicar_web=true
  elif grep -qE '^visor/v4/' <<<"$files"; then echo "::warning::El push toca visor/v4/ junto con otros ficheros: la web en R2 no se publica sola; queda atrás hasta la siguiente P40."; fi
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
    """3c y después 3b (para la equivalencia con pruebas-plataforma, `test_t366`)."""
    return _t430c.deshacer(deshacer_3c(p90))


def deshacer_3c(p90):
    """Solo 3c (para comparar con la 1.4.x congelada, `test_t379_2a`)."""
    p = copy.deepcopy(p90)
    c = p["jobs"]["cambios"]
    assert c["outputs"].pop("publicar_web") == "${{ steps.f.outputs.publicar_web }}", "falta la salida publicar_web"
    paso = next(s for s in c["steps"] if s.get("id") == "f")
    paso["run"] = _uno(paso["run"], BLOQUE_3C, "", "el bloque de cambios")
    paso["run"] = _uno(paso["run"], RC_NUEVO, RC_VIEJO, "el arreglo de rc")
    w = p["jobs"]["web"]["steps"][-1]
    w["run"] = _uno(w["run"], " tests.test_t430_web_fusion", "", "el test en el job web")
    del p["jobs"]["publicar_web"]
    return p


def deshacer_medicion(p90):
    """T-450 §4 (P90 1.5.2): quita el secreto MEDICION_CDN del paso de `medir_web` (posterior a la 2a)."""
    p = copy.deepcopy(p90)
    paso = p["jobs"]["medir_web"]["steps"][-1]
    assert paso.pop("env") == {"MEDICION_CDN": "${{ secrets.MEDICION_CDN }}"}, "falta MEDICION_CDN en medir_web"
    return p


def deshacer_nombre_ia(p90):
    """T-457 (P90 1.5.3): devuelve «Sonnet, » al pie del forense (posterior a la 2a; la 1.4.0 congelada lo lleva)."""
    n = 0

    def rec(x):
        nonlocal n
        if isinstance(x, str):
            if "Forense automático (solo lectura;" in x:
                n += 1
                return x.replace("Forense automático (solo lectura;", "Forense automático (Sonnet, solo lectura;")
            return x
        if isinstance(x, list):
            return [rec(i) for i in x]
        if isinstance(x, dict):
            return {k: rec(v) for k, v in x.items()}
        return x
    r = rec(copy.deepcopy(p90))
    assert n == 1, "falta el pie del forense"
    return r
