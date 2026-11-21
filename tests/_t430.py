"""T-430 fase 1 (P40 1.4.0): deshace en memoria SOLO el paso que añadió T-430 a `publicar`, para que las pruebas de equivalencia con
publicadores anteriores sigan comparando todo lo demás (si el paso no está exactamente una vez, falla: control negativo)."""
import copy

PASO = "Datos de la web en R2 (T-430)"


def deshacer(steps):
    steps = copy.deepcopy(steps)
    assert [s.get("name") for s in steps].count(PASO) == 1, "falta el paso de T-430"
    return [s for s in steps if s.get("name") != PASO]
