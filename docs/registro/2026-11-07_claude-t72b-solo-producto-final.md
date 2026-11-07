## 2026-11-07 — T-72 — Solo el producto final de cada run en R2

- Causa: el propietario fija R2 bajo 10 GB; #471 subía M06 y M08 y el archivista copiaba también M01-M05 y paquetes
  fuente (R2 ya tiene 27,9 GB).
- Cambio: el estado M08 es acumulativo (lleva cache/run del M06; M08 = M06 + 1-10 MB). Tras subir el M08, el
  reutilizable electoral (1.2.0) llama a `archivo_origen.py r2 --sustituye-m06-run`, que retira de R2 el M06 del run
  territorial y anota `incluye_m06_run` en la entrada M08 (si la retirada falla, solo avisa). El archivista
  (`archivar_artefactos_r2.py` 1.1.0) deja de copiar M01-M05 y paquetes fuente y omite el M06 si vive su M08. El check
  acepta el M08 que contiene el M06 publicado; Murcia sale de las excepciones (quedan 48).
- Tamaño medio del producto final por run: 150,6 MB (mediana 113, máx. 367; 32 runs del manifiesto actual).
  La limpieza de los 27,9 GB actuales es T-76.
- Pruebas: retirada del M06 (y fallo al retirar), cobertura por M08 en el check, archivista solo finales.
- Riesgos: toca la 00 (`no-automerge`); se valida en la misma 00 de prueba de T-72.
