"""T-379 PR 2a (D-147, opción a; D-162, opción A): deshace sobre un workflow ya cargado los cambios de la 2a (entornos con los secretos de la
app de registro) para comparar con la versión anterior congelada (`tests/fixtures/t379_2a_workflows/`). La igualdad exacta
`deshacer(actual) == anterior` la fija `tests/test_t379_2a_entorno_registro.py`; las equivalencias antiguas comparan contra `deshacer(actual)`.
"""
import copy

APP = "secrets.DDD_REGISTRO_APP_ID"
REGISTRO_PR = "${{ github.event_name != 'pull_request' && 'registro' || '' }}"
# P40 `preparar` (T-41): personas → `produccion`; robots → `registro` (antes, sin entorno).
P40_PERSONA = ("(github.event_name == 'workflow_dispatch' && github.actor != 'github-actions[bot]' && github.actor != 'ddd-registro[bot]' "
               "&& github.workflow == 'P40 Publicación')")
P40_PREPARAR = "${{ " + P40_PERSONA + " && 'produccion' || 'registro' }}"
P40_PREPARAR_ANTES = "${{ " + P40_PERSONA + " && 'produccion' || '' }}"


def es_registro(env):
    return env in ("registro", REGISTRO_PR)


def deshacer(nombre, doc):
    """`nombre` sin extensión (p. ej. 'p40-publicacion'). Devuelve una copia con la 2a deshecha."""
    d = copy.deepcopy(doc)
    for job in (d.get("jobs") or {}).values():
        env = job.get("environment")
        if es_registro(env):
            job.pop("environment")
        elif env == P40_PREPARAR:
            job["environment"] = P40_PREPARAR_ANTES
    return d
