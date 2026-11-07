## 2026-11-07 — T-72 — Paquete mínimo por run en R2

- Causa: el propietario fija R2 total ≤ 8 GB. #471 subía los ZIP de estado M06 y M08 (media de 150,6 MB por run) y el
  archivista copiaba también M01-M05 y los paquetes fuente (R2 ya tiene 27,9 GB).
- Cambio: a R2 va un paquete mínimo `ddd-minimo-<run>-M06|M08.zip` (`archivar_artefactos_r2.py` 1.1.0,
  `empaquetar_minimo`), ZIP determinista con: GeoJSON distritales (sin claves de sección, ≤ 2000 features), CSV/JSON
  `_m06_`/`_m07_`/`_m08_` (composición sección→distrito, resúmenes, resultados, reconciliación), VALIDACION,
  CHAIN_STATE, production_status y manifiestos, los `--extra` del job (auditoría M06 y manifiesto de generación) y
  `MANIFEST_MINIMO.json` (sha256 de cada fichero y sha256/tamaño del ZIP de estado original, también en
  `archivo_r2.json`). El estado M08 es acumulativo, así que el paquete M08 lleva lo del M06 y el reutilizable electoral
  (1.2.1) retira de R2 el paquete M06 del run territorial (`incluye_m06_run`). El archivista deja de copiar M01-M05 y
  paquetes fuente, empaqueta igual los M06/M08 y omite el M06 si vive su M08. Reutilizable territorial 1.3.1,
  `archivo_origen.py` 1.0.1. El check acepta el M08 que contiene el M06 publicado; Murcia sale de las excepciones (48).
- Tamaño estimado del paquete M08 con los productos publicados: Cantabria 0,56 MB, Castilla-La Mancha 1,99 MB, Madrid
  2,74 MB (frente a 104-357 MB del estado). El log de la 00 da el tamaño real (`paquete=… estado_original=…`).
  La limpieza de los 27,9 GB actuales es T-76.
- Pruebas: selección y determinismo del paquete, exclusión de GeoJSON de secciones, entrada con sha256 del estado
  original, retirada del M06 (y fallo al retirar), cobertura por M08 en el check.
- Riesgos: toca la 00 (`no-automerge`); se valida en la misma 00 de prueba de T-72.
