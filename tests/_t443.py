"""T-443 (p70-archivo 1.1.7): deshace en memoria SOLO el cambio del resumen del paso de P75 (INFORME_CLAVE con `clave_informe` de P75 en vez de
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
