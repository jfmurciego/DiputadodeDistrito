## 2026-11-11 — T-233 — La batería vuelca el final de log.txt cuando fallan las entradas

- `herramientas/bateria_motor.py` 1.2.4: si `entradas_uno` falla (FALLO_ADQUISICION o FALLO_M01-M03), imprime en la salida
  del paso las últimas 60 líneas de `bateria/entradas/<t>/log.txt` y una línea `::error title=entradas <t>::<estado> rc=<rc>: <motivo>`
  (última línea de error del log). En r6 (run 42981399280) la traza solo estaba en el artefacto (403 desde la nube).
- Sin cambios en la adquisición, los reintentos, official_live/shapefile ni en la salida de éxito. Copia 1.2.3 en `legacy/`.
- Tests: `T233VolcadoDelLog` (fallo de adquisición, fallo de M01, éxito sin ruido).
