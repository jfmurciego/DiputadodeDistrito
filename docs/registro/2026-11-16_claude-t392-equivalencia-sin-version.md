## 2026-11-16 — T-392 — Equivalencia congelada ignora la versión de las acciones de terceros

Causa: la PR #863 de Dependabot (bump de `anthropics/claude-code-action` en `p90-automatico.yml` y `revisor-pr.yml`) ponía la CI en rojo solo por
`test_t366_p90_equivalencia::test_job_a_job_sin_diferencias` («pasos difieren»): los tests de equivalencia comparan los pasos contra copias congeladas
con el `uses: owner/repo@<sha>` literal, y cualquier bump rutinario los rompía sin cambio de lógica.

Cambio (solo tests): `tests/_uses_sin_version.py` reduce cada `uses:` de acción de terceros a `owner/repo` (conserva `./…` y los reutilizables locales)
al cargar los YAML en t366, t368, t369, t370 y t372; t370 ajusta sus `startswith("…@")`. `tests/test_uses_sin_version.py` añade controles negativos
(otra acción, `with:`, `run:`, paso quitado siguen diferenciando). El pin por SHA de 40 hex sigue exigido por `test_workflow_safety` (lee los ficheros reales).

Pruebas: en un worktree con `main` + la rama de Dependabot de #863, t366 falla sin este cambio (única causa) y pasa con él, junto con t368/369/370/372 y
`test_workflow_safety`; cambiar la acción en P90 vuelve a fallar. No se empuja a la rama de Dependabot.
