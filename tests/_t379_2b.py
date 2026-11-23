"""T-379 PR 2b (D-163, 2b mínima; T-409 añade `PASO_DV_T409`/`sin_t409_run`: la doble vuelta de P30 1.0.2; T-449 añade `sin_t449`: el espejo de P10 1.0.3): deshace sobre un workflow ya cargado (P10, P20, P30 o sus vistas) los cambios de la 2b para comparar con
la versión anterior congelada (`tests/fixtures/t379_2b_workflows/`). La igualdad exacta `deshacer(actual) == anterior` la fija
`tests/test_t379_2b_campana.py`; las equivalencias antiguas (T-375, T-376, T-377, T-332) comparan contra `deshacer(actual)`.
"""
import copy
import re

SIN_CAMPANA = " && !inputs.campana }}"
FALLBACK = 'if [[ -z "${APP_ID:-}" || -z "${APP_KEY:-}" ]]; then echo "Registro con github.token (sin app propia)."; exit 0; fi'
SIN_FALLBACK = ('if [[ -z "${APP_ID:-}" || -z "${APP_KEY:-}" ]]; then echo "::error::Sin la app de registro (DDD_REGISTRO_APP_*): '
                'GITHUB_TOKEN es de solo lectura (T-379 2b, D-163)."; exit 1; fi')
LECTURA = {"contents": "read", "actions": "read"}
PERSIST_CAMPANA = "${{ inputs.campana && 'false' || toJSON(inputs.persist_state) }}"
PERSIST_ANTES = "${{ toJSON(inputs.persist_state) }}"
M04_SERIE = " && (needs.pre_m04_evidence.result == 'success' || needs.pre_m04_evidence.result == 'skipped') }}"


def _on(d):
    return d.get("on") if "on" in d else d.get(True)


PASO_DV_T409 = "Doble vuelta con coaliciones (D-171; no fatal)"  # T-409: lo añadido a P30 1.0.2, que no existía en la 1.0.0 congelada
PASO_ARCHIVO_T409 = "Archivo en origen — M08 a R2 y votos por partido a git"  # el único paso cuyo comando lleva el `--extra` de T-409
EXTRA_T409 = 'extra=(); [[ -d "$GITHUB_WORKSPACE/doble_vuelta" ]] && extra=(--extra "$GITHUB_WORKSPACE/doble_vuelta")\n'


# T-449: lo añadido a P10 1.0.3 (opción «Espejo de fuente oficial», su caso en la entrada y el job aislado `p13_espejo`), que no existía en la 1.0.0 congelada.
OPCION_T449 = "Espejo de fuente oficial"
CASO_T449 = '|"Espejo de fuente oficial") ;;'


GRUPO_T449 = "${{ inputs.tipo == 'Espejo de fuente oficial' && format('ddd-espejo-fuente-{0}', inputs.territorio) || "


def sin_t449(d):
    (d.get("jobs") or {}).pop("p13_espejo", None)
    c = d.get("concurrency")
    if isinstance(c, dict) and str(c.get("group", "")).startswith(GRUPO_T449):
        c["group"] = "${{ " + c["group"][len(GRUPO_T449):]
    tipo = (((_on(d) or {}).get("workflow_dispatch") or {}).get("inputs") or {}).get("tipo") or {}
    if OPCION_T449 in (tipo.get("options") or []):
        tipo["options"] = [o for o in tipo["options"] if o != OPCION_T449]
    for paso in ((d.get("jobs") or {}).get("entrada") or {}).get("steps") or []:
        if isinstance(paso.get("run"), str):
            paso["run"] = paso["run"].replace(CASO_T449, ") ;;")
    return d


def sin_t409_run(run):
    return run.replace(EXTRA_T409, "").replace(' "${extra[@]}"', "")


def deshacer(nombre, doc):
    d = copy.deepcopy(doc)
    on = _on(d) or {}
    wc = (on.get("workflow_call") or {}).get("inputs") or {} if isinstance(on, dict) else {}
    sin_t449(d)
    if "campana" not in wc:
        return d
    wc.pop("campana")
    if d.get("permissions") == LECTURA:
        d["permissions"] = {"contents": "write", "actions": "read"}
    for nombre_job, job in d["jobs"].items():
        cond = job.get("if")
        if isinstance(cond, str) and cond.endswith(SIN_CAMPANA):
            m = re.fullmatch(r"\$\{\{ \((.*)\) && !inputs\.campana \}\}", cond)
            job["if"] = "${{ " + m.group(1) + " }}" if m else cond[: -len(SIN_CAMPANA)] + " }}"
        if nombre_job == "resolver_interfaz" and job.get("permissions") == LECTURA:
            job["permissions"] = {"contents": "write", "actions": "read", "issues": "write"}
        if nombre_job == "m04" and "pre_m04_evidence" in (job.get("needs") or []):
            job["needs"] = [n for n in job["needs"] if n != "pre_m04_evidence"]
            job["if"] = job["if"].replace(M04_SERIE, " }}")
        if job.get("steps"):
            job["steps"] = [s for s in job["steps"] if s.get("name") != PASO_DV_T409]
        for paso in job.get("steps") or []:
            if isinstance(paso.get("run"), str) and paso.get("name") == PASO_ARCHIVO_T409:
                paso["run"] = sin_t409_run(paso["run"])
            if isinstance(paso.get("env"), dict) and paso["env"].get("PERSIST_INPUT") == PERSIST_CAMPANA:
                paso["env"]["PERSIST_INPUT"] = PERSIST_ANTES
            if isinstance(paso.get("if"), str) and paso["if"].endswith(SIN_CAMPANA):
                paso["if"] = paso["if"][: -len(SIN_CAMPANA)] + " }}"
            if isinstance(paso.get("run"), str) and SIN_FALLBACK in paso["run"]:
                paso["run"] = paso["run"].replace(SIN_FALLBACK, FALLBACK)
    return d
