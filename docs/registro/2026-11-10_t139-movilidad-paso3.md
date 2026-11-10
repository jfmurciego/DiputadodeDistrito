## 2026-11-10 — T-139 — Piloto de movilidad, paso 3: tabla por provincia y recomendación

Causa: cierre del piloto aprobado (5 provincias, solo indicador, sin peso).
Cambio: `herramientas/movilidad_em_union.py` 1.2.0 (`compacidad`: Polsby-Popper del M06 vigente con sha256; `tabla`: Spearman entre indicador, compacidad y población); `datos/movilidad/piloto_compacidad_m06.csv` y `piloto_tabla_provincias.csv`; `docs/ESTUDIOS/T139_PILOTO_MOVILIDAD_PASO3_2026-11-10.md` (tabla y recomendación A/B/C). Copias en `legacy/` de herramienta y prueba 1.1.0.
Pruebas: `tests.test_movilidad_em_union` (12; Spearman con valores conocidos, población M06 = composición).
Riesgos: n pequeño por provincia; un solo plan vigente por territorio; datos 2019-mar-2020. Depende de #607 y #611. Sin efecto en motor, huellas ni 00; no se publica nada.
