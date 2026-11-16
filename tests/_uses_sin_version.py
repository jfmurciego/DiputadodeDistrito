"""Equivalencia de workflows (T-366/368/369/370/372): ignora la versión de las acciones de terceros.

Las copias congeladas (`tests/fixtures/*_workflows/`) guardan `uses: owner/repo@<sha> # vX`. Un bump rutinario (Dependabot) no es un
cambio de lógica: aquí cada `uses:` de paso se reduce a `owner/repo`. Las acciones locales (`./…`) y los reutilizables
`./.github/workflows/…` se conservan tal cual. Cambiar la acción, quitar un paso o tocar `with:`/`run:` sigue diferenciando.
El pin por SHA de 40 hex lo exige aparte `tests/test_workflow_safety.py`, que lee los ficheros reales (no esto).
"""
import yaml


def sin_version(o):
    """Copia del árbol YAML con `uses: owner/repo@ref` -> `owner/repo` (solo acciones de terceros)."""
    if isinstance(o, dict):
        return {k: (_uses(v) if k == "uses" else sin_version(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [sin_version(v) for v in o]
    return o


def _uses(v):
    if isinstance(v, str) and not v.startswith("./"):
        return v.split("@", 1)[0]
    return v


def cargar(texto):
    return sin_version(yaml.safe_load(texto))
