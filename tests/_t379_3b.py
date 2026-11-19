"""T-379 PR 3b: deshace sobre P10 o P20 ya cargados los cambios de la 3b (registro en ensayo con campaña) para comparar con
la 1.0.1 congelada en `tests/fixtures/t379_3b_workflows/`. `tests._t379_2b.deshacer` lo aplica primero, así que las
equivalencias antiguas siguen comparando contra su versión de origen. La igualdad exacta la fija `tests/test_t379_3b_workflows.py`.
"""
import copy
import re

ENSAYO = "Registro en ensayo (campaña)"
CAPTURA = "Capturar el registro (campaña)"
SOLO_SIN_CAMPANA = "${{ !inputs.campana }}"
JOBS = {
    "p10-fuentes": ("p11_registrar", "p11_generation_pending", "p12_registrar"),
    "p20-distritos": ("pre_m04_evidence", "pre_m04_diagnostic", "registrar"),
}
PERSIST_3B = "${{ toJSON(inputs.persist_state) }}"
PERSIST_2B = "${{ inputs.campana && 'false' || toJSON(inputs.persist_state) }}"
REF_3B = re.compile(r"\$\{\{ inputs\.campana && github\.sha \|\| (needs\.[a-z0-9_]*registrar\.outputs\.promotion_sha) \}\}")
GRUPO = re.compile(r"\$\{\{ inputs\.campana && format\('ddd-campana-\{0\}-\{1\}', inputs\.campana, [a-z0-9_.]+\) \|\| '([a-z-]+)' \}\}")


def jobs_3b(doc):
    """Jobs con el paso de ensayo (vale para P10, P20 y las vistas de P10, que renombran los jobs)."""
    return [j for j, job in (doc.get("jobs") or {}).items() if any(s.get("name") == ENSAYO for s in job.get("steps") or [])]


def es_3b(nombre, doc):
    return bool(jobs_3b(doc))


def deshacer(nombre, doc):
    d = copy.deepcopy(doc)
    if not es_3b(nombre, d):
        return d
    for j in jobs_3b(d):
        job = d["jobs"][j]
        m = re.fullmatch(r"\$\{\{ (.*) \}\}", job["if"])
        job["if"] = "${{ (" + m.group(1) + ") && !inputs.campana }}"
        job["steps"] = [s for s in job["steps"] if s.get("name") not in (ENSAYO, CAPTURA)]
        for s in job["steps"]:
            if s.get("name") == "Credencial de registro" and s.get("if") == SOLO_SIN_CAMPANA:
                del s["if"]
            m = REF_3B.fullmatch(str((s.get("with") or {}).get("ref", "")))
            if m:
                s["with"]["ref"] = "${{ " + m.group(1) + " }}"
        c = job.get("concurrency")
        if isinstance(c, dict) and isinstance(c.get("group"), str):
            g = GRUPO.fullmatch(c["group"])
            if g:
                c["group"] = g.group(1)
    if nombre != "p20-distritos":  # P10 y sus vistas: los resolutores vuelven a forzar sin persistencia con campaña
        for j, job in d["jobs"].items():
            if j.endswith("resolver"):
                for s in job.get("steps") or []:
                    if (s.get("env") or {}).get("PERSIST_INPUT") == PERSIST_3B:
                        s["env"]["PERSIST_INPUT"] = PERSIST_2B
    return d


P40_P00 = "(github.workflow == 'P40 Publicación' || contains(github.workflow_ref, '/.github/workflows/p00-campana.yml@'))"
P40_ANTES = "github.workflow == 'P40 Publicación'"


def sin_p00_en_p40(expresion):
    """La condición de `produccion` de P40 sin lo que añade la 3b (G4)."""
    return expresion.replace(P40_P00, P40_ANTES)
