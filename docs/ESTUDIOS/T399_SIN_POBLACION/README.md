# T-399 · 2011-11: seccionado del Censo 2011 y relleno de las secciones sin fila en la tabla (D-156)

Herramienta `herramientas/contrato_historico_epoca.py` 1.2.0, contratos 1.3.0. Decisión del propietario D-156 (17-11), sobre el análisis de `docs/ESTUDIOS/T399_2011_SIN_POBLACION/`.

1. **Seccionado de 2011-11 = cartografía del Censo 2011** (`cartografia_censo2011_nacional.zip`, 35.960 secciones, sha256 `d0151e0c…` de T-357, www.ine.es). No el de 2012: sus 63 secciones nuevas parten una del Censo y doblaban la población. Con él toda sección de la tabla tiene geometría: desaparece el caso de D-153 en 2011-11 (T-396: 42 asignadas y 2 excluidas pasan a 0). Mismos campos y CRS (25830) que el seccionado anual: el motor (M01-M08) corre sin cambios (piloto nac22 2011-11: M01-M08 OK).
2. **Secciones del seccionado sin fila en la tabla** (43 en la cartografía): valor de la misma sección en el año más cercano del Atlas 30832 con dato (D-126; para 2011 es 2015), origen `rellenada_año_cercano` (cuenta como estimada en el umbral del 1 %).
3. **Ajuste al total municipal oficial del Censo 2011: sin ajuste, declarado.** No he localizado una tabla del INE con ese total y su sha256 (`Municipios_Censo_2011.xls` es la lista de códigos; las tablas municipales del Censo no dan un CSV con id estable). El contrato declara `poblacion.total_municipal_oficial.fuente = null` y cada sección sale `sin_ajuste_municipal`. El código ya ajusta (restos mayores, residuo ≤ 0 → sin ajuste) en cuanto se le dé el total.
4. **Sin dato en ningún año** (2701501005, 3605901003): la provincia queda BLOQUEADA_SIN_DATO (27 y 36; 36 además 2,64 % > 1 %).
5. `materializar` solo aplica lo declarado y falla cerrado si difiere.

## Resultado en 2011-11
41 secciones rellenadas (46.199 hab.) en 25 provincias, 2 sin dato. `materializar`: 49 de 52 provincias OK (antes 2). No materializan: 27 y 36 (BLOQUEADA_SIN_DATO) y 35 (`PUENTE_FUERA_DEL_SECCIONADO`, La Graciosa: T-400, no tocada). Las otras 4 elecciones solo cambian de versión y regla. Informes derivados del contrato (`informe_poblacion`): `informe_provincias.csv` y `cuadre_municipal.csv`.

## Aviso: la premisa «los votos coinciden» no se cumple
La puerta M07 de 2011-11 FALLA en 13 provincias con el seccionado del Censo (votos de secciones que el Censo no tiene: 0,10-0,58 % de los votos frente al tope de 0,1 %), p. ej. nac22: 418 votos (0,357 %) de la sección 2212503008, una de las «hijas» de 2012. Con el seccionado 2012 son 5 provincias (03, 24, 27, 32, 33), las cubiertas por las excepciones D-70. El Observatorio usa un mapa mixto. Detalle: `docs/ESTUDIOS/T399_2011_SIN_POBLACION/votos_fuera_del_seccionado.csv`.
