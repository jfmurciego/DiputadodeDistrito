"""T-430 paso 2 (P40 1.5.0): deshace en memoria SOLO el paso «Web en R2 (T-430)» para las pruebas de equivalencia (control negativo:
si el paso no está exactamente una vez, falla)."""
import copy

PASO = "Web en R2 (T-430)"


def deshacer(steps):
    steps = copy.deepcopy(steps)
    assert [s.get("name") for s in steps].count(PASO) == 1, "falta el paso de T-430 (web)"
    return [s for s in steps if s.get("name") != PASO]
