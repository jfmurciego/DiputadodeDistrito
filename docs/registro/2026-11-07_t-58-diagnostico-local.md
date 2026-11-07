## 2026-11-07 — T-58 — Álava: artefacto local, regla de diagnóstico corregida

Causa: la regresión local de Álava dio el distrito 2 en 80.885 (< 95.287) con M04 7.6.7. No era del motor: la regla
de diagnóstico local ejecutaba `ddd_core.m04_seed_engine`, que omite la unidad flexible :F de 7.6.0 (01059:F1), y un
`pip install` sin fijar trajo pandas 3 / geopandas 1.2, que rompe M05 («unidad partida»).
Cambio: `.claude/rules/diagnostico-local.md` manda `modulos/04_generar_semillas.py` e instalar con `requirements.lock`;
línea del forense en `evals/oro/LIBRO_DE_COSTES.md`.
Pruebas: con el envoltorio y el lock, M04+M05 de Álava dan PASS 127.496 / 113.457 / 95.355, igual que el run
41346917857 (publicado, correcto). PR: T-58.
