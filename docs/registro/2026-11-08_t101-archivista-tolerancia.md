## 2026-11-08 — T-101 — Archivista: tolerancia D-17 a desajustes de sección

- Causa: la 00 de Congreso Málaga (run 42490329631, job 128768345867, paso «Archivo en origen») falló con
  PARTIDOS_ORIGEN_FAILED: el ZIP de Interior (secciones del censo de julio de 2023) y el M06 (seccionado INE 2023)
  difieren en una sección por lado (2900701022 / 2908405001). Alicante y Barcelona, igual.
- Cambio (D-17, peso D-13): `herramientas/resultados_partidos.py` 1.1.0 (`agregar_informe`) y
  `herramientas/archivo_origen.py` 1.0.3. Si los votos de las secciones del ZIP sin distrito son ≤ 0,5 % de los votos a
  candidaturas de la provincia, se reparten (votos, blancos, nulos y censo, en enteros por restos mayores) entre los
  distritos de sus secciones M06 con peso de población de la composición; si no, o sin equivalencia, fallo estricto.
  Evidencia: `datos/resultados/runs/<territorio>_<run>_desajustes.json` (sección, origen, votos, distritos, regla),
  clave `desajustes` en `datos/resultados/MANIFEST.json` y `::warning PARTIDOS_DESAJUSTE_D17` en el log.
  Tabla nueva `configuracion/equivalencia_secciones_congreso_2023.csv` (+ `.json` con sha256 y fuentes: ZIP mesa
  e78fc231…, seccionado INE 2023 7a15e700…, geometría INE 2024 df931fa0… y 2025 55c9da7e…), generada con
  `herramientas/equivalencia_congreso_2023.py` (intersección de T-85).
- Desajuste por provincia (22 de 52 con alguno): por encima del tope Badajoz 0,87 %, Valencia 0,77 %, Albacete 0,63 %,
  Almería 0,52 %; por debajo La Coruña 0,47, La Rioja 0,34, Cáceres 0,32, Barcelona 0,24, Toledo 0,21, Lugo 0,21,
  Alicante 0,19, Zaragoza 0,15, Pontevedra 0,12, Málaga 0,064, Sevilla 0,063, Madrid 0,029; con 0 votos (solo
  secciones M06 sin mesas) Ávila, Ciudad Real, Córdoba, Guipúzcoa, Jaén y Vizcaya.
- Pruebas: `tests/test_desajuste_d17.py` (Málaga sintética, sección partida por población, por encima del tope, sin
  tabla, evidencia del archivista, sha256 de la tabla), `test_resultados_partidos`, `test_archivo_origen`,
  `test_equivalencia_seccionados`, gobernanza. Datos reales de Málaga, Alicante y Barcelona pasan el desajuste y los
  totales. Sin cambio de huellas M04/M05/checkpoints ni de workflows.
