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
REF_3B = "${{ inputs.campana && github.sha || needs.p11_registrar.outputs.promotion_sha }}"
REF_2B = "${{ needs.p11_registrar.outputs.promotion_sha }}"
GRUPO = re.compile(r"\$\{\{ inputs\.campana && format\('ddd-campana-\{0\}-\{1\}', inputs\.campana, [a-z0-9_.]+\) \|\| '([a-z-]+)' \}\}")


def es_3b(nombre, doc):
    jobs = (doc.get("jobs") or {})
    return any(s.get("name") == ENSAYO for j in JOBS.get(nombre, ()) for s in (jobs.get(j) or {}).get("steps") or [])


def deshacer(nombre, doc):
    d = copy.deepcopy(doc)
    if not es_3b(nombre, d):
        return d
    for j in JOBS[nombre]:
        job = d["jobs"][j]
        m = re.fullmatch(r"\$\{\{ (.*) \}\}", job["if"])
        job["if"] = "${{ (" + m.group(1) + ") && !inputs.campana }}"
        job["steps"] = [s for s in job["steps"] if s.get("name") not in (ENSAYO, CAPTURA)]
        for s in job["steps"]:
            if s.get("name") == "Credencial de registro" and s.get("if") == SOLO_SIN_CAMPANA:
                del s["if"]
            if (s.get("with") or {}).get("ref") == REF_3B:
                s["with"]["ref"] = REF_2B
        c = job.get("concurrency")
        if isinstance(c, dict) and isinstance(c.get("group"), str):
            g = GRUPO.fullmatch(c["group"])
            if g:
                c["group"] = g.group(1)
    if nombre == "p10-fuentes":
        for j in ("p11_resolver", "p12_resolver"):
            for s in d["jobs"][j]["steps"]:
                if (s.get("env") or {}).get("PERSIST_INPUT") == PERSIST_3B:
                    s["env"]["PERSIST_INPUT"] = PERSIST_2B
    return d


P40_P00 = "(github.workflow == 'P40 Publicación' || contains(github.workflow_ref, '/.github/workflows/p00-campana.yml@'))"
P40_ANTES = "github.workflow == 'P40 Publicación'"


def sin_p00_en_p40(expresion):
    """La condición de `produccion` de P40 sin lo que añade la 3b (G4)."""
    return expresion.replace(P40_P00, P40_ANTES)
