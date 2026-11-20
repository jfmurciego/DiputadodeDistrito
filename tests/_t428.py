"""T-428 (P40 1.3.0): deshace en memoria SOLO lo que añadió T-428 a los pasos de `publicar`, para que las pruebas de equivalencia
con publicadores anteriores sigan comparando todo lo demás (nombre del paso y líneas exactas; si no están, falla: control negativo)."""
import copy

PASO_V4 = "Promocionar la V4 como portada oficial (T-428)"
VALIDACION_V4 = """          grep -q '<title>Diputado de Distrito | Portada</title>' /tmp/site-candidate/index.html
          test -s /tmp/site-candidate/comprender.html
          test -s /tmp/site-candidate/mapa/index.html
          test -s /tmp/site-candidate/mapa/explorar.js
          grep -q 'url=../"' /tmp/site-candidate/v4/index.html
          grep -q 'url=../../mapa/"' /tmp/site-candidate/v4/mapa/index.html
          test -s /tmp/site-candidate/v1/app.js
          grep -q 'src="v1/app.js"' /tmp/site-candidate/v1/index.html
"""
VALIDACION_V3 = "          grep -q 'url=v3/' /tmp/site-candidate/index.html\n"
DESTINO = ("--destino /tmp/site-candidate/mapa/datos", "--destino /tmp/site-candidate/v4/mapa/datos")


def _sin_sangria(t):
    return "\n".join(l[10:] for l in t.splitlines()) + "\n"


def deshacer(steps):
    steps = [s for s in copy.deepcopy(steps)]
    nombres = [s.get("name") for s in steps]
    assert nombres.count(PASO_V4) == 1, "falta el paso de T-428"
    steps = [s for s in steps if s.get("name") != PASO_V4]
    validar = next(s for s in steps if s.get("name") == "Validar sitio candidato completo")
    nuevo, viejo = _sin_sangria(VALIDACION_V4), _sin_sangria(VALIDACION_V3)
    assert validar["run"].count(nuevo) == 1, "falta la validación de T-428"
    validar["run"] = validar["run"].replace(nuevo, viejo)
    for s in steps:
        if DESTINO[0] in s.get("run", ""):
            s["run"] = s["run"].replace(*DESTINO)
            break
    else:
        raise AssertionError("falta el destino de T-428")
    return steps
