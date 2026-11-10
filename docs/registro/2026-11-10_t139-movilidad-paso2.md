## 2026-11-10 — T-139 — Piloto de movilidad, paso 2: indicador de cohesión funcional

Causa: continuación del piloto aprobado (5 provincias, solo indicador, sin peso).
Cambio: `herramientas/movilidad_em_union.py` 1.1.0 (`indicador`: cohesión por distrito y plan, con y sin capital; columna `nmun` en el CSV de áreas, nuevo sha256); `datos/movilidad/piloto_indicador_em1.csv`; `docs/ESTUDIOS/T139_PILOTO_MOVILIDAD_PASO2_2026-11-10.md` (definición, resultados, límites y cómo cubrir las 15 capitales). Copias en `legacy/` de la herramienta y la prueba 1.0.0.
Pruebas: `tests.test_movilidad_em_union` (9; el indicador, sobre un territorio de juguete con valores calculados a mano).
Riesgos: el área partida reparte flujo por población (hipótesis); datos 2019-mar-2020. Depende de #607 (paso 1). Sin efecto en motor, huellas ni 00; no se publica nada.
