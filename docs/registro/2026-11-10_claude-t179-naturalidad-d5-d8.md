## 2026-11-10 — T-179 — Naturalidad: variantes D5 y D8 (tope de desvío solo para elegir)

**Causa:** el propietario quiere ver un término medio entre A (solo población) y C (naturalidad con desvío ≈14 %).
**Cambio:** `ddd_motor2/naturalidad_competicion.py` 1.1.0 (D5/D8 = C con tope de desvío máximo del 5 % / 8 % solo para elegir entre candidatos; mismas cadenas ponderadas y semillas; A/B/C y su huella sin cambios) y `ddd_motor2/naturalidad_informe.py` 1.1.0 (cinco paneles A, D5, D8, C, B; filas D5/D8; `DISTRITOS.csv` por distrito con superficie y núcleo cerrado). Entregable regenerado en `docs/ESTUDIOS/T172_naturalidad/` con la explicación de los distritos urbanos minúsculos. No es regla: núcleo, suelo, techo y K sin cambios. Producción no lo importa; sin huellas ni workflows.
**Pruebas:** `tests.test_motor2_naturalidad` (11, nuevo `test_tope_d5_d8_solo_elige`), `GovernanceHeaders`. Huella A/B/C igual a #651 en León, Cádiz y Asturias; Badajoz, Madrid y Barcelona cambian por la versión de GEOS (una arista distinta): RESULTADO.json guarda ahora el entorno (añadido a los seis ficheros con la misma función `entorno()`).
**Riesgos:** ninguno en producción.
