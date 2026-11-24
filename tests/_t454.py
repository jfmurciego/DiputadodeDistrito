"""T-454 (P40 1.7.0): deshace en memoria SOLO el paso que espera al artefacto github-pages antes de deploy-pages. Si no está exactamente una vez, falla (control negativo)."""
import copy

PASO_P40 = "Esperar a que el artefacto github-pages sea visible (T-454)"


def deshacer_p40_pasos(steps: list) -> list:
    steps = copy.deepcopy(steps)
    assert [s.get("name") for s in steps].count(PASO_P40) == 1, "falta el paso de T-454 en P40"
    return [s for s in steps if s.get("name") != PASO_P40]


def deshacer_p40(p40: dict) -> dict:
    d = copy.deepcopy(p40)
    d["jobs"]["publicar"]["steps"] = deshacer_p40_pasos(d["jobs"]["publicar"]["steps"])
    return d
