"""T-443 (p70-archivo 1.1.7; y P40 1.6.0 abajo): deshace en memoria SOLO el cambio del resumen del paso de P75 (INFORME_CLAVE con `clave_informe` de P75 en vez de
componerlo a mano). Si no está exactamente una vez, falla (control negativo)."""
import copy

IMPORT = 'sys.path.insert(0,"herramientas")\nfrom p75_doble_vuelta_r2 import clave_informe\n'
NUEVO = "INFORME_CLAVE={clave_informe(r, r['run_p75'])}"
VIEJO = "INFORME_CLAVE=doble_vuelta/{r['eleccion']}/{r['run_p75']}/INFORME.json"


def deshacer_job(job: dict) -> dict:
    j = copy.deepcopy(job)
    pasos = [st for st in j["steps"] if NUEVO in st.get("run", "")]
    assert len(pasos) == 1, "falta el cambio de T-443 en el paso de P75"
    st = pasos[0]
    assert st["run"].count(IMPORT) == 1 and st["run"].count(NUEVO) == 1, "cambio de T-443 incompleto"
    st["run"] = st["run"].replace(IMPORT, "").replace(NUEVO, VIEJO)
    return j


def deshacer(p70: dict) -> dict:
    d = copy.deepcopy(p70)
    d["jobs"]["doble_vuelta_r2"] = deshacer_job(d["jobs"]["doble_vuelta_r2"])
    return d


PASO_P40 = "Promover la doble vuelta a mapas/ (T-443)"


def deshacer_p40_pasos(steps: list) -> list:
    """P40 1.6.0: quita SOLO el paso que promueve a `mapas/` (si no está exactamente una vez, falla)."""
    steps = copy.deepcopy(steps)
    assert [s.get("name") for s in steps].count(PASO_P40) == 1, "falta el paso de T-443 en P40"
    return [s for s in steps if s.get("name") != PASO_P40]


def deshacer_p40(p40: dict) -> dict:
    d = copy.deepcopy(p40)
    d["jobs"]["publicar"]["steps"] = deshacer_p40_pasos(d["jobs"]["publicar"]["steps"])
    return d
