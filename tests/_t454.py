"""T-454 (P40 1.7.0): deshace en memoria SOLO el paso que espera al artefacto github-pages antes de deploy-pages y el nombre de artefacto por intento
(`name` de upload-pages-artifact y `artifact_name` de deploy-pages). Si algo no está exactamente una vez, falla (control negativo)."""
import copy

NOMBRE = "github-pages-${{ github.run_attempt }}"
PASO_P40 = "Esperar a que el artefacto github-pages sea visible (T-454)"


def deshacer_p40_pasos(steps: list) -> list:
    steps = copy.deepcopy(steps)
    assert [s.get("name") for s in steps].count(PASO_P40) == 1, "falta el paso de T-454 en P40"
    steps = [s for s in steps if s.get("name") != PASO_P40]
    sube = [s for s in steps if (s.get("uses") or "").startswith("actions/upload-pages-artifact")]
    despliega = [s for s in steps if (s.get("uses") or "").startswith("actions/deploy-pages")]
    assert len(sube) == 1 and len(despliega) == 1, "faltan los pasos de Pages"
    assert sube[0].get("with", {}).pop("name", None) == NOMBRE, "falta el nombre por intento en la subida (T-454)"
    assert despliega[0].pop("with", None) == {"artifact_name": NOMBRE}, "falta artifact_name en el despliegue (T-454)"
    return steps


def deshacer_p40(p40: dict) -> dict:
    d = copy.deepcopy(p40)
    d["jobs"]["publicar"]["steps"] = deshacer_p40_pasos(d["jobs"]["publicar"]["steps"])
    return d
