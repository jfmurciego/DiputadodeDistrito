## 2026-11-10 — T-132 — Banco: generador competidor (D-48) y prueba de reproducibilidad

**Causa.** Decisión D-48 del propietario: primera versión del motor nuevo = competición «canónico + GerryChain» bajo el
núcleo de reglas (T-163). La batería de los 71 debe poder juzgar ese competidor (71/71 válidos, ninguno peor que el
canónico, tiempos y reproducibilidad bit a bit) sin cambiar de herramienta.

**Cambio.** `herramientas/banco_generadores.py` 1.1.0: generador «competidor», una orden que sustituye a M05 con
`--params --run-id --semilla` (por defecto `python -m ddd_motor2.competidor`, cambiable con `DDD_COMPETIDOR`); después,
M06 y la validación de producción, como los demás generadores. Subcomando `reproducibilidad`: dos ejecuciones por
territorio y semilla y comparación del sha256 de la composición M06 (`bateria/REPRODUCIBILIDAD.csv`). Copia anterior en
`legacy/herramientas/banco_generadores_v1.0.0_20261109.py`.

**Pruebas.** `tests/test_banco_generadores.py`; en local, con un competidor de prueba (el canónico envuelto), Congreso
Huesca da PASS, idéntico a lo publicado y reproducible bit a bit.
