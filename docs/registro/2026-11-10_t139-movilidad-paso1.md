## 2026-11-10 — T-139 — Piloto de movilidad, paso 1: datos EM-1, unión de áreas y 5 provincias

Causa: opción B del propietario (piloto de 5 provincias, solo indicador, sin peso) tras la nota T-138 (#596).
Cambio: `herramientas/movilidad_em_union.py` 1.0.0 (convertir, verificar, candidatas); `datos/movilidad/` (áreas 2019, flujos EM-1 y códigos en CSV, MANIFEST con sha256 de origen y salida); `docs/ESTUDIOS/T139_PILOTO_MOVILIDAD_PASO1_2026-11-10.md` (unión verificada 3.214↔3.214 por nombre normalizado; criterio y 5 provincias: Cádiz, Granada, León, Gerona, Tarragona).
Pruebas: `tests.test_movilidad_em_union` (5 pruebas, valores leídos de los xlsx del INE).
Riesgos: las áreas SCD no se casan con secciones (15 provincias excluidas); datos 2019-mar-2020 con áreas a 1-ene-2019. Sin efecto en motor, huellas ni 00; no se publica nada.
