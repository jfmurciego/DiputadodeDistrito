"""T-379 PR 2a (D-147, opción a): deshace sobre un workflow ya cargado los cambios de la 2a (entorno `registro` y jobs partidos de P40 y P70)
para comparar con la versión anterior congelada (`tests/fixtures/t379_2a_workflows/`). La igualdad exacta `deshacer(actual) == anterior` la fija
`tests/test_t379_2a_entorno_registro.py`; las equivalencias antiguas (T-368, T-372) comparan contra `deshacer(actual)`.
"""
import copy
import re

REGISTRO_PR = "${{ github.event_name != 'pull_request' && 'registro' || '' }}"
APP = "secrets.DDD_REGISTRO_APP_ID"


def es_registro(env):
    return env in ("registro", REGISTRO_PR)


def _paso(job, nombre):
    return next(i for i, s in enumerate(job["steps"]) if s.get("name") == nombre)


def _deshacer_p40(d):
    j = d["jobs"]
    apr = j.pop("aprobar")
    cond = re.fullmatch(r"\$\{\{ needs\.resolver\.outputs\.publicar == 'true' && (.*) \}\}", apr["if"]).group(1)
    pre = j["preparar"]
    pre["needs"] = "resolver"
    pre["if"] = "${{ needs.resolver.outputs.publicar == 'true' }}"
    pre["environment"] = "${{ " + cond + " && 'produccion' || '' }}"
    reg = j.pop("registrar")
    cred = reg["steps"][_paso(reg, "Credencial de registro")]
    bucle = reg["steps"][_paso(reg, "Persistir registro en main")]["run"]
    bucle = bucle[bucle.index("for attempt in 1 2 3; do"):]
    pub = j["publicar"]
    pub.pop("outputs")
    pub["steps"].insert(1, copy.deepcopy(cred))
    pub["steps"] = [s for s in pub["steps"] if s.get("name") != "Conservar el parche del registro"]
    per = pub["steps"][_paso(pub, "Persistir registro sólo después del despliegue")]
    per.pop("id")
    run = per["run"]
    run = run[:run.index("# T-379 PR 2a: el push a main")] + bucle
    per["run"] = run
    j["publicar"] = {k: pub[k] for k in pub}  # mismo contenido; el orden de claves no cuenta en la igualdad


def _deshacer_p70(d):
    j = d["jobs"]
    reg = j.pop("registrar_poda")
    pod = j["podar"]
    pod["permissions"] = {"contents": "write"}
    pod.pop("outputs")
    pod["steps"].insert(1, copy.deepcopy(reg["steps"][_paso(reg, "Credencial de registro")]))
    poda = pod["steps"][_paso(pod, "Verificar y podar")]
    poda.pop("id")
    poda["run"] = "".join(l for l in poda["run"].splitlines(keepends=True) if 'echo "informe=$informe"' not in l)
    paso = copy.deepcopy(reg["steps"][_paso(reg, "Registrar informe y manifiesto en main")])
    paso.pop("env")
    paso = {"name": paso["name"], "if": "${{ always() && !inputs.simular }}", **{k: v for k, v in paso.items() if k != "name"}}
    pod["steps"].append(paso)


def deshacer(nombre, doc):
    """`nombre` sin extensión (p. ej. 'p40-publicacion'). Devuelve una copia con la 2a deshecha."""
    d = copy.deepcopy(doc)
    if nombre == "p40-publicacion":
        _deshacer_p40(d)
    elif nombre == "p70-archivo":
        _deshacer_p70(d)
    for job in d["jobs"].values():
        if es_registro(job.get("environment")):
            job.pop("environment")
    return d
