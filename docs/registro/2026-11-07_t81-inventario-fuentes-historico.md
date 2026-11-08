## 2026-11-07 — T-81 — Inventario de fuentes del histórico de generales 2011-2023

**Causa:** decisiones D-9 y D-11: hay que saber, por elección y provincia, qué fuente, fecha, sha256 y cobertura tenemos antes de construir el histórico.

**Cambio:** `herramientas/inventario_fuentes_historico.py` 1.0.0 y `orchestracion/inventario_fuentes_historico.json` (6 elecciones × 52 provincias, sin red, a partir del manifiesto T-89 y los contratos de Infoelectoral); informe en `docs/ESTUDIOS/T81_INVENTARIO_FUENTES_HISTORICO/INFORME.md`. Hallazgos: Observatorio 52/52 en las 6; Infoelectoral solo 2023-07; sin oficial local en 2011, 2015, 2016 y 2019-04; seccionados INE históricos sin adquirir.

**Pruebas:** `tests/test_inventario_fuentes_historico.py` (sintético, valores a mano; el JSON real debe estar al día).

**Efectos:** ninguno en huellas, checkpoints ni workflows. Nada lanzado ni publicado.
