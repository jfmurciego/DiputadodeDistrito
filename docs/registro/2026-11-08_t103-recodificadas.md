## 2026-11-08 — T-103 — Archivista: recodificadas y contenidas fuera del tope D-17

- Causa: tras T-101, Badajoz (0,87 %), Valencia (0,77 %), Albacete (0,63 %) y Almería (0,52 %) superaban el tope D-17
  de desajuste de secciones ZIP↔M06. Decisión del propietario (08-11, vía Coordinador): las secciones recodificadas y
  las «contenidas» (cada una dentro de una sola sección del M06, distrito exacto) no cuentan; solo lo partido/unido.
  Valencia se queda como caso aparte.
- Clasificación con `configuracion/equivalencia_secciones_congreso_2023.csv` (sha256 45befb76…; geometría INE 2023
  frente a 2024; en el repositorio no hay ningún cruce oficial del INE): recodificada = tipo 1:1 (Badajoz 0608304014→0608304013,
  1054 votos); contenida = ≥ 95 % del área en una sola sección M06 (9 secciones); el resto, partida.
  % partido: Badajoz 0,179, Albacete 0, Almería 0 (dentro del tope); Valencia 0,600 (8511 votos en 4607001005 y
  007–015): sigue con fallo estricto, el error lo señala como caso aparte (`CASOS_APARTE`, sin excepción).
- Cambio: `herramientas/resultados_partidos.py` 1.2.0 (`clasificar`, informe con `clase`, `votos_partidos` y
  `pct_partido`); tope y reparto D-13 de las partidas sin cambios. Sin regenerar M06, sin tocar workflows.
- Pruebas: `tests/test_desajuste_d17.py` 1.1.0 (recodificada, contenida, partida, por encima del tope tras descontar,
  cifras de las 4 provincias con la tabla versionada), `test_resultados_partidos`, `test_archivo_origen`, gobernanza.
- Efecto: las 00 de Badajoz, Albacete y Almería deberían pasar el archivo en origen al relanzarlas (Operador); sin
  cambio de huellas M04/M05 ni de checkpoints.
