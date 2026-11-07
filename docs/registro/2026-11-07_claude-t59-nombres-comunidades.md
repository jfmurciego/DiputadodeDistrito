## 2026-11-07 — T-59 — Nombres de distrito y comarcas partidas de las 49 provincias

Causa: faltaba un nombre legible y estable por distrito nacional y la medida de comarcas partidas (C-12/C-13).
Cambio: `herramientas/generar_nombres_comunidades_nacional.py` 1.0.0 (nueva), `datos/distritos/` (49 `nombres_*.csv`,
49 informes, `toponimos_es.csv`, `municipios_ine_2025.csv`, `MANIFEST.json`), `docs/NOMBRES_Y_COMUNIDADES_NACIONAL.md`
y `tests/test_nombres_comunidades_nacional.py`. Reglas y límites en el documento: comarcas solo en Aragón
(Huesca, Teruel, Zaragoza), el resto `NOT_EVALUABLE`. Sin cambios en motor, contratos, workflows, M06 ni huellas.
Pruebas: tests nuevos, R015 `GovernanceHeaders` y `comprobar_guardian_main.py todo`.
Riesgos: ninguno para checkpoints; no exige ninguna 00.
